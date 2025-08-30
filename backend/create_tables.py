#!/usr/bin/env python3
"""
Script to create all database tables from models.py
Run this to initialize your PostgreSQL database with all required tables.
"""

import sys
import os

# Add the app directory to the path
app_path = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_path)

from sqlalchemy import create_engine, text
from db import Base, DATABASE_URL
from models import (
    Currency, User, ExpenseCategory, Month, Year, 
    MonthlyLimit, Expense
)

def create_all_tables():
    """Create all tables defined in models.py"""
    
    print("🔧 Database Table Creation Script")
    print("=" * 50)
    print(f"📊 Database URL: {DATABASE_URL}")
    print("=" * 50)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        print("\n🔌 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Create all tables
        print("\n📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        print("\n📋 Created tables:")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        for table in sorted(tables):
            print(f"   ✓ {table}")
        
        # Add initial data
        print("\n🌱 Adding initial data...")
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if currencies exist
        currency_count = session.query(Currency).count()
        if currency_count == 0:
            print("   Adding default currencies...")
            currencies = [
                Currency(currency_id=1, currency_name="US Dollar", currency_symbol="$"),
                Currency(currency_id=2, currency_name="Euro", currency_symbol="€"),
                Currency(currency_id=3, currency_name="British Pound", currency_symbol="£"),
                Currency(currency_id=4, currency_name="Indian Rupee", currency_symbol="₹"),
                Currency(currency_id=5, currency_name="Japanese Yen", currency_symbol="¥"),
            ]
            session.add_all(currencies)
            session.commit()
            print(f"   ✓ Added {len(currencies)} currencies")
        
        # Check if months exist
        month_count = session.query(Month).count()
        if month_count == 0:
            print("   Adding months...")
            months = [
                Month(month_id=1, month_name="January"),
                Month(month_id=2, month_name="February"),
                Month(month_id=3, month_name="March"),
                Month(month_id=4, month_name="April"),
                Month(month_id=5, month_name="May"),
                Month(month_id=6, month_name="June"),
                Month(month_id=7, month_name="July"),
                Month(month_id=8, month_name="August"),
                Month(month_id=9, month_name="September"),
                Month(month_id=10, month_name="October"),
                Month(month_id=11, month_name="November"),
                Month(month_id=12, month_name="December"),
            ]
            session.add_all(months)
            session.commit()
            print(f"   ✓ Added {len(months)} months")
        
        # Check if years exist
        year_count = session.query(Year).count()
        if year_count == 0:
            print("   Adding years...")
            years = [
                Year(year_id=2024, year_number=2024),
                Year(year_id=2025, year_number=2025),
                Year(year_id=2026, year_number=2026),
            ]
            session.add_all(years)
            session.commit()
            print(f"   ✓ Added {len(years)} years")
        
        # Check if default categories exist
        category_count = session.query(ExpenseCategory).filter_by(user_id=None).count()
        if category_count == 0:
            print("   Adding default expense categories...")
            categories = [
                ExpenseCategory(expense_category_name="Food & Dining", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Transportation", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Shopping", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Entertainment", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Bills & Utilities", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Healthcare", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Education", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Travel", user_id=None, is_deleted=False),
                ExpenseCategory(expense_category_name="Other", user_id=None, is_deleted=False),
            ]
            session.add_all(categories)
            session.commit()
            print(f"   ✓ Added {len(categories)} default categories")
        
        # Check if default user exists
        user_count = session.query(User).count()
        if user_count == 0:
            print("   Adding default user...")
            default_user = User(
                user_id=1,
                username="default_user",
                password="hashed_password_here",  # In production, this should be properly hashed
                email="user@example.com",
                global_limit=0,
                currency_id=1  # USD
            )
            session.add(default_user)
            session.commit()
            print("   ✓ Added default user")
        
        session.close()
        
        print("\n" + "=" * 50)
        print("✨ Database setup completed successfully!")
        print("🚀 Your PostgreSQL database is ready to use")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check if the database 'expense_db' exists")
        print("   3. Verify your connection credentials in app/db.py")
        print("   4. Ensure you have the required permissions")
        return False

if __name__ == "__main__":
    success = create_all_tables()
    sys.exit(0 if success else 1)