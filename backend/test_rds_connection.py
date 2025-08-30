import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_and_test_rds_database():
    try:
        print("🔄 Step 1: Creating monthly_expense_tracker database on RDS...")
        
        # Get the database URL and modify it to connect to 'postgres' database temporarily
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in .env file")
            return False
        
        print(f"RDS Endpoint: {database_url}")
        
        # Connect to 'postgres' database to create our target database
        temp_url = database_url.replace('/monthly_expense_tracker', '/postgres')
        print(f"🔗 Connecting to default postgres database...")
        
        conn = psycopg2.connect(temp_url)
        conn.autocommit = True  # Required for CREATE DATABASE
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'monthly_expense_tracker'")
        exists = cur.fetchone()
        
        if not exists:
            print("📝 Creating monthly_expense_tracker database...")
            cur.execute("CREATE DATABASE monthly_expense_tracker")
            print("✅ Database 'monthly_expense_tracker' created successfully on RDS!")
        else:
            print("ℹ️ Database 'monthly_expense_tracker' already exists on RDS")
        
        cur.close()
        conn.close()
        
        print("\n🔄 Step 2: Testing connection to monthly_expense_tracker database...")
        
        # Now connect to your target database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Test queries
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("✅ RDS Connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()
        print(f"✅ Connected to RDS database: {db_name[0]}")
        
        # Show existing tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print(f"📊 Tables in RDS database: {len(tables)}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ RDS Operation failed: {e}")
        return False

if __name__ == "__main__":
    create_and_test_rds_database()