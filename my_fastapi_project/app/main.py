from fastapi import FastAPI, HTTPException, Depends,  Request, Response
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import logging

models.Base.metadata.create_all(bind=engine)

SECRET_KEY = "8bfdfbfc16fe28366ac05000e501b18789567c5e3ecb8a287f1c34fb2fef25d9"  # Replace with your own secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin")
logging.basicConfig(filename='./logfile.log', level=logging.INFO)

app = FastAPI()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logging.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logging.info(f"Response: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response

# Dependency
def get_db(request: Request):
    return request.state.db

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        print(datetime.now())
        print(datetime.now() + expires_delta)
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# API endpoints for User
@app.post("/signup", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.create_user(db=db, user=user)
    return db_user

@app.post("/signin", response_model=schemas.Token)
async def signin_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=form_data.username)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Incorrect username")
    if not crud.verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    token = schemas.Token(access_token=access_token, token_type="bearer")
    return token

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# API endpoints for Product
@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_product(db=db, product=product)

@app.post("/update_stock_quantity/{product_id}/{stock_quantity}", response_model=schemas.Product)
def update_stock_quantity(product_id: int, stock_quantity: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.stock_quantity = stock_quantity
    crud.update_stock_quantity(db, product_id, stock_quantity)
    db.commit()
    return db_product

@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# # API endpoint for placing an order
@app.post("/orders/", response_model=schemas.Order)
def place_order(order: schemas.OrderCreate, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if the product exists
    product_in_db = crud.get_product(db, order.product_id)
    if product_in_db is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if there is enough stock
    if order.quantity > product_in_db.stock_quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")
    
    if order.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")
        
    # Calculate total price
    total_price = product_in_db.price * order.quantity
    order.total_price = total_price
    
    # Create order
    db_order = crud.create_order(db, order)

    crud.update_order_user_id(db, db_order.id, current_user.id)
    
    payment = schemas.PaymentCreate(
        user_id=current_user.id,
        order_id=db_order.id,
        amount=total_price,
        status="Pending",
        payment_method="Credit Card"
    )

    # Create payment
    db_payment = crud.create_payment(db, payment)
    crud.update_order_payment_id(db, db_order.id, db_payment.id)
    db_order = crud.get_order(db, db_order.id)

    # Adjust stock quantity
    product_in_db.stock_quantity -= order.quantity
    crud.update_stock_quantity(db, order.product_id, product_in_db.stock_quantity)
    db.commit()

    return db_order

# # API endpoint for simulating payment processing
@app.put("/payments/{payment_id}", response_model=schemas.Payment)
def process_payment(payment_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_payment = crud.get_payment(db, payment_id)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Simulate processing payment (changing payment status)
    db_payment.status = "Processed"
    db.commit()
    
    return db_payment