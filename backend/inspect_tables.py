"""
RDS Table Structure Inspector
Shows all tables, their columns, data types, and sample data
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

def inspect_all_tables():
    """Inspect all tables in the database"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found")
            return False
        
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        logger.info("🔍 INSPECTING ALL TABLES ON RDS DATABASE")
        logger.info("=" * 60)
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        
        logger.info(f"📊 FOUND {len(tables)} TABLES:")
        for i, table in enumerate(tables, 1):
            logger.info(f"  {i}. {table}")
        
        print()
        
        # Inspect each table in detail
        for table_num, table in enumerate(tables, 1):
            logger.info(f"🔍 TABLE {table_num}/{len(tables)}: {table.upper()}")
            logger.info("-" * 40)
            
            # Get table structure
            cur.execute("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table,))
            columns = cur.fetchall()
            
            logger.info(f"📋 COLUMNS ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                default = f" DEFAULT: {col['column_default']}" if col['column_default'] else ""
                logger.info(f"  • {col['column_name']}: {col['data_type']}{max_len} {nullable}{default}")
            
            # Get record count
            if table == 'user':
                cur.execute(f'SELECT COUNT(*) as count FROM "{table}"')
            else:
                cur.execute(f'SELECT COUNT(*) as count FROM {table}')
            count = cur.fetchone()['count']
            
            logger.info(f"📊 RECORD COUNT: {count}")
            
            # Show sample data if records exist
            if count > 0:
                logger.info("📝 SAMPLE DATA (first 3 records):")
                if table == 'user':
                    cur.execute(f'SELECT * FROM "{table}" LIMIT 3')
                else:
                    cur.execute(f'SELECT * FROM {table} LIMIT 3')
                samples = cur.fetchall()
                
                for i, record in enumerate(samples, 1):
                    logger.info(f"  Record {i}: {dict(record)}")
            else:
                logger.info("📝 SAMPLE DATA: (empty table)")
            
            print()
        
        cur.close()
        conn.close()
        
        logger.info("=" * 60)
        logger.info("🎉 TABLE INSPECTION COMPLETED!")
        logger.info(f"✅ All {len(tables)} tables are available and accessible")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inspecting tables: {e}")
        return False

def check_expected_tables():
    """Check if all expected tables are present"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        logger.info("✅ EXPECTED TABLES VERIFICATION")
        logger.info("-" * 30)
        
        # Expected tables for the expense tracker
        expected_tables = [
            'user',
            'month', 
            'year',
            'expense_category',
            'expense',
            'monthly_limit'
        ]
        
        # Get actual tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        actual_tables = [row['table_name'] for row in cur.fetchall()]
        
        # Check each expected table
        all_present = True
        for table in expected_tables:
            if table in actual_tables:
                logger.info(f"✅ {table} - PRESENT")
            else:
                logger.error(f"❌ {table} - MISSING")
                all_present = False
        
        # Check for unexpected tables
        unexpected = [t for t in actual_tables if t not in expected_tables]
        if unexpected:
            logger.info(f"ℹ️ Unexpected tables found: {unexpected}")
        
        cur.close()
        conn.close()
        
        return all_present
        
    except Exception as e:
        logger.error(f"❌ Error checking expected tables: {e}")
        return False

def main():
    """Main inspection function"""
    logger.info("🚀 RDS TABLE STRUCTURE INSPECTION")
    logger.info("=" * 60)
    
    # First check if expected tables are present
    expected_check = check_expected_tables()
    
    print()
    
    # Then do detailed inspection
    detailed_check = inspect_all_tables()
    
    if expected_check and detailed_check:
        logger.info("🎉 ALL TABLES ARE AVAILABLE AND PROPERLY STRUCTURED!")
        return True
    else:
        logger.error("💥 Some tables are missing or inaccessible!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("💥 Table inspection failed!")
        exit(1)
    else:
        logger.info("🚀 Table inspection successful!")
