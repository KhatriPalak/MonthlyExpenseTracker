"""
Quick RDS Table Inspector
Simple script to check what tables and data exist in your RDS database
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_rds_tables():
    """Check all tables and their record counts in RDS"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in .env file")
            return False
        
        print("🔍 Connecting to RDS Database...")
        print("=" * 50)
        
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Check PostgreSQL version
        cur.execute("SELECT version();")
        version = cur.fetchone()['version']
        print(f"📊 Database: {version.split(',')[0]}")
        print()
        
        # Get all tables
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        
        if not tables:
            print("❌ No tables found in database!")
            return False
        
        print(f"📋 Found {len(tables)} tables:")
        print("=" * 50)
        
        # Check each table
        for table in tables:
            try:
                if table == 'user':
                    cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                else:
                    cur.execute(f'SELECT COUNT(*) FROM {table}')
                count = cur.fetchone()['count']
                
                # Get sample data for smaller tables
                sample_info = ""
                if table == 'month' and count > 0:
                    cur.execute("SELECT month_name FROM month ORDER BY month_id LIMIT 3")
                    months = [row['month_name'] for row in cur.fetchall()]
                    sample_info = f" (e.g., {', '.join(months)}...)"
                elif table == 'expense_category' and count > 0:
                    cur.execute("SELECT expense_category_name FROM expense_category WHERE user_id IS NULL AND is_deleted = FALSE ORDER BY expense_category_name LIMIT 3")
                    categories = [row['expense_category_name'] for row in cur.fetchall()]
                    sample_info = f" (e.g., {', '.join(categories)}...)"
                elif table == 'year' and count > 0:
                    cur.execute("SELECT year_number FROM year ORDER BY year_number")
                    years = [str(row['year_number']) for row in cur.fetchall()]
                    sample_info = f" (years: {', '.join(years)})"
                
                print(f"✅ {table:<15} : {count:>3} records{sample_info}")
                
            except Exception as e:
                print(f"❌ {table:<15} : Error - {str(e)}")
        
        print()
        print("=" * 50)
        
        # Check critical data
        cur.execute("SELECT COUNT(*) FROM expense_category WHERE user_id IS NULL AND is_deleted = FALSE")
        default_categories = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM month")
        months_count = cur.fetchone()['count']
        
        if months_count == 12 and default_categories >= 12:
            print("✅ Database is properly configured!")
            print("✅ All essential data is present")
        else:
            print("⚠️  Database may need setup:")
            if months_count != 12:
                print(f"   - Expected 12 months, found {months_count}")
            if default_categories < 12:
                print(f"   - Expected 12+ categories, found {default_categories}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to RDS: {e}")
        return False

if __name__ == "__main__":
    print("🚀 RDS Table Inspector")
    print("Checking your AWS RDS database tables...")
    print()
    
    success = check_rds_tables()
    
    if success:
        print("\n🎉 RDS inspection completed!")
    else:
        print("\n💥 Failed to inspect RDS database!")
