"""
Database Migration and Setup Test Script for RDS
This script handles complete database setup, migration, and verification for AWS RDS PostgreSQL
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """Create the monthly_expense_tracker database if it doesn't exist"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found in .env file")
            return False
        
        logger.info("🔄 Step 1: Checking/Creating monthly_expense_tracker database...")
        
        # Connect to default postgres database
        temp_url = database_url.replace('/monthly_expense_tracker', '/postgres')
        conn = psycopg2.connect(temp_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'monthly_expense_tracker'")
        exists = cur.fetchone()
        
        if not exists:
            logger.info("📝 Creating monthly_expense_tracker database...")
            cur.execute("CREATE DATABASE monthly_expense_tracker")
            logger.info("✅ Database 'monthly_expense_tracker' created successfully!")
        else:
            logger.info("ℹ️ Database 'monthly_expense_tracker' already exists")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating database: {e}")
        return False

def create_tables():
    """Create all required tables with proper schema"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        logger.info("🔄 Step 2: Creating database tables...")
        
        # Create User table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "user" (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                global_limit REAL DEFAULT 0
            )
        """)
        logger.info("✅ User table created/verified")
        
        # Create Month table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS month (
                month_id SERIAL PRIMARY KEY,
                month_name VARCHAR(20) NOT NULL UNIQUE
            )
        """)
        logger.info("✅ Month table created/verified")
        
        # Create Year table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS year (
                year_id SERIAL PRIMARY KEY,
                year_number INTEGER NOT NULL UNIQUE
            )
        """)
        logger.info("✅ Year table created/verified")
        
        # Create ExpenseCategory table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expense_category (
                expense_category_id SERIAL PRIMARY KEY,
                expense_category_name VARCHAR(100) NOT NULL,
                user_id INTEGER REFERENCES "user"(user_id),
                is_deleted BOOLEAN DEFAULT FALSE NOT NULL
            )
        """)
        logger.info("✅ ExpenseCategory table created/verified")
        
        # Create Expense table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expense (
                expense_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expense_item_price REAL NOT NULL,
                expense_category_id INTEGER NOT NULL,
                expense_description VARCHAR(255),
                expense_item_count INTEGER DEFAULT 1,
                expenditure_date DATE NOT NULL
            )
        """)
        logger.info("✅ Expense table created/verified")
        
        # Create MonthlyLimit table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS monthly_limit (
                monthly_limit_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                monthly_limit_amount REAL NOT NULL,
                month_id INTEGER NOT NULL,
                year_id INTEGER NOT NULL
            )
        """)
        logger.info("✅ MonthlyLimit table created/verified")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def seed_initial_data():
    """Seed the database with initial required data"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        logger.info("🔄 Step 3: Seeding initial data...")
        
        # Insert months if they don't exist
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        cur.execute("SELECT COUNT(*) FROM month")
        month_count = cur.fetchone()['count']
        
        if month_count == 0:
            for i, month_name in enumerate(month_names, 1):
                cur.execute(
                    "INSERT INTO month (month_id, month_name) VALUES (%s, %s)",
                    (i, month_name)
                )
            logger.info("✅ Inserted 12 months")
        else:
            logger.info("ℹ️ Months already exist in database")
        
        # Insert current year and next year if they don't exist
        current_year = datetime.now().year
        years_to_insert = [current_year, current_year + 1]
        
        for year in years_to_insert:
            cur.execute("SELECT COUNT(*) FROM year WHERE year_number = %s", (year,))
            year_exists = cur.fetchone()['count'] > 0
            
            if not year_exists:
                cur.execute("INSERT INTO year (year_number) VALUES (%s)", (year,))
                logger.info(f"✅ Inserted year {year}")
            else:
                logger.info(f"ℹ️ Year {year} already exists")
        
        # Insert default expense categories if they don't exist
        default_categories = [
            "Food & Dining", "Transportation", "Shopping", "Entertainment",
            "Bills & Utilities", "Healthcare", "Education", "Travel",
            "Personal Care", "Home & Garden", "Gifts & Donations", "Other"
        ]
        
        cur.execute("SELECT COUNT(*) FROM expense_category WHERE user_id IS NULL")
        category_count = cur.fetchone()['count']
        
        if category_count == 0:
            for category_name in default_categories:
                cur.execute(
                    "INSERT INTO expense_category (expense_category_name, user_id, is_deleted) VALUES (%s, %s, %s)",
                    (category_name, None, False)
                )
            logger.info(f"✅ Inserted {len(default_categories)} default categories")
        else:
            logger.info("ℹ️ Default categories already exist in database")
        
        # Create a default user if none exists
        cur.execute("SELECT COUNT(*) FROM \"user\"")
        user_count = cur.fetchone()['count']
        
        if user_count == 0:
            cur.execute(
                "INSERT INTO \"user\" (username, password, email, global_limit) VALUES (%s, %s, %s, %s)",
                ('admin', 'scrypt:32768:8:1$...', 'admin@example.com', 1000.0)  # Placeholder password
            )
            logger.info("✅ Created default admin user (remember to change password)")
        else:
            logger.info("ℹ️ Users already exist in database")
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error seeding data: {e}")
        return False

def test_database_operations():
    """Test basic database operations to ensure everything is working"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        logger.info("🔄 Step 4: Testing database operations...")
        
        # Test 1: Check PostgreSQL version
        cur.execute("SELECT version();")
        version = cur.fetchone()
        logger.info(f"✅ PostgreSQL Version: {version['version'][:50]}...")
        
        # Test 2: Count records in each table
        tables = ['user', 'month', 'year', 'expense_category', 'expense', 'monthly_limit']
        
        for table in tables:
            if table == 'user':
                cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            else:
                cur.execute(f'SELECT COUNT(*) FROM {table}')
            count = cur.fetchone()['count']
            logger.info(f"✅ Table '{table}' has {count} records")
        
        # Test 3: Verify relationships work
        cur.execute("""
            SELECT ec.expense_category_name, COUNT(*) as category_count
            FROM expense_category ec
            WHERE ec.user_id IS NULL AND ec.is_deleted = FALSE
            GROUP BY ec.expense_category_name
            ORDER BY ec.expense_category_name
            LIMIT 5
        """)
        categories = cur.fetchall()
        logger.info(f"✅ Sample categories: {[cat['expense_category_name'] for cat in categories]}")
        
        # Test 4: Check if we can insert/delete test data
        cur.execute(
            "INSERT INTO expense_category (expense_category_name, user_id, is_deleted) VALUES (%s, %s, %s) RETURNING expense_category_id",
            ('Test Category', None, False)
        )
        test_id = cur.fetchone()['expense_category_id']
        logger.info(f"✅ Test insert successful (ID: {test_id})")
        
        cur.execute("DELETE FROM expense_category WHERE expense_category_id = %s", (test_id,))
        logger.info("✅ Test delete successful")
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing database: {e}")
        return False

def verify_migration_complete():
    """Final verification that migration is complete and successful"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        logger.info("🔄 Step 5: Final migration verification...")
        
        # Check required tables exist
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        
        required_tables = ['user', 'month', 'year', 'expense_category', 'expense', 'monthly_limit']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            logger.info(f"✅ All required tables present: {required_tables}")
        
        # Check required columns exist
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'expense_category' AND table_schema = 'public'
        """)
        columns = [row['column_name'] for row in cur.fetchall()]
        
        required_columns = ['expense_category_id', 'expense_category_name', 'user_id', 'is_deleted']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            logger.error(f"❌ Missing columns in expense_category: {missing_columns}")
            return False
        else:
            logger.info("✅ All required columns present in expense_category table")
        
        # Check data integrity
        cur.execute("SELECT COUNT(*) FROM month")
        month_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM expense_category WHERE user_id IS NULL")
        category_count = cur.fetchone()['count']
        
        if month_count != 12:
            logger.error(f"❌ Expected 12 months, found {month_count}")
            return False
        
        if category_count < 10:
            logger.error(f"❌ Expected at least 10 default categories, found {category_count}")
            return False
        
        logger.info("✅ Data integrity checks passed")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration and test function"""
    logger.info("🚀 Starting RDS Database Migration and Setup...")
    logger.info("=" * 60)
    
    # Step 1: Create database
    if not create_database_if_not_exists():
        logger.error("❌ Database creation failed. Exiting.")
        return False
    
    # Step 2: Create tables
    if not create_tables():
        logger.error("❌ Table creation failed. Exiting.")
        return False
    
    # Step 3: Seed initial data
    if not seed_initial_data():
        logger.error("❌ Data seeding failed. Exiting.")
        return False
    
    # Step 4: Test operations
    if not test_database_operations():
        logger.error("❌ Database testing failed. Exiting.")
        return False
    
    # Step 5: Final verification
    if not verify_migration_complete():
        logger.error("❌ Migration verification failed. Exiting.")
        return False
    
    logger.info("=" * 60)
    logger.info("🎉 RDS Database Migration and Setup COMPLETED SUCCESSFULLY!")
    logger.info("✅ Your monthly expense tracker database is ready to use!")
    logger.info("✅ You can now start your Flask app and it will connect to RDS")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("💥 Migration failed! Please check the errors above.")
        exit(1)
    else:
        logger.info("🚀 Migration completed successfully! Your app is ready to deploy.")
