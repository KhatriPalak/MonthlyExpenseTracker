#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.app import app, db

def create_tables():
    """Create/update all tables based on current models"""
    with app.app_context():
        try:
            print("Creating/updating database tables...")
            
            # This will create any missing tables and columns
            db.create_all()
            
            print("✅ Database tables updated successfully!")
            
            # Show current expense categories
            from app.app import ExpenseCategory
            categories = ExpenseCategory.query.all()
            
            print(f"\nCurrent categories ({len(categories)} total):")
            for cat in categories:
                user_type = 'Global' if cat.user_id is None else f'User {cat.user_id}'
                print(f"  ID: {cat.expense_category_id}, Name: {cat.expense_category_name}, Type: {user_type}")
                
        except Exception as e:
            print(f"❌ Error updating database: {e}")

if __name__ == "__main__":
    create_tables()
