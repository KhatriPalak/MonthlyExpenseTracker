"""
Quick RDS Database Verification Script
This script checks if your database exists and shows its contents
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_exists():
    """Check if the database exists and is accessible"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found in .env file")
            return False
        
        logger.info("🔍 Checking database connection and contents...")
        logger.info(f"📍 Connecting to: {database_url.split('@')[1].split('/')[0]}")
        
        # Connect to the database
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Check PostgreSQL version
        cur.execute("SELECT version();")
        version = cur.fetchone()
        logger.info(f"✅ Connected! PostgreSQL Version: {version['version'][:60]}...")
        
        # Check database name
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()
        logger.info(f"✅ Current Database: {db_name['current_database']}")
        
        # List all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        logger.info(f"✅ Tables found ({len(tables)}): {tables}")
        
        # Check data in each table
        for table in tables:
            if table == 'user':
                cur.execute(f'SELECT COUNT(*) as count FROM "{table}"')
            else:
                cur.execute(f'SELECT COUNT(*) as count FROM {table}')
            count = cur.fetchone()['count']
            logger.info(f"  📊 {table}: {count} records")
        
        # Show sample categories
        cur.execute("""
            SELECT expense_category_name, user_id, is_deleted 
            FROM expense_category 
            WHERE user_id IS NULL 
            ORDER BY expense_category_name
        """)
        categories = cur.fetchall()
        logger.info(f"✅ Default Categories ({len(categories)}):")
        for cat in categories:
            status = "🗑️ Deleted" if cat['is_deleted'] else "✅ Active"
            logger.info(f"  - {cat['expense_category_name']} ({status})")
        
        # Show months
        cur.execute("SELECT month_name FROM month ORDER BY month_id")
        months = [row['month_name'] for row in cur.fetchall()]
        logger.info(f"✅ Months ({len(months)}): {', '.join(months)}")
        
        # Show years
        cur.execute("SELECT year_number FROM year ORDER BY year_number")
        years = [str(row['year_number']) for row in cur.fetchall()]
        logger.info(f"✅ Years ({len(years)}): {', '.join(years)}")
        
        # Show users
        cur.execute('SELECT username, email FROM "user"')
        users = cur.fetchall()
        logger.info(f"✅ Users ({len(users)}):")
        for user in users:
            logger.info(f"  - {user['username']} ({user['email']})")
        
        cur.close()
        conn.close()
        
        logger.info("🎉 Database verification completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        if "does not exist" in str(e):
            logger.error("❌ Database 'monthly_expense_tracker' does not exist")
        elif "timeout" in str(e).lower():
            logger.error("❌ Connection timeout - check your network/security groups")
        else:
            logger.error(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking database: {e}")
        return False

def check_database_on_rds():
    """Check what databases exist on RDS instance"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found")
            return False
        
        # Connect to postgres database to list all databases
        temp_url = database_url.replace('/monthly_expense_tracker', '/postgres')
        
        logger.info("🔍 Checking all databases on RDS instance...")
        
        conn = psycopg2.connect(temp_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # List all databases
        cur.execute("""
            SELECT datname, datcollate, encoding 
            FROM pg_database 
            WHERE datistemplate = false
            ORDER BY datname
        """)
        databases = cur.fetchall()
        
        logger.info(f"✅ Databases on RDS ({len(databases)}):")
        for db in databases:
            logger.info(f"  - {db['datname']} (encoding: {db['encoding']})")
        
        # Check if our target database exists
        target_exists = any(db['datname'] == 'monthly_expense_tracker' for db in databases)
        
        if target_exists:
            logger.info("✅ Target database 'monthly_expense_tracker' exists!")
        else:
            logger.error("❌ Target database 'monthly_expense_tracker' NOT found!")
        
        cur.close()
        conn.close()
        return target_exists
        
    except Exception as e:
        logger.error(f"❌ Error checking RDS databases: {e}")
        return False

def main():
    """Main verification function"""
    logger.info("🚀 RDS Database Verification Check")
    logger.info("=" * 50)
    
    # Step 1: Check what databases exist on RDS
    logger.info("Step 1: Checking RDS instance databases...")
    rds_check = check_database_on_rds()
    
    if not rds_check:
        logger.error("💥 RDS database check failed!")
        return False
    
    print()
    
    # Step 2: Check our specific database contents
    logger.info("Step 2: Checking monthly_expense_tracker database...")
    db_check = check_database_exists()
    
    if not db_check:
        logger.error("💥 Database content check failed!")
        return False
    
    logger.info("=" * 50)
    logger.info("🎉 ALL CHECKS PASSED! Your RDS database is ready to use!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("💥 Database verification failed!")
        exit(1)
    else:
        logger.info("🚀 Database verification successful!")
