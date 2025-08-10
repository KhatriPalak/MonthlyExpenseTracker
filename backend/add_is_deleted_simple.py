#!/usr/bin/env python3
"""
Simple migration script to add is_deleted column to expense_category table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def add_is_deleted_column():
    """Add is_deleted column to expense_category table"""
    try:
        from app.app import app, db
        from sqlalchemy import text
        
        with app.app_context():
            print("🔄 Adding is_deleted column to expense_category table...")
            
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'expense_category' AND column_name = 'is_deleted'
            """))
            
            if result.fetchone():
                print("✅ is_deleted column already exists!")
                return True
            
            # Add the column
            print("📝 Adding is_deleted column...")
            db.session.execute(text("""
                ALTER TABLE expense_category 
                ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL
            """))
            
            # Update existing records
            print("🔄 Updating existing records...")
            db.session.execute(text("""
                UPDATE expense_category 
                SET is_deleted = FALSE 
                WHERE is_deleted IS NULL
            """))
            
            # Add index for performance
            print("⚡ Adding index...")
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_expense_category_is_deleted 
                ON expense_category(is_deleted)
            """))
            
            db.session.commit()
            print("✅ Successfully added is_deleted column!")
            
            # Verify the change
            result = db.session.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'expense_category'
                ORDER BY ordinal_position
            """))
            
            print("\n📊 Updated table structure:")
            for col in result.fetchall():
                print(f"   • {col[0]} ({col[1]}) - Default: {col[2]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("🗄️  Database Migration: Add is_deleted Column")
    print("=" * 50)
    
    success = add_is_deleted_column()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("🔄 Please restart your backend server")
        print("🌐 Test category deletion in the frontend")
    else:
        print("\n❌ Migration failed")
        
    print("=" * 50)
