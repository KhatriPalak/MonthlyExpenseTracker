#!/usr/bin/env python3
"""
Script to create the User table for authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def create_user_table():
    """Create the User table if it doesn't exist"""
    with app.app_context():
        try:
            # Create the User table
            db.create_all()
            print("✅ User table created successfully!")
            
            # Check if table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'user' in tables:
                print("✅ User table confirmed in database")
                
                # Show table columns
                columns = inspector.get_columns('user')
                print("\n📋 User table columns:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("❌ User table not found in database")
                
        except Exception as e:
            print(f"❌ Error creating User table: {e}")

if __name__ == '__main__':
    create_user_table()
