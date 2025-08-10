#!/usr/bin/env python3
"""
PostgreSQL Migration Script: Add user_id column to expense_category table
This script connects to your PostgreSQL database and adds the missing user_id column.
"""

import sys
import os
import psycopg2
from psycopg2 import sql

def get_db_connection():
    """Get database connection using environment variables or defaults"""
    try:
        # Use the same connection details as your Flask app
        POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
        POSTGRES_PW = os.environ.get('POSTGRES_PW', 'postgres')
        POSTGRES_HOST = os.environ.get('POSTGRES_URL', 'localhost:5432').split(':')[0]
        POSTGRES_PORT = os.environ.get('POSTGRES_URL', 'localhost:5432').split(':')[1] if ':' in os.environ.get('POSTGRES_URL', 'localhost:5432') else '5432'
        POSTGRES_DB = os.environ.get('POSTGRES_DB', 'expense_db')
        
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PW
        )
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    return cursor.fetchone() is not None

def add_user_id_column():
    """Add user_id column to expense_category table"""
    print("🚀 Starting PostgreSQL migration...")
    print("📋 Adding user_id column to expense_category table")
    print("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Step 1: Check if column already exists
        print("🔍 Checking if user_id column already exists...")
        if check_column_exists(cursor, 'expense_category', 'user_id'):
            print("✅ user_id column already exists in expense_category table!")
            
            # Show current table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'expense_category' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("\n📊 Current table structure:")
            for col in columns:
                print(f"   • {col[0]} ({col[1]}) - Nullable: {col[2]}")
            
            cursor.close()
            conn.close()
            return True
        
        # Step 2: Add the user_id column
        print("📝 Adding user_id column...")
        cursor.execute("""
            ALTER TABLE expense_category 
            ADD COLUMN user_id INTEGER
        """)
        print("✅ user_id column added successfully")
        
        # Step 3: Add foreign key constraint
        print("🔗 Adding foreign key constraint...")
        cursor.execute("""
            ALTER TABLE expense_category 
            ADD CONSTRAINT fk_expense_category_user 
            FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE SET NULL
        """)
        print("✅ Foreign key constraint added successfully")
        
        # Step 4: Add index for performance
        print("⚡ Adding index for better performance...")
        cursor.execute("""
            CREATE INDEX idx_expense_category_user_id 
            ON expense_category(user_id)
        """)
        print("✅ Index created successfully")
        
        # Step 5: Commit the changes
        conn.commit()
        print("💾 Changes committed to database")
        
        # Step 6: Verify the final structure
        print("\n🔍 Verifying final table structure...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'expense_category' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("📊 Updated table structure:")
        for col in columns:
            print(f"   • {col[0]} ({col[1]}) - Nullable: {col[2]}")
        
        # Step 7: Show current data
        cursor.execute("SELECT expense_category_id, expense_category_name, user_id FROM expense_category")
        categories = cursor.fetchall()
        print(f"\n📋 Current categories ({len(categories)} total):")
        for cat in categories:
            user_type = 'Global' if cat[2] is None else f'User {cat[2]}'
            print(f"   • ID: {cat[0]}, Name: '{cat[1]}', Type: {user_type}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print("🌐 Your database is now ready for user-specific categories!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    print("🗄️  PostgreSQL Database Migration")
    print("📝 Monthly Expense Tracker - Add user_id to expense_category")
    print("=" * 60)
    
    success = add_user_id_column()
    
    if success:
        print("\n✨ Migration completed successfully!")
        print("🔧 Backend: http://localhost:5000")
        print("🌐 Frontend: http://localhost:3001")
        print("📊 You can now test user-specific categories!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("💡 Make sure PostgreSQL is running and connection details are correct.")
    
    print("=" * 60)
