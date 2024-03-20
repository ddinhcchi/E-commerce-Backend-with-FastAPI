from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'User'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    # relationships
    orders = relationship("Order", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class Product(Base):
    __tablename__ = 'Product'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    # relationships
    orders = relationship("Order", back_populates="product")

class Payment(Base):
    __tablename__ = 'Payment'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    order_id = Column(Integer, ForeignKey('Order.id'))
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), nullable=False)
    payment_method = Column(String(100), nullable=False)
    # relationships
    user = relationship("User", back_populates="payments")

class Order(Base):
    __tablename__ = 'Order'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    product_id = Column(Integer, ForeignKey('Product.id'))
    payment_id = Column(Integer, ForeignKey('Payment.id'))
    quantity = Column(Integer, nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    # relationships
    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")
