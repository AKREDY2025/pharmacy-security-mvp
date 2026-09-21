from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, UUID, Date, Time, DECIMAL, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime, date, time, timedelta
from typing import List, Optional
import uuid
import jwt
from decimal import Decimal

# ===================================================================
# DATABASE CONFIGURATION
# ===================================================================

DATABASE_URL = "postgresql://postgres:password@localhost/pharmsecure_erp"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ===================================================================
# DATABASE MODELS
# ===================================================================

class Company(Base):
    __tablename__ = "companies"
    company_id = Column(UUID, primary_key=True)
    company_name = Column(String)

class Branch(Base):
    __tablename__ = "branches"
    branch_id = Column(UUID, primary_key=True)
    company_id = Column(UUID, ForeignKey("companies.company_id"))
    branch_code = Column(String)
    branch_name = Column(String)

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID, primary_key=True)
    company_id = Column(UUID)
    branch_id = Column(UUID)
    username = Column(String, unique=True)
    password_hash = Column(String)
    full_name = Column(String)

class Product(Base):
    __tablename__ = "products"
    product_id = Column(UUID, primary_key=True)
    company_id = Column(UUID)
    sku = Column(String, unique=True)
    product_name = Column(String)
    retail_price = Column(DECIMAL)
    vat_rate = Column(DECIMAL)

class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    batch_id = Column(UUID, primary_key=True)
    product_id = Column(UUID, ForeignKey("products.product_id"))
    branch_id = Column(UUID)
    batch_number = Column(String)
    serial_number = Column(String)
    expiry_date = Column(Date)
    quantity_on_hand = Column(Integer)

class Sale(Base):
    __tablename__ = "sales"
    sale_id = Column(UUID, primary_key=True)
    company_id = Column(UUID)
    branch_id = Column(UUID)
    transaction_number = Column(String, unique=True)
    customer_id = Column(UUID, nullable=True)
    sale_date = Column(Date)
    sale_time = Column(Time)
    sold_by = Column(UUID)
    subtotal = Column(DECIMAL)
    vat_amount = Column(DECIMAL)
    wht_amount = Column(DECIMAL)
    discount_amount = Column(DECIMAL)
    total_amount = Column(DECIMAL)
    payment_method = Column(String)
    payment_status = Column(String)
    is_voided = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SaleDetail(Base):
    __tablename__ = "sale_details"
    sale_detail_id = Column(UUID, primary_key=True)
    sale_id = Column(UUID, ForeignKey("sales.sale_id"))
    batch_id = Column(UUID)
    product_id = Column(UUID)
    quantity_sold = Column(Integer)
    unit_price = Column(DECIMAL)
    vat_rate = Column(DECIMAL)
    line_total = Column(DECIMAL)

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(UUID, primary_key=True)
    company_id = Column(UUID)
    branch_id = Column(UUID)
    customer_name = Column(String)
    phone = Column(String)
    customer_type = Column(String)

# ===================================================================
# PYDANTIC SCHEMAS
# ===================================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class ProductResponse(BaseModel):
    product_id: str
    sku: str
    product_name: str
    retail_price: float
    vat_rate: float
    quantity_on_hand: int
    expiry_date: date

class SaleItemRequest(BaseModel):
    batch_id: str
    product_id: str
    quantity: int
    unit_price: float

class CreateSaleRequest(BaseModel):
    branch_id: str
    customer_id: Optional[str] = None

class PaymentRequest(BaseModel):
    payment_method: str  # 'CASH', 'CARD', 'CREDIT', 'MOBILE_MONEY'
    amount_paid: float
    discount_amount: float = 0

class SaleReceipt(BaseModel):
    transaction_number: str
    sale_date: date
    sale_time: time
    items: List[dict]
    subtotal: float
    vat_amount: float
    wht_amount: float
    discount_amount: float
    total_amount: float
    payment_method: str

# ===================================================================
# FASTAPI APP
# ===================================================================

app = FastAPI(
    title="PharmSecure POS API",
    version="1.0.0",
    description="Enterprise Pharmacy Point of Service System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "pharmsecure-pos-2024"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===================================================================
# AUTHENTICATION ENDPOINTS
# ===================================================================

@app.post("/auth/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login user and get JWT token"""
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # In production, verify password hash
    payload = {
        "user_id": str(user.user_id),
        "username": user.username,
        "branch_id": str(user.branch_id),
        "company_id": str(user.company_id),
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user.user_id),
            "username": user.username,
            "full_name": user.full_name,
            "branch_id": str(user.branch_id)
        }
    }

def verify_token(authorization: str = Header(None)):
    """Verify JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    
    try:
        scheme, token = authorization.split(" ")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===================================================================
# PRODUCT ENDPOINTS
# ===================================================================

@app.get("/products/search")
def search_products(
    query: str,
    branch_id: str,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Search products by SKU or name with real-time stock"""
    
    products = db.query(Product).filter(
        (Product.sku.ilike(f"%{query}%")) |
        (Product.product_name.ilike(f"%{query}%"))
    ).limit(20).all()
    
    results = []
    for product in products:
        # Get stock for this branch
        stock = db.query(func.sum(InventoryBatch.quantity_on_hand)).filter(
            (InventoryBatch.product_id == product.product_id) &
            (InventoryBatch.branch_id == branch_id)
        ).scalar() or 0
        
        results.append({
            "product_id": str(product.product_id),
            "sku": product.sku,
            "product_name": product.product_name,
            "retail_price": float(product.retail_price),
            "vat_rate": float(product.vat_rate),
            "quantity_on_hand": int(stock)
        })
    
    return results

@app.get("/products/{product_id}/stock/{branch_id}")
def get_product_stock(
    product_id: str,
    branch_id: str,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Get real-time stock for a product at a branch"""
    
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get all batches for this product at this branch
    batches = db.query(InventoryBatch).filter(
        (InventoryBatch.product_id == product_id) &
        (InventoryBatch.branch_id == branch_id)
    ).all()
    
    total_stock = sum(b.quantity_on_hand for b in batches)
    
    batch_details = []
    for batch in batches:
        batch_details.append({
            "batch_id": str(batch.batch_id),
            "batch_number": batch.batch_number,
            "serial_number": batch.serial_number,
            "expiry_date": str(batch.expiry_date),
            "quantity_available": batch.quantity_on_hand
        })
    
    return {
        "product_id": str(product.product_id),
        "sku": product.sku,
        "product_name": product.product_name,
        "retail_price": float(product.retail_price),
        "total_stock": total_stock,
        "batches": batch_details
    }

# ===================================================================
# SALES ENDPOINTS
# ===================================================================

@app.post("/sales")
def create_sale(
    request: CreateSaleRequest,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Create new POS sale transaction"""
    
    sale_id = str(uuid.uuid4())
    transaction_number = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    sale = Sale(
        sale_id=sale_id,
        company_id=user_data['company_id'],
        branch_id=request.branch_id,
        transaction_number=transaction_number,
        customer_id=request.customer_id,
        sale_date=date.today(),
        sale_time=datetime.now().time(),
        sold_by=user_data['user_id'],
        subtotal=Decimal(0),
        vat_amount=Decimal(0),
        wht_amount=Decimal(0),
        discount_amount=Decimal(0),
        total_amount=Decimal(0),
        payment_status='PENDING'
    )
    
    db.add(sale)
    db.commit()
    
    return {
        "sale_id": sale_id,
        "transaction_number": transaction_number,
        "sale_date": str(sale.sale_date),
        "sale_time": str(sale.sale_time)
    }

@app.post("/sales/{sale_id}/items")
def add_sale_item(
    sale_id: str,
    item: SaleItemRequest,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Add item to POS sale"""
    
    sale = db.query(Sale).filter(Sale.sale_id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Get product and validate
    product = db.query(Product).filter(Product.product_id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check stock
    batch = db.query(InventoryBatch).filter(
        InventoryBatch.batch_id == item.batch_id
    ).first()
    
    if not batch or batch.quantity_on_hand < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Calculate line total
    vat_rate = float(product.vat_rate) / 100
    line_subtotal = Decimal(str(item.quantity * item.unit_price))
    line_vat = line_subtotal * Decimal(str(vat_rate))
    line_total = line_subtotal + line_vat
    
    # Create sale detail
    sale_detail = SaleDetail(
        sale_detail_id=str(uuid.uuid4()),
        sale_id=sale_id,
        batch_id=item.batch_id,
        product_id=item.product_id,
        quantity_sold=item.quantity,
        unit_price=Decimal(str(item.unit_price)),
        vat_rate=product.vat_rate,
        line_total=line_total
    )
    
    db.add(sale_detail)
    
    # Update sale totals
    sale.subtotal = (sale.subtotal or Decimal(0)) + line_subtotal
    sale.vat_amount = (sale.vat_amount or Decimal(0)) + line_vat
    sale.total_amount = sale.subtotal + sale.vat_amount - (sale.discount_amount or Decimal(0))
    
    # Reserve stock
    batch.quantity_reserved = (batch.quantity_reserved or 0) + item.quantity
    
    db.commit()
    
    return {
        "sale_detail_id": str(sale_detail.sale_detail_id),
        "product_name": product.product_name,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price),
        "vat_rate": float(product.vat_rate),
        "line_total": float(line_total),
        "sale_total": float(sale.total_amount)
    }

@app.post("/sales/{sale_id}/payment")
def process_payment(
    sale_id: str,
    payment: PaymentRequest,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Process payment and finalize sale"""
    
    sale = db.query(Sale).filter(Sale.sale_id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Apply discount
    if payment.discount_amount > 0:
        sale.discount_amount = Decimal(str(payment.discount_amount))
        sale.total_amount = sale.subtotal + sale.vat_amount - sale.discount_amount
    
    # Update payment info
    sale.payment_method = payment.payment_method
    sale.payment_status = 'PAID'
    
    # Deduct from inventory
    sale_details = db.query(SaleDetail).filter(SaleDetail.sale_id == sale_id).all()
    for detail in sale_details:
        batch = db.query(InventoryBatch).filter(
            InventoryBatch.batch_id == detail.batch_id
        ).first()
        if batch:
            batch.quantity_on_hand -= detail.quantity_sold
            batch.quantity_reserved = (batch.quantity_reserved or 0) - detail.quantity_sold
    
    db.commit()
    
    return {
        "sale_id": sale_id,
        "transaction_number": sale.transaction_number,
        "total_amount": float(sale.total_amount),
        "amount_paid": float(payment.amount_paid),
        "change": float(payment.amount_paid - sale.total_amount),
        "payment_method": payment.payment_method,
        "payment_status": sale.payment_status
    }

@app.get("/sales/{sale_id}/receipt")
def get_receipt(
    sale_id: str,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Generate POS receipt"""
    
    sale = db.query(Sale).filter(Sale.sale_id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    sale_details = db.query(SaleDetail).filter(SaleDetail.sale_id == sale_id).all()
    
    items = []
    for detail in sale_details:
        product = db.query(Product).filter(Product.product_id == detail.product_id).first()
        items.append({
            "product_name": product.product_name if product else "Unknown",
            "quantity": detail.quantity_sold,
            "unit_price": float(detail.unit_price),
            "line_total": float(detail.line_total)
        })
    
    return {
        "transaction_number": sale.transaction_number,
        "sale_date": str(sale.sale_date),
        "sale_time": str(sale.sale_time),
        "items": items,
        "subtotal": float(sale.subtotal),
        "vat_amount": float(sale.vat_amount),
        "wht_amount": float(sale.wht_amount or 0),
        "discount_amount": float(sale.discount_amount or 0),
        "total_amount": float(sale.total_amount),
        "payment_method": sale.payment_method,
        "payment_status": sale.payment_status
    }

# ===================================================================
# REPORTING ENDPOINTS
# ===================================================================

@app.get("/sales/daily-summary/{branch_id}")
def get_daily_summary(
    branch_id: str,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Get daily sales summary"""
    
    today = date.today()
    
    sales = db.query(Sale).filter(
        (Sale.branch_id == branch_id) &
        (Sale.sale_date == today) &
        (Sale.is_voided == False) &
        (Sale.payment_status == 'PAID')
    ).all()
    
    total_sales = len(sales)
    total_amount = sum(s.total_amount for s in sales) if sales else Decimal(0)
    total_vat = sum(s.vat_amount for s in sales) if sales else Decimal(0)
    
    cash_sales = sum(s.total_amount for s in sales if s.payment_method == 'CASH') if sales else Decimal(0)
    credit_sales = sum(s.total_amount for s in sales if s.payment_method == 'CREDIT') if sales else Decimal(0)
    
    return {
        "date": str(today),
        "branch_id": branch_id,
        "total_transactions": total_sales,
        "total_sales_amount": float(total_amount),
        "total_vat": float(total_vat),
        "cash_sales": float(cash_sales),
        "credit_sales": float(credit_sales),
        "average_transaction": float(total_amount / total_sales) if total_sales > 0 else 0
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "PharmSecure POS API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

