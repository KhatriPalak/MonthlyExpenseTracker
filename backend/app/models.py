from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    global_limit = Column(Float, default=0)
    expenses = relationship("Expense", back_populates="user")
    monthly_limits = relationship("MonthlyLimit", back_populates="user")
    categories = relationship("ExpenseCategory", back_populates="user")

class ExpenseCategory(Base):
    __tablename__ = "expense_category"
    expense_category_id = Column(Integer, primary_key=True, autoincrement=True)
    expense_category_name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=True)  # NULL for global categories
    is_deleted = Column(Boolean, default=False, nullable=False)
    expenses = relationship("Expense", back_populates="category")
    user = relationship("User", back_populates="categories")

class Month(Base):
    __tablename__ = "month"
    month_id = Column(Integer, primary_key=True, autoincrement=True)
    month_name = Column(String(20), nullable=False, unique=True)
    monthly_limits = relationship("MonthlyLimit", back_populates="month")

class Year(Base):
    __tablename__ = "year"
    year_id = Column(Integer, primary_key=True, autoincrement=True)
    year_number = Column(Integer, nullable=False, unique=True)
    monthly_limits = relationship("MonthlyLimit", back_populates="year")

class MonthlyLimit(Base):
    __tablename__ = "monthly_limit"
    monthly_limit_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    monthly_limit_amount = Column(Float, nullable=False)
    month_id = Column(Integer, ForeignKey("month.month_id"), nullable=False)
    year_id = Column(Integer, ForeignKey("year.year_id"), nullable=False)
    user = relationship("User", back_populates="monthly_limits")
    month = relationship("Month", back_populates="monthly_limits")
    year = relationship("Year", back_populates="monthly_limits")

class Expense(Base):
    __tablename__ = "expense"
    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    expense_item_price = Column(Float, nullable=False)
    expense_category_id = Column(Integer, ForeignKey("expense_category.expense_category_id"), nullable=False)
    expense_description = Column(String(255))
    expense_item_count = Column(Integer, default=1)
    expenditure_date = Column(Date, nullable=False)
    user = relationship("User", back_populates="expenses")
    category = relationship("ExpenseCategory", back_populates="expenses")