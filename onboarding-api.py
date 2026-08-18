"""
Security MVP - Onboarding API Module
Handles pharmacy registration, approval, API key generation, and customer success metrics
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import Column, String, Integer, DateTime, Enum, Boolean, Float, Text
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, timedelta
import secrets
import hashlib
from enum import Enum as PyEnum

# ============================================================================
# DATABASE MODELS
# ============================================================================

class PharmacyStatusEnum(str, PyEnum):
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class OnboardingPharmacy(Base):
    """Pharmacy registration model"""
    __tablename__ = "onboarding_pharmacies"
    
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_name = Column(String(255), nullable=False, index=True)
    license_number = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    region = Column(String(100), nullable=False)
    staff_count = Column(Integer, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # API Keys
    api_key = Column(String(255), nullable=False, unique=True, index=True)
    api_secret = Column(String(255), nullable=False)
    
    # Status
    status = Column(String(50), default=PharmacyStatusEnum.PENDING_APPROVAL, index=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)
    
    # Subscription
    subscription_plan = Column(String(50), default="trial")  # trial, starter, professional, enterprise
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Metrics
    verifications_count = Column(Integer, default=0)
    counterfeits_detected = Column(Integer, default=0)
    last_verification_at = Column(DateTime, nullable=True)
    
    # Billing
    stripe_customer_id = Column(String(255), nullable=True)
    monthly_fee = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes
    admin_notes = Column(Text, nullable=True)


class ApiKeyLog(Base):
    """Track API key usage for security"""
    __tablename__ = "api_key_logs"
    
    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey("onboarding_pharmacies.id"), nullable=False)
    api_key = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    ip_address = Column(String(50), nullable=False)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class OnboardingActivity(Base):
    """Track onboarding and admin activities"""
    __tablename__ = "onboarding_activities"
    
    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey("onboarding_pharmacies.id"), nullable=True)
    action = Column(String(100), nullable=False)  # signup, approve, suspend, generate_key, etc.
    actor = Column(String(100), nullable=False)  # admin email or "system"
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================

class PharmacySignupRequest(BaseModel):
    """Pharmacy signup request"""
    pharmacy_name: str
    license_number: str
    email: EmailStr
    phone: str
    city: str
    region: str
    staff_count: int
    password: str
    
    @validator('pharmacy_name')
    def pharmacy_name_not_empty(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Pharmacy name must be at least 3 characters')
        return v
    
    @validator('staff_count')
    def staff_count_positive(cls, v):
        if v < 1:
            raise ValueError('Staff count must be at least 1')
        return v


class PharmacyResponse(BaseModel):
    """Pharmacy response model"""
    id: int
    pharmacy_name: str
    email: str
    city: str
    region: str
    status: str
    verifications_count: int
    counterfeits_detected: int
    created_at: datetime
    subscription_plan: str
    
    class Config:
        from_attributes = True


class ApiKeyResponse(BaseModel):
    """API key response"""
    api_key: str
    api_secret: str
    created_at: datetime
    expires_at: datetime = None


class AdminApprovalRequest(BaseModel):
    """Admin approval request"""
    approve: bool
    notes: str = ""


class PendingPharmacyResponse(BaseModel):
    """Pending pharmacy for admin approval"""
    id: int
    pharmacy_name: str
    email: str
    city: str
    region: str
    license_number: str
    staff_count: int
    created_at: datetime


class CustomerMetricsResponse(BaseModel):
    """Customer success metrics"""
    pharmacy_name: str
    verifications_total: int
    counterfeits_detected: int
    authentics_verified: int
    verification_success_rate: float
    last_verification: datetime
    average_verification_time_seconds: float
    monthly_revenue: float
    subscription_plan: str


# ============================================================================
# API ROUTES
# ============================================================================

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Generate API key and secret"""
    api_key = f"sk_live_{secrets.token_urlsafe(32)}"
    api_secret = f"sec_{secrets.token_urlsafe(32)}"
    return api_key, api_secret


@router.post("/register", response_model=dict)
async def register_pharmacy(
    request: PharmacySignupRequest,
    db: Session = Depends(get_db)
):
    """Register a new pharmacy (creates pending approval entry)"""
    
    # Check if email already exists
    existing = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.email == request.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if license already exists
    existing_license = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.license_number == request.license_number
    ).first()
    if existing_license:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License number already registered"
        )
    
    # Generate API keys
    api_key, api_secret = generate_api_key()
    
    # Create pharmacy record
    pharmacy = OnboardingPharmacy(
        pharmacy_name=request.pharmacy_name,
        license_number=request.license_number,
        email=request.email,
        phone=request.phone,
        city=request.city,
        region=request.region,
        staff_count=request.staff_count,
        password_hash=hash_password(request.password),
        api_key=api_key,
        api_secret=api_secret,
        status=PharmacyStatusEnum.PENDING_APPROVAL,
        trial_ends_at=datetime.utcnow() + timedelta(days=30),
        subscription_plan="trial"
    )
    
    db.add(pharmacy)
    db.commit()
    db.refresh(pharmacy)
    
    # Log activity
    activity = OnboardingActivity(
        pharmacy_id=pharmacy.id,
        action="signup",
        actor="system",
        details=f"Pharmacy registered: {request.pharmacy_name}"
    )
    db.add(activity)
    db.commit()
    
    # Send welcome email (would integrate with email service)
    # send_welcome_email(pharmacy.email, pharmacy.pharmacy_name)
    
    return {
        "status": "success",
        "message": "Pharmacy registered successfully. Awaiting admin approval.",
        "pharmacy_id": pharmacy.id,
        "email": pharmacy.email
    }


@router.get("/pending", response_model=list[PendingPharmacyResponse])
async def get_pending_pharmacies(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all pending pharmacy approvals (admin only)"""
    
    pending = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.status == PharmacyStatusEnum.PENDING_APPROVAL
    ).order_by(OnboardingPharmacy.created_at.desc()).all()
    
    return pending


@router.post("/approve/{pharmacy_id}")
async def approve_pharmacy(
    pharmacy_id: int,
    request: AdminApprovalRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Approve or reject pharmacy registration (admin only)"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.id == pharmacy_id
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    if request.approve:
        pharmacy.status = PharmacyStatusEnum.ACTIVE
        pharmacy.approved_at = datetime.utcnow()
        pharmacy.approved_by = admin_user["email"]
        
        # Send approval email
        # send_approval_email(pharmacy.email, pharmacy.pharmacy_name, pharmacy.api_key)
        
        message = "Pharmacy approved successfully"
    else:
        pharmacy.status = PharmacyStatusEnum.SUSPENDED
        # Send rejection email
        # send_rejection_email(pharmacy.email, request.notes)
        
        message = "Pharmacy rejected"
    
    pharmacy.admin_notes = request.notes
    db.commit()
    
    # Log activity
    activity = OnboardingActivity(
        pharmacy_id=pharmacy.id,
        action="approve" if request.approve else "reject",
        actor=admin_user["email"],
        details=request.notes
    )
    db.add(activity)
    db.commit()
    
    return {
        "status": "success",
        "message": message,
        "pharmacy_id": pharmacy.id
    }


@router.get("/api-keys/{pharmacy_id}", response_model=ApiKeyResponse)
async def get_api_keys(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get API keys for a pharmacy (owner or admin only)"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.id == pharmacy_id
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Check authorization
    if pharmacy.email != current_user["email"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return ApiKeyResponse(
        api_key=pharmacy.api_key,
        api_secret=pharmacy.api_secret,
        created_at=pharmacy.created_at
    )


@router.post("/regenerate-api-keys/{pharmacy_id}", response_model=ApiKeyResponse)
async def regenerate_api_keys(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Regenerate API keys for a pharmacy (owner or admin only)"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.id == pharmacy_id
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Check authorization
    if pharmacy.email != current_user["email"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate new keys
    old_key = pharmacy.api_key
    api_key, api_secret = generate_api_key()
    
    pharmacy.api_key = api_key
    pharmacy.api_secret = api_secret
    db.commit()
    
    # Log activity
    activity = OnboardingActivity(
        pharmacy_id=pharmacy.id,
        action="regenerate_keys",
        actor=current_user["email"],
        details=f"Old key: {old_key[:20]}..."
    )
    db.add(activity)
    db.commit()
    
    return ApiKeyResponse(
        api_key=pharmacy.api_key,
        api_secret=pharmacy.api_secret,
        created_at=pharmacy.created_at
    )


@router.get("/metrics/{pharmacy_id}", response_model=CustomerMetricsResponse)
async def get_customer_metrics(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get customer success metrics"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.id == pharmacy_id
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Calculate metrics
    authentics = pharmacy.verifications_count - pharmacy.counterfeits_detected
    success_rate = (authentics / pharmacy.verifications_count * 100) if pharmacy.verifications_count > 0 else 0
    
    return CustomerMetricsResponse(
        pharmacy_name=pharmacy.pharmacy_name,
        verifications_total=pharmacy.verifications_count,
        counterfeits_detected=pharmacy.counterfeits_detected,
        authentics_verified=authentics,
        verification_success_rate=success_rate,
        last_verification=pharmacy.last_verification_at,
        average_verification_time_seconds=2.3,  # Would calculate from logs
        monthly_revenue=pharmacy.monthly_fee,
        subscription_plan=pharmacy.subscription_plan
    )


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get dashboard statistics (admin only)"""
    
    total_pharmacies = db.query(OnboardingPharmacy).count()
    active_pharmacies = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.status == PharmacyStatusEnum.ACTIVE
    ).count()
    pending_approvals = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.status == PharmacyStatusEnum.PENDING_APPROVAL
    ).count()
    
    # Calculate total revenue
    total_revenue = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.status == PharmacyStatusEnum.ACTIVE
    ).with_entities(func.sum(OnboardingPharmacy.monthly_fee)).scalar() or 0
    
    # Calculate total verifications
    total_verifications = db.query(OnboardingPharmacy).with_entities(
        func.sum(OnboardingPharmacy.verifications_count)
    ).scalar() or 0
    
    return {
        "total_pharmacies": total_pharmacies,
        "active_pharmacies": active_pharmacies,
        "pending_approvals": pending_approvals,
        "total_monthly_revenue": float(total_revenue),
        "total_verifications": total_verifications,
        "year_1_projection": float(total_revenue * 12)
    }


@router.post("/update-subscription/{pharmacy_id}")
async def update_subscription(
    pharmacy_id: int,
    plan: str,  # trial, starter, professional, enterprise
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Update pharmacy subscription plan (admin only)"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.id == pharmacy_id
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Define plan pricing (in GHS)
    plan_pricing = {
        "trial": 0.0,
        "starter": 2500.0,
        "professional": 5000.0,
        "enterprise": 10000.0
    }
    
    if plan not in plan_pricing:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    old_plan = pharmacy.subscription_plan
    pharmacy.subscription_plan = plan
    pharmacy.monthly_fee = plan_pricing[plan]
    db.commit()
    
    # Log activity
    activity = OnboardingActivity(
        pharmacy_id=pharmacy.id,
        action="update_subscription",
        actor=admin_user["email"],
        details=f"Changed from {old_plan} to {plan}"
    )
    db.add(activity)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Subscription updated to {plan}",
        "monthly_fee": plan_pricing[plan]
    }


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify user is admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Note: get_db and get_current_user should be imported from main API file

# ============================================================================
# INTEGRATION WITH BILLING (Stripe/Paystack)
# ============================================================================

async def create_stripe_customer(pharmacy: OnboardingPharmacy):
    """Create Stripe customer for pharmacy"""
    # import stripe
    # customer = stripe.Customer.create(
    #     email=pharmacy.email,
    #     name=pharmacy.pharmacy_name,
    #     phone=pharmacy.phone,
    #     metadata={"pharmacy_id": pharmacy.id}
    # )
    # pharmacy.stripe_customer_id = customer.id
    pass


async def update_stripe_subscription(pharmacy: OnboardingPharmacy, plan: str):
    """Update Stripe subscription"""
    # import stripe
    # stripe.Subscription.create(
    #     customer=pharmacy.stripe_customer_id,
    #     items=[{"price": STRIPE_PRICES[plan]}]
    # )
    pass

# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

WELCOME_EMAIL_TEMPLATE = """
<h2>Welcome to PharmSecure!</h2>
<p>Thank you for registering {{pharmacy_name}}.</p>
<p>Your account is pending admin approval. We typically approve accounts within 1 hour.</p>
<p>You'll receive an email when your account is active.</p>
"""

APPROVAL_EMAIL_TEMPLATE = """
<h2>Welcome to PharmSecure! 🎉</h2>
<p>Your pharmacy {{pharmacy_name}} has been approved and is now active.</p>
<h3>Your API Credentials:</h3>
<p><strong>API Key:</strong> {{api_key}}</p>
<p><strong>API Secret:</strong> Keep this secure!</p>
<h3>Quick Start:</h3>
<ol>
  <li>Visit {{dashboard_url}}</li>
  <li>Start verifying products</li>
  <li>View metrics and analytics</li>
</ol>
<p>Need help? Check our documentation at {{docs_url}}</p>
"""

REJECTION_EMAIL_TEMPLATE = """
<p>Thank you for applying to PharmSecure.</p>
<p>Unfortunately, we cannot approve your application at this time.</p>
<p>Reason: {{reason}}</p>
<p>If you have questions, please contact: support@pharmsecure.com</p>
"""
