#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db import SessionLocal
from app.models import ExpenseCategory

def create_expense_categories():
    """Create default expense categories"""
    session = SessionLocal()
    try:
        # Check if categories already exist
        existing_categories = session.query(ExpenseCategory).count()
        if existing_categories > 0:
            print(f"Found {existing_categories} existing categories. Skipping creation.")
            return

        # Default categories
        categories = [
            "Food & Dining",
            "Transportation", 
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Personal Care",
            "Groceries",
            "Other"
        ]

        for i, category_name in enumerate(categories, 1):
            category = ExpenseCategory(
                expense_category_id=i,
                expense_category_name=category_name
            )
            session.add(category)
            print(f"Added category: {category_name} (ID: {i})")

        session.commit()
        print("Successfully created expense categories!")

    except Exception as e:
        print(f"Error creating categories: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_expense_categories()
