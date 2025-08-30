import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Database configuration - supports both SQLite and PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Fallback to SQLite for development
    DATABASE_URL = 'sqlite:///expense_tracker.db'
    logger.info('Using SQLite database for development')
else:
    logger.info('Using configured database from environment')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

db = SQLAlchemy(app)

# Database connection function (for PostgreSQL only)
def get_db_connection():
    try:
        if DATABASE_URL.startswith('postgresql://'):
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return conn
        else:
            logger.info('Using SQLAlchemy for database operations (SQLite)')
            return None
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Test database connection endpoint
@app.route('/api/test-db', methods=['GET'])
def test_db():
    try:
        if DATABASE_URL.startswith('postgresql://'):
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT version();")
                version = cur.fetchone()
                cur.close()
                conn.close()
                return jsonify({
                    "status": "success",
                    "message": "PostgreSQL (RDS) Database connected successfully",
                    "version": version['version'],
                    "database_type": "PostgreSQL"
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Failed to connect to PostgreSQL database"
                }), 500
        else:
            # SQLite test
            db.engine.execute("SELECT 1")
            return jsonify({
                "status": "success",
                "message": "SQLite Database connected successfully",
                "database_type": "SQLite"
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ... (rest of your existing models and routes stay the same) ...

# Database Models
class Expense(db.Model):
    expense_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    expense_item_price = db.Column(db.Float, nullable=False)
    expense_category_id = db.Column(db.Integer, nullable=False)
    expense_description = db.Column(db.String(255))
    expense_item_count = db.Column(db.Integer, default=1)
    expenditure_date = db.Column(db.Date, nullable=False)

class ExpenseCategory(db.Model):
    __tablename__ = "expense_category"
    expense_category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    expense_category_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

class MonthlyLimit(db.Model):
    __tablename__ = "monthly_limit"
    monthly_limit_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    monthly_limit_amount = db.Column(db.Float, nullable=False)
    month_id = db.Column(db.Integer, nullable=False)
    year_id = db.Column(db.Integer, nullable=False)

class Month(db.Model):
    __tablename__ = "month"
    month_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    month_name = db.Column(db.String(20), nullable=False, unique=True)

class Year(db.Model):
    __tablename__ = "year"
    year_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    year_number = db.Column(db.Integer, nullable=False, unique=True)

class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    global_limit = db.Column(db.Float, default=0)

# API Routes
@app.route('/api/months', methods=['GET'])
def get_months():
    try:
        logger.info('GET /api/months called')
        
        months = Month.query.order_by(Month.month_id).all()
        
        if not months:
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            months_data = []
            for i, month_name in enumerate(month_names, 1):
                month = Month(month_id=i, month_name=month_name)
                db.session.add(month)
                months_data.append({
                    'month_id': i,
                    'month_name': month_name
                })
            
            db.session.commit()
            logger.info('Created %d months in database', len(months_data))
            return jsonify({'months': months_data})
        else:
            months_data = [
                {
                    'month_id': month.month_id,
                    'month_name': month.month_name
                }
                for month in months
            ]
            
            logger.info('Returning %d months from database', len(months_data))
            return jsonify({'months': months_data})
        
    except Exception as e:
        logger.error('Error fetching months: %s', e)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        logger.info('GET /api/categories called')
        
        user_id = 1  # For now, using default user
        
        try:
            categories = ExpenseCategory.query.filter(
                ((ExpenseCategory.user_id == None) | (ExpenseCategory.user_id == user_id)),
                ExpenseCategory.is_deleted == False
            ).order_by(ExpenseCategory.expense_category_name).all()
        except Exception as e:
            logger.warning('is_deleted column not available, using fallback query: %s', e)
            categories = ExpenseCategory.query.filter(
                (ExpenseCategory.user_id == None) | (ExpenseCategory.user_id == user_id)
            ).order_by(ExpenseCategory.expense_category_name).all()
        
        if not categories:
            # Create default categories
            default_categories = [
                'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
                'Bills & Utilities', 'Healthcare', 'Travel', 'Other'
            ]
            
            categories_data = []
            for cat_name in default_categories:
                category = ExpenseCategory(
                    expense_category_name=cat_name,
                    user_id=None,  # Global category
                    is_deleted=False
                )
                db.session.add(category)
                categories_data.append({
                    'category_id': None,  # Will be set after commit
                    'category_name': cat_name,
                    'is_global': True
                })
            
            db.session.commit()
            logger.info('Created %d default categories', len(categories_data))
            
            # Re-query to get IDs
            categories = ExpenseCategory.query.filter(
                ExpenseCategory.user_id == None
            ).all()
        
        categories_data = [
            {
                'category_id': category.expense_category_id,
                'category_name': category.expense_category_name.title(),
                'is_global': category.user_id is None
            }
            for category in categories
        ]
        
        logger.info('Returning %d categories from database', len(categories_data))
        return jsonify({'categories': categories_data})
        
    except Exception as e:
        logger.error('Error fetching categories: %s', e)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Create tables when app starts
    with app.app_context():
        try:
            logger.info('Creating database tables if they do not exist...')
            db.create_all()
            logger.info('Database tables created successfully')
        except Exception as e:
            logger.error('Error creating database tables: %s', e)
    
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=True)