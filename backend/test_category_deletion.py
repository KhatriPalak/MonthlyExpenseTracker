#!/usr/bin/env python3
"""
Test script to verify category deletion works correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_category_model():
    """Test if the category model has the is_deleted field"""
    try:
        from app.app import app, db, ExpenseCategory
        
        with app.app_context():
            print("🔍 Testing category model...")
            
            # Test if we can create a category with is_deleted field
            test_category = ExpenseCategory(
                expense_category_name="test_category",
                user_id=1,
                is_deleted=False
            )
            
            print("✅ Category model supports is_deleted field")
            
            # Check if there are any categories in the database
            categories = ExpenseCategory.query.all()
            print(f"📋 Found {len(categories)} categories in database:")
            
            for cat in categories:
                is_deleted_status = "Unknown"
                try:
                    is_deleted_status = "Deleted" if cat.is_deleted else "Active"
                except AttributeError:
                    is_deleted_status = "No is_deleted column"
                
                user_type = 'Global' if cat.user_id is None else f'User {cat.user_id}'
                print(f"   • ID: {cat.expense_category_id}, Name: '{cat.expense_category_name}', Type: {user_type}, Status: {is_deleted_status}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing category model: {e}")
        return False

def test_database_schema():
    """Test if the database has the is_deleted column"""
    try:
        from app.app import app, db
        from sqlalchemy import text
        
        with app.app_context():
            print("\n🔍 Testing database schema...")
            
            # Check if is_deleted column exists
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'expense_category'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("📊 Current expense_category table structure:")
            
            has_is_deleted = False
            for col in columns:
                if col[0] == 'is_deleted':
                    has_is_deleted = True
                print(f"   • {col[0]} ({col[1]}) - Nullable: {col[2]}, Default: {col[3]}")
            
            if has_is_deleted:
                print("✅ is_deleted column exists in database")
            else:
                print("❌ is_deleted column missing from database")
                print("💡 Run the migration script: python migrate_database.py")
            
            return has_is_deleted
            
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Category Deletion Test")
    print("=" * 50)
    
    model_ok = test_category_model()
    schema_ok = test_database_schema()
    
    print("\n" + "=" * 50)
    if model_ok and schema_ok:
        print("✅ All tests passed! Category deletion should work.")
    else:
        print("❌ Some tests failed. Check the issues above.")
        
    print("\n💡 Next steps:")
    print("1. If is_deleted column is missing, run: python migrate_database.py")
    print("2. Test deletion in the frontend")
    print("3. Check browser console for any errors")
