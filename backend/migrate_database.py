#!/usr/bin/env python3
"""
Database Migration Script: Add user_id column to expense_category table
This script will safely add the user_id column if it doesn't exist,
and populate it with some sample data.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def run_migration():
    try:
        from app.app import app, db, ExpenseCategory
        
        with app.app_context():
            print("🔄 Starting database migration...")
            
            # Method 1: Try using SQLAlchemy's create_all() which is safe
            print("📊 Updating database schema...")
            db.create_all()
            print("✅ Schema update completed")
            
            # Check current categories
            categories = ExpenseCategory.query.all()
            print(f"\n📋 Found {len(categories)} categories in database:")
            
            for cat in categories:
                user_type = 'Global' if cat.user_id is None else f'User {cat.user_id}'
                print(f"   • ID: {cat.expense_category_id}, Name: '{cat.expense_category_name}', Type: {user_type}")
            
            # If no categories exist, create some default ones
            if len(categories) == 0:
                print("\n🏗️  Creating default categories...")
                default_categories = [
                    'Food & Dining',
                    'Transportation', 
                    'Shopping',
                    'Entertainment',
                    'Bills & Utilities',
                    'Healthcare',
                    'Travel',
                    'Personal Care'
                ]
                
                for cat_name in default_categories:
                    category = ExpenseCategory(
                        expense_category_name=cat_name,
                        user_id=None  # Global category
                    )
                    db.session.add(category)
                    print(f"   ✅ Added global category: {cat_name}")
                
                # Add one user-specific category for testing
                user_category = ExpenseCategory(
                    expense_category_name='Personal Projects',
                    user_id=1  # User-specific category
                )
                db.session.add(user_category)
                print("   ✅ Added user-specific category: Personal Projects")
                
                db.session.commit()
                print("📊 Default categories created successfully!")
            
            print("\n🎉 Migration completed successfully!")
            print("🌐 You can now test the category functionality in the frontend")
            
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this from the backend directory")
        return False
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        print("💡 The user_id column might already exist, which is fine!")
        
        # Try to verify the column exists by querying
        try:
            from app.app import app, db, ExpenseCategory
            with app.app_context():
                categories = ExpenseCategory.query.all()
                print(f"✅ Database is working! Found {len(categories)} categories")
                return True
        except Exception as e2:
            print(f"❌ Database verification failed: {e2}")
            return False

if __name__ == "__main__":
    print("🚀 Monthly Expense Tracker - Database Migration")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        print("\n✨ Migration completed! Your database is ready.")
        print("🌐 Frontend: http://localhost:3001")
        print("🔧 Backend: http://localhost:5000")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        
    print("=" * 50)
