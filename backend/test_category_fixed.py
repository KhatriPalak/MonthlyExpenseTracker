#!/usr/bin/env python3
"""
Test the category deletion functionality after fixing the model
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_category_deletion_fixed():
    """Test if category deletion works with the fixed model"""
    try:
        from app.app import app, db, ExpenseCategory
        
        with app.app_context():
            print("🧪 Testing Fixed Category Deletion")
            print("=" * 40)
            
            # Check if we can access the is_deleted field
            categories = ExpenseCategory.query.all()
            print(f"📋 Found {len(categories)} categories in database:")
            
            for cat in categories[:5]:  # Show first 5
                try:
                    is_deleted_status = "Deleted" if cat.is_deleted else "Active"
                    user_type = 'Global' if cat.user_id is None else f'User {cat.user_id}'
                    print(f"   • ID: {cat.expense_category_id}, Name: '{cat.expense_category_name}', Type: {user_type}, Status: {is_deleted_status}")
                except AttributeError as e:
                    print(f"   ❌ Category {cat.expense_category_id} missing is_deleted field: {e}")
                    return False
            
            # Test creating a category with is_deleted field
            print("\n🔧 Testing category creation with is_deleted field...")
            test_category = ExpenseCategory(
                expense_category_name="test_delete_functionality",
                user_id=1,
                is_deleted=False
            )
            
            # Try to save it
            db.session.add(test_category)
            db.session.commit()
            
            created_id = test_category.expense_category_id
            print(f"   ✅ Created test category with ID: {created_id}")
            
            # Test soft deletion
            print(f"\n🗑️  Testing soft deletion...")
            test_category.is_deleted = True
            db.session.commit()
            print(f"   ✅ Soft deleted category ID: {created_id}")
            
            # Verify it's marked as deleted
            deleted_category = ExpenseCategory.query.filter_by(expense_category_id=created_id).first()
            if deleted_category and deleted_category.is_deleted:
                print(f"   ✅ Category correctly marked as deleted")
            else:
                print(f"   ❌ Category not properly marked as deleted")
                return False
            
            # Clean up - actually delete the test category
            db.session.delete(deleted_category)
            db.session.commit()
            print(f"   🧹 Cleaned up test category")
            
            print("\n🎉 All tests passed! Category deletion should work properly now.")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_category_deletion_fixed()
    
    if success:
        print("\n✅ Category deletion is working properly!")
        print("💡 You can now test deletion in the frontend")
    else:
        print("\n❌ There are still issues with category deletion")
        print("💡 Check that the database has the is_deleted column")
