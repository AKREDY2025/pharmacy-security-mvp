"""
Security MVP - Billing & Revenue Integration
Stripe/Paystack integration, subscription management, and revenue tracking
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum as PyEnum
import json

# Import payment libraries (optional - use only if configured)
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

try:
    import requests
    PAYSTACK_AVAILABLE = True
except ImportError:
    PAYSTACK_AVAILABLE = False


# ============================================================================
# DATABASE MODELS
# ============================================================================

class SubscriptionPlan(str, PyEnum):
    """Subscription plan types"""
    TRIAL = "trial"           # Free, 30 days, full access
    STARTER = "starter"       # GHS 2,500/month, up to 1000 verifications
    PROFESSIONAL = "professional"  # GHS 5,000/month, up to 5000 verifications
    ENTERPRISE = "enterprise" # GHS 10,000/month, unlimited, dedicated support


class PaymentStatus(str, PyEnum):
    """Payment transaction status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, PyEnum):
    """Payment methods"""
    STRIPE = "stripe"
    PAYSTACK = "paystack"
    BANK_TRANSFER = "bank_transfer"
    TRIAL = "trial"


class BillingAccount(Base):
    """Billing account for pharmacy"""
    __tablename__ = "billing_accounts"
    
    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey("onboarding_pharmacies.id"), unique=True)
    
    # Subscription details
    subscription_plan = Column(String(50), default=SubscriptionPlan.TRIAL)
    subscription_started_at = Column(DateTime, default=datetime.utcnow)
    subscription_renews_at = Column(DateTime, nullable=True)
    subscription_cancelled_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Payment info
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    paystack_customer_id = Column(String(255), nullable=True, unique=True)
    
    # Pricing
    monthly_price = Column(Float, default=0.0)
    currency = Column(String(3), default="GHS")
    
    # Usage tracking
    verifications_this_month = Column(Integer, default=0)
    verifications_limit = Column(Integer, default=None)  # None = unlimited
    
    # Billing info
    billing_email = Column(String(255), nullable=True)
    billing_phone = Column(String(20), nullable=True)
    billing_address = Column(String(500), nullable=True)
    
    # Payment method
    default_payment_method = Column(String(50), default=PaymentMethod.TRIAL)
    card_last_four = Column(String(4), nullable=True)
    card_expiry = Column(String(5), nullable=True)  # MM/YY
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes
    notes = Column(String(500), nullable=True)


class PaymentTransaction(Base):
    """Individual payment transaction"""
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True)
    billing_account_id = Column(Integer, ForeignKey("billing_accounts.id"))
    
    # Transaction info
    transaction_id = Column(String(255), unique=True, index=True)
    reference_number = Column(String(255), unique=True, index=True)
    
    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="GHS")
    amount_paid = Column(Float, nullable=True)  # Actual amount if different
    
    # Payment details
    payment_method = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    status = Column(String(50), default=PaymentStatus.PENDING)
    
    # External IDs
    stripe_charge_id = Column(String(255), nullable=True)
    paystack_reference = Column(String(255), nullable=True)
    
    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, default=dict)  # Store additional info
    error_message = Column(String(500), nullable=True)


class MonthlyInvoice(Base):
    """Monthly invoice for subscription"""
    __tablename__ = "monthly_invoices"
    
    id = Column(Integer, primary_key=True)
    billing_account_id = Column(Integer, ForeignKey("billing_accounts.id"))
    
    # Invoice info
    invoice_number = Column(String(50), unique=True)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    
    # Amount
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    currency = Column(String(3), default="GHS")
    
    # Verification usage
    verifications_used = Column(Integer, default=0)
    verification_overage_charge = Column(Float, default=0.0)
    
    # Status
    status = Column(String(50), default="draft")  # draft, sent, viewed, paid, overdue
    paid_at = Column(DateTime, nullable=True)
    
    # Items
    line_items = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UsageMetric(Base):
    """Track daily usage for billing"""
    __tablename__ = "usage_metrics"
    
    id = Column(Integer, primary_key=True)
    billing_account_id = Column(Integer, ForeignKey("billing_accounts.id"))
    
    # Date
    metric_date = Column(DateTime, default=datetime.utcnow, index=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    
    # Usage
    verifications_count = Column(Integer, default=0)
    counterfeits_detected = Column(Integer, default=0)
    pharmacists_active = Column(Integer, default=0)
    
    # Cost
    daily_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SubscriptionPlanInfo(BaseModel):
    """Subscription plan details"""
    plan: str
    name: str
    monthly_price: float
    currency: str
    features: list
    verification_limit: Optional[int]
    support_level: str


class BillingResponse(BaseModel):
    """Current billing status"""
    pharmacy_name: str
    subscription_plan: str
    monthly_price: float
    subscription_renews_at: datetime
    is_active: bool
    verifications_used_this_month: int
    verifications_limit: Optional[int]
    payment_method: str
    next_invoice_date: datetime


class PaymentIntentResponse(BaseModel):
    """Payment intent for checkout"""
    client_secret: str
    stripe_public_key: Optional[str]
    paystack_public_key: Optional[str]
    amount: float
    currency: str


class InvoiceResponse(BaseModel):
    """Invoice details"""
    invoice_number: str
    invoice_date: datetime
    due_date: datetime
    subtotal: float
    tax: float
    total: float
    items: list
    status: str
    download_url: Optional[str]


# ============================================================================
# PRICING CONFIGURATION
# ============================================================================

SUBSCRIPTION_PLANS = {
    SubscriptionPlan.TRIAL: {
        "name": "Trial Plan",
        "monthly_price": 0.0,
        "currency": "GHS",
        "duration_days": 30,
        "features": [
            "Up to 500 verifications",
            "Full feature access",
            "Email support",
            "Basic analytics"
        ],
        "verification_limit": 500,
        "support_level": "email"
    },
    SubscriptionPlan.STARTER: {
        "name": "Starter Plan",
        "monthly_price": 2500.0,
        "currency": "GHS",
        "features": [
            "Up to 1,000 verifications/month",
            "Full feature access",
            "Email & phone support",
            "Advanced analytics",
            "API access"
        ],
        "verification_limit": 1000,
        "support_level": "standard"
    },
    SubscriptionPlan.PROFESSIONAL: {
        "name": "Professional Plan",
        "monthly_price": 5000.0,
        "currency": "GHS",
        "features": [
            "Up to 5,000 verifications/month",
            "All Starter features",
            "Priority support",
            "Custom reports",
            "Dedicated account manager (via Slack)"
        ],
        "verification_limit": 5000,
        "support_level": "priority"
    },
    SubscriptionPlan.ENTERPRISE: {
        "name": "Enterprise Plan",
        "monthly_price": 10000.0,
        "currency": "GHS",
        "features": [
            "Unlimited verifications",
            "All Professional features",
            "24/7 phone support",
            "Custom integrations",
            "Dedicated support team",
            "SLA guarantee"
        ],
        "verification_limit": None,
        "support_level": "enterprise"
    }
}

OVERAGE_PRICE_PER_VERIFICATION = 5.0  # GHS per verification over limit


# ============================================================================
# BILLING ROUTES
# ============================================================================

billing_router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@billing_router.get("/plans", response_model=dict)
async def get_subscription_plans():
    """Get all subscription plans"""
    plans = {}
    for plan_key, plan_details in SUBSCRIPTION_PLANS.items():
        plans[plan_key.value] = {
            **plan_details,
            "plan": plan_key.value
        }
    return plans


@billing_router.get("/plans/{plan_name}", response_model=SubscriptionPlanInfo)
async def get_plan_details(plan_name: str):
    """Get details for specific plan"""
    plan_enum = SubscriptionPlan(plan_name)
    plan_details = SUBSCRIPTION_PLANS[plan_enum]
    
    return SubscriptionPlanInfo(
        plan=plan_name,
        name=plan_details["name"],
        monthly_price=plan_details["monthly_price"],
        currency=plan_details["currency"],
        features=plan_details["features"],
        verification_limit=plan_details["verification_limit"],
        support_level=plan_details["support_level"]
    )


@billing_router.get("/current", response_model=BillingResponse)
async def get_current_billing(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current billing information"""
    
    # Get pharmacy
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.email == current_user["email"]
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Get billing account
    billing = db.query(BillingAccount).filter(
        BillingAccount.pharmacy_id == pharmacy.id
    ).first()
    
    if not billing:
        raise HTTPException(status_code=404, detail="Billing account not found")
    
    # Calculate usage this month
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    verifications = db.query(Verification).filter(
        Verification.pharmacy_id == pharmacy.id,
        Verification.timestamp >= current_month_start
    ).count()
    
    return BillingResponse(
        pharmacy_name=pharmacy.pharmacy_name,
        subscription_plan=billing.subscription_plan,
        monthly_price=billing.monthly_price,
        subscription_renews_at=billing.subscription_renews_at,
        is_active=billing.is_active,
        verifications_used_this_month=verifications,
        verifications_limit=billing.verifications_limit,
        payment_method=billing.default_payment_method,
        next_invoice_date=billing.subscription_renews_at
    )


@billing_router.post("/upgrade")
async def upgrade_subscription(
    new_plan: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upgrade to different subscription plan"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.email == current_user["email"]
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Validate plan
    try:
        plan_enum = SubscriptionPlan(new_plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_details = SUBSCRIPTION_PLANS[plan_enum]
    
    # Get or create billing account
    billing = db.query(BillingAccount).filter(
        BillingAccount.pharmacy_id == pharmacy.id
    ).first()
    
    if not billing:
        billing = BillingAccount(pharmacy_id=pharmacy.id)
        db.add(billing)
    
    # Update subscription
    old_plan = billing.subscription_plan
    billing.subscription_plan = new_plan
    billing.monthly_price = plan_details["monthly_price"]
    billing.verifications_limit = plan_details["verification_limit"]
    billing.subscription_renews_at = datetime.utcnow() + timedelta(days=30)
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Upgraded from {old_plan} to {new_plan}",
        "plan": new_plan,
        "monthly_price": plan_details["monthly_price"],
        "effective_date": datetime.utcnow()
    }


@billing_router.post("/payment/intent")
async def create_payment_intent(
    amount: float,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create payment intent for Stripe or Paystack"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.email == current_user["email"]
    ).first()
    
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Get billing account
    billing = db.query(BillingAccount).filter(
        BillingAccount.pharmacy_id == pharmacy.id
    ).first()
    
    if not billing:
        raise HTTPException(status_code=404, detail="Billing account not found")
    
    # Create Stripe payment intent
    if STRIPE_AVAILABLE and billing.stripe_customer_id:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency="ghs",
            customer=billing.stripe_customer_id,
            description=f"PharmSecure subscription - {pharmacy.pharmacy_name}"
        )
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            stripe_public_key="pk_live_...",  # Replace with actual key
            paystack_public_key=None,
            amount=amount,
            currency="GHS"
        )
    
    # Fallback to Paystack
    return PaymentIntentResponse(
        client_secret=None,
        stripe_public_key=None,
        paystack_public_key="pk_live_...",  # Replace with actual key
        amount=amount,
        currency="GHS"
    )


@billing_router.post("/webhook/stripe")
async def handle_stripe_webhook(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    
    # Verify webhook signature
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=400, detail="Stripe not configured")
    
    event_type = request.get("type")
    
    if event_type == "payment_intent.succeeded":
        payment_intent = request["data"]["object"]
        
        # Update transaction
        transaction = db.query(PaymentTransaction).filter(
            PaymentTransaction.stripe_charge_id == payment_intent["id"]
        ).first()
        
        if transaction:
            transaction.status = PaymentStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            transaction.amount_paid = payment_intent["amount"] / 100
            db.commit()
    
    elif event_type == "customer.subscription.updated":
        subscription = request["data"]["object"]
        
        # Update subscription
        billing = db.query(BillingAccount).filter(
            BillingAccount.stripe_subscription_id == subscription["id"]
        ).first()
        
        if billing:
            billing.subscription_renews_at = datetime.fromtimestamp(
                subscription["current_period_end"]
            )
            db.commit()
    
    return {"status": "success"}


@billing_router.get("/invoices")
async def get_invoices(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get invoices for pharmacy"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.email == current_user["email"]
    ).first()
    
    billing = db.query(BillingAccount).filter(
        BillingAccount.pharmacy_id == pharmacy.id
    ).first()
    
    invoices = db.query(MonthlyInvoice).filter(
        MonthlyInvoice.billing_account_id == billing.id
    ).order_by(MonthlyInvoice.invoice_date.desc()).limit(limit).all()
    
    return [
        {
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "total": inv.total,
            "status": inv.status,
            "download_url": f"/api/v1/billing/invoices/{inv.id}/download"
        }
        for inv in invoices
    ]


@billing_router.post("/verify-quota")
async def verify_quota(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if pharmacy has remaining verification quota"""
    
    pharmacy = db.query(OnboardingPharmacy).filter(
        OnboardingPharmacy.email == current_user["email"]
    ).first()
    
    billing = db.query(BillingAccount).filter(
        BillingAccount.pharmacy_id == pharmacy.id
    ).first()
    
    if not billing:
        return {"has_quota": False, "reason": "No billing account"}
    
    # Check if subscription is active
    if not billing.is_active:
        return {"has_quota": False, "reason": "Subscription inactive"}
    
    # Check if trial has expired
    if billing.subscription_plan == SubscriptionPlan.TRIAL:
        if datetime.utcnow() > billing.subscription_renews_at:
            return {"has_quota": False, "reason": "Trial expired"}
    
    # Check verification limit
    if billing.verifications_limit:
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        verifications = db.query(Verification).filter(
            Verification.pharmacy_id == pharmacy.id,
            Verification.timestamp >= current_month_start
        ).count()
        
        if verifications >= billing.verifications_limit:
            return {
                "has_quota": False,
                "reason": "Verification limit reached",
                "limit": billing.verifications_limit,
                "used": verifications
            }
    
    return {
        "has_quota": True,
        "plan": billing.subscription_plan,
        "verifications_remaining": "unlimited" if billing.verifications_limit is None 
                                   else billing.verifications_limit - verifications
    }


# ============================================================================
# ADMIN REVENUE ENDPOINTS
# ============================================================================

@billing_router.get("/admin/revenue")
async def get_revenue_analytics(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get revenue analytics (admin only)"""
    
    # Monthly revenue
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    
    monthly_revenue = db.query(func.sum(BillingAccount.monthly_price)).filter(
        BillingAccount.is_active == True,
        BillingAccount.subscription_plan != SubscriptionPlan.TRIAL
    ).scalar() or 0
    
    # Total active subscriptions
    active_subs = db.query(BillingAccount).filter(
        BillingAccount.is_active == True
    ).count()
    
    # Plan breakdown
    plan_breakdown = db.query(BillingAccount.subscription_plan, func.count()).filter(
        BillingAccount.is_active == True
    ).group_by(BillingAccount.subscription_plan).all()
    
    return {
        "monthly_revenue": float(monthly_revenue),
        "projected_annual_revenue": float(monthly_revenue * 12),
        "active_subscriptions": active_subs,
        "plan_breakdown": dict(plan_breakdown),
        "currency": "GHS"
    }


@billing_router.get("/admin/churn")
async def get_churn_analytics(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get churn analytics (admin only)"""
    
    # Cancelled subscriptions this month
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    
    cancelled_this_month = db.query(BillingAccount).filter(
        BillingAccount.subscription_cancelled_at >= current_month_start
    ).count()
    
    # Active at start of month
    active_start = db.query(BillingAccount).filter(
        BillingAccount.subscription_started_at < current_month_start,
        (BillingAccount.subscription_cancelled_at.is_(None) | 
         (BillingAccount.subscription_cancelled_at >= current_month_start))
    ).count()
    
    churn_rate = (cancelled_this_month / active_start * 100) if active_start > 0 else 0
    
    return {
        "cancelled_this_month": cancelled_this_month,
        "active_at_month_start": active_start,
        "churn_rate_percent": round(churn_rate, 2)
    }
