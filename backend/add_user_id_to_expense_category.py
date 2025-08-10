#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.app import app, db
from sqlalchemy import text

def add_user_id_column():
    """Add user_id column to expense_category table"""
    with app.app_context():
        try:
            print("Checking expense_category table structure...")
            
            # Check if the column already exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='expense_category' AND column_name='user_id'
            """))
            
            if result.fetchone():
                print("✅ user_id column already exists in expense_category table")
                
                # Show current categories
                result = db.session.execute(text("SELECT expense_category_id, expense_category_name, user_id FROM expense_category"))
                categories = result.fetchall()
                
                print(f"\nCurrent categories in table ({len(categories)} total):")
                for cat in categories:
                    user_type = 'Global' if cat[2] is None else f'User {cat[2]}'
                    print(f"  ID: {cat[0]}, Name: {cat[1]}, Type: {user_type}")
                return
            
            print("Adding user_id column to expense_category table...")
            
            # Add the user_id column with foreign key constraint
            db.session.execute(text("""
                ALTER TABLE expense_category 
                ADD COLUMN user_id INTEGER REFERENCES "user"(user_id)
            """))
            
            db.session.commit()
            
            print("✅ Successfully added user_id column to expense_category table")
            
            # Show updated table structure
            result = db.session.execute(text("SELECT expense_category_id, expense_category_name, user_id FROM expense_category"))
            categories = result.fetchall()
            
            print(f"\nUpdated categories in table ({len(categories)} total):")
            for cat in categories:
                user_type = 'Global' if cat[2] is None else f'User {cat[2]}'
                print(f"  ID: {cat[0]}, Name: {cat[1]}, Type: {user_type}")
            
            print("\n🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            
            # Check if it's because column already exists
            try:
                result = db.session.execute(text("SELECT user_id FROM expense_category LIMIT 1"))
                print("✅ user_id column appears to already exist (error was expected)")
            except:
                print("💥 user_id column does not exist and migration failed")

if __name__ == "__main__":
    add_user_id_column()
