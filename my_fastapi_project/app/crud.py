from sqlalchemy.orm import Session
import models, schemas
from passlib.context import CryptContext

# CRUD cho User
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def hash_password(password: str):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password, hashed_password):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

# CRUD cho Product
def get_product(db: Session, product_id: int):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    print(product.stock_quantity)
    return product

def get_products(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_payment(db: Session, order_id: int):
    return db.query(models.Payment).filter(models.Payment.order_id == order_id).first()

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# CRUD cho Payment
def create_payment(db: Session, payment: schemas.PaymentCreate):
    db_payment = models.Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

# CRUD cho Order
def create_order(db: Session, order: schemas.OrderCreate):
    db_order = models.Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_payment_status(db: Session, payment_id: int, status: str):
    db_payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    db_payment.status = status
    db.commit()
    db.refresh(db_payment)
    return db_payment

def update_order_payment_id(db: Session, order_id: int, payment_id: int):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    db_order.payment_id = payment_id
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_user_id(db: Session, order_id: int, user_id: int):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    db_order.user_id = user_id
    db.commit()
    db.refresh(db_order)
    return db_order

def update_stock_quantity(db: Session, product_id: int, quantity: int):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    db_product.stock_quantity = quantity
    db.commit()
    db.refresh(db_product)
    return db_product