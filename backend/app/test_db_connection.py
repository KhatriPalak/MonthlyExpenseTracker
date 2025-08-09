
# Direct SQLAlchemy connection (edit credentials as needed)
from sqlalchemy import create_engine, inspect

# Set your credentials here
USERNAME = "postgres"  # change if needed
PASSWORD = "postgres"  # change if needed
HOST = "localhost"
PORT = "5432"
DBNAME = "expense_db"

DB_URL = f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

def test_connection():
    try:
        engine = create_engine(DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("Connected successfully! Tables in DB:", tables)
    except Exception as e:
        print("Database connection failed:", e)

if __name__ == "__main__":
    test_connection()