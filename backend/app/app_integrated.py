import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from passlib.context import CryptContext
import jwt
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///expense_tracker.db'
    logger.info('Using SQLite database for development')
else:
    logger.info('Using configured database from environment')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

db = SQLAlchemy(app)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET = app.config['SECRET_KEY']
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ===================== DATABASE MODELS =====================

class Currency(db.Model):
    __tablename__ = "currency"
    currency_id = db.Column(db.Integer, primary_key=True)
    currency_name = db.Column(db.String(50), nullable=False)
    currency_symbol = db.Column(db.String(10), nullable=False)

class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    global_limit = db.Column(db.Float, default=0)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.currency_id'), default=1)
    name = db.Column(db.String(100))

class Expense(db.Model):
    __tablename__ = "expense"
    expense_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    expense_name = db.Column(db.String(200), nullable=True)  # New column for expense name
    expense_item_price = db.Column(db.Float, nullable=False)
    expense_category_id = db.Column(db.Integer, db.ForeignKey('expense_category.expense_category_id'), nullable=False)
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
    monthly_limit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    monthly_limit_amount = db.Column(db.Float, nullable=False)
    month_id = db.Column(db.Integer, db.ForeignKey('month.month_id'), nullable=False)
    year_id = db.Column(db.Integer, db.ForeignKey('year.year_id'), nullable=False)

class Month(db.Model):
    __tablename__ = "month"
    month_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    month_name = db.Column(db.String(20), nullable=False, unique=True)

class Year(db.Model):
    __tablename__ = "year"
    year_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    year_number = db.Column(db.Integer, nullable=False, unique=True)

# ===================== HELPER FUNCTIONS =====================

def create_access_token(data):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token):
    """Verify JWT token"""
    try:
        logger.info(f'verify_token - Attempting to decode token: {token[:20]}...')
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f'verify_token - Token decoded successfully. Payload: {payload}')
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.error(f'verify_token - Token expired: {e}')
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f'verify_token - Invalid token: {e}')
        return None

def get_current_user_id():
    """Get current user ID from token"""
    auth_header = request.headers.get('Authorization')
    logger.info(f'get_current_user_id - Auth header: {auth_header[:50] if auth_header else "None"}')
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        logger.info(f'get_current_user_id - Token extracted: {token[:20]}...')
        
        payload = verify_token(token)
        if payload:
            user_id = payload.get('user_id')
            logger.info(f'get_current_user_id - User ID from token: {user_id}')
            return user_id
        else:
            logger.warning('get_current_user_id - Token verification failed!')
    else:
        logger.warning('get_current_user_id - No valid auth header found!')
    
    logger.error('get_current_user_id - No authenticated user found')
    return None  # No default user - authentication required

# ===================== AUTHENTICATION ENDPOINTS =====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration endpoint"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not all([name, email, password]):
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Create username from email
        username = email.split('@')[0]
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create new user
        new_user = User(
            username=username,
            name=name,
            email=email,
            password=hashed_password,
            global_limit=0,
            currency_id=1  # Default to USD
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create token
        token = create_access_token({
            'user_id': new_user.user_id,
            'username': new_user.username,
            'email': new_user.email
        })
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': new_user.user_id,
                'name': new_user.name,
                'email': new_user.email
            },
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f'Error in signup: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not pwd_context.verify(password, user.password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create token
        token = create_access_token({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email
        })
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.user_id,
                'name': user.name or user.username,
                'email': user.email
            },
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f'Error in login: {e}')
        return jsonify({'error': str(e)}), 500

# ===================== EXPENSE ENDPOINTS =====================

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Get expenses for a specific year and month"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not year or not month:
            return jsonify({'error': 'Year and month are required'}), 400
        
        # Get expenses for the specified month and year
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.expenditure_date >= start_date,
            Expense.expenditure_date < end_date
        ).all()
        
        expenses_data = []
        for expense in expenses:
            # Get category name
            category = ExpenseCategory.query.get(expense.expense_category_id)
            expenses_data.append({
                'expense_id': expense.expense_id,
                'expense_name': expense.expense_name or '',  # Include expense name
                'expense_item_price': expense.expense_item_price,
                'expense_category_id': expense.expense_category_id,
                'expense_category_name': category.expense_category_name if category else 'Unknown',
                'expense_description': expense.expense_description or '',
                'expense_item_count': expense.expense_item_count,
                'expenditure_date': expense.expenditure_date.isoformat()
            })
        
        return jsonify(expenses_data), 200
        
    except Exception as e:
        logger.error(f'Error fetching expenses: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """Add a new expense"""
    try:
        data = request.get_json()
        logger.info(f'Add expense request data: {data}')
        year = data.get('year')
        month = data.get('month')
        expense_data = data.get('expense', {})
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
            
        logger.info(f'Expense data: {expense_data}')
        
        if not all([year, month, expense_data]):
            return jsonify({'error': 'Year, month, and expense data are required'}), 400
        
        # Parse expense data - handle both field names from frontend
        expense_date = expense_data.get('expenditure_date') or expense_data.get('date')
        if expense_date:
            expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
        else:
            expense_date = datetime(year, month, 1).date()
        
        # Get category ID - frontend sends category_id, not expense_category_id
        category_id = expense_data.get('category_id') or expense_data.get('expense_category_id')
        if not category_id:
            return jsonify({'error': 'Category ID is required'}), 400
            
        # Get amount - frontend sends 'amount', not 'expense_item_price'
        amount = expense_data.get('amount') or expense_data.get('expense_item_price')
        if not amount:
            return jsonify({'error': 'Amount is required'}), 400
        
        # Get expense name - frontend sends 'name'
        expense_name = expense_data.get('name') or expense_data.get('expense_name', '')
        
        # Create new expense
        new_expense = Expense(
            user_id=user_id,
            expense_name=expense_name,  # Save the expense name
            expense_item_price=float(amount),
            expense_category_id=int(category_id),
            expense_description=expense_data.get('description') or expense_data.get('expense_description', ''),
            expense_item_count=int(expense_data.get('expense_item_count', 1)),
            expenditure_date=expense_date
        )
        
        db.session.add(new_expense)
        db.session.commit()
        
        return jsonify({
            'message': 'Expense added successfully',
            'expense_id': new_expense.expense_id
        }), 201
        
    except Exception as e:
        logger.error(f'Error adding expense: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['DELETE'])
def delete_expense():
    """Delete an expense"""
    try:
        data = request.get_json()
        expense_id = data.get('expense_id')
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not expense_id:
            return jsonify({'error': 'Expense ID is required'}), 400
        
        # Find and delete expense
        expense = Expense.query.filter_by(
            expense_id=expense_id,
            user_id=user_id
        ).first()
        
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({'message': 'Expense deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f'Error deleting expense: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===================== LIMIT ENDPOINTS =====================

@app.route('/api/global_limit', methods=['GET'])
def get_global_limit():
    """Get user's global spending limit"""
    try:
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
            
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'global_limit': user.global_limit or 0}), 200
        
    except Exception as e:
        logger.error(f'Error fetching global limit: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/global_limit', methods=['POST'])
def set_global_limit():
    """Set user's global spending limit and currency"""
    try:
        logger.info('=== SET GLOBAL LIMIT START ===')
        
        # Log headers
        auth_header = request.headers.get('Authorization')
        logger.info(f'Authorization header: {auth_header[:50] if auth_header else "NO AUTH HEADER"}')
        
        data = request.get_json()
        logger.info(f'Request data: {data}')
        
        global_limit = data.get('global_limit')
        currency_id = data.get('currency_id')
        
        # Get user ID and log the process
        user_id = get_current_user_id()
        logger.info(f'Extracted user_id from token: {user_id}')
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        logger.info(f'Setting global limit: {global_limit}, currency_id: {currency_id} for user_id: {user_id}')
        
        if global_limit is None:
            logger.error('Global limit is None')
            return jsonify({'error': 'Global limit is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f'User not found with id: {user_id}')
            return jsonify({'error': f'User not found with id: {user_id}'}), 404
        
        logger.info(f'Found user: {user.username} (id: {user.user_id})')
        logger.info(f'Current global_limit: {user.global_limit}, current currency_id: {user.currency_id}')
        
        user.global_limit = float(global_limit)
        
        # Update currency if provided
        if currency_id is not None:
            user.currency_id = int(currency_id)
            logger.info(f'Updated currency_id to {currency_id} for user {user_id}')
        
        db.session.commit()
        logger.info(f'✅ Successfully saved global_limit={user.global_limit} and currency_id={user.currency_id} for user {user.username} (id: {user_id})')
        
        return jsonify({
            'message': 'Global limit and currency updated successfully',
            'global_limit': user.global_limit,
            'currency_id': user.currency_id,
            'user_id': user_id,
            'username': user.username
        }), 200
        
    except Exception as e:
        logger.error(f'Error setting global limit: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/limit', methods=['GET'])
def get_monthly_limit():
    """Get monthly spending limit"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not year or not month:
            return jsonify({'error': 'Year and month are required'}), 400
        
        # Get or create year
        year_obj = Year.query.filter_by(year_number=year).first()
        if not year_obj:
            return jsonify({'limit': 0}), 200
        
        # Get monthly limit
        monthly_limit = MonthlyLimit.query.filter_by(
            user_id=user_id,
            month_id=month,
            year_id=year_obj.year_id
        ).first()
        
        return jsonify({
            'limit': monthly_limit.monthly_limit_amount if monthly_limit else 0
        }), 200
        
    except Exception as e:
        logger.error(f'Error fetching monthly limit: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/limit', methods=['POST'])
def set_monthly_limit():
    """Set monthly spending limit"""
    try:
        data = request.get_json()
        year = data.get('year')
        month = data.get('month')
        limit = data.get('limit')
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not all([year, month]) or limit is None:
            return jsonify({'error': 'Year, month, and limit are required'}), 400
        
        # Get or create year
        year_obj = Year.query.filter_by(year_number=year).first()
        if not year_obj:
            year_obj = Year(year_number=year)
            db.session.add(year_obj)
            db.session.flush()
        
        # Check if monthly limit exists
        monthly_limit = MonthlyLimit.query.filter_by(
            user_id=user_id,
            month_id=month,
            year_id=year_obj.year_id
        ).first()
        
        if monthly_limit:
            # Update existing limit
            if limit == 0:
                # Delete if setting to 0
                db.session.delete(monthly_limit)
            else:
                monthly_limit.monthly_limit_amount = float(limit)
        else:
            # Create new limit if not 0
            if limit > 0:
                monthly_limit = MonthlyLimit(
                    user_id=user_id,
                    monthly_limit_amount=float(limit),
                    month_id=month,
                    year_id=year_obj.year_id
                )
                db.session.add(monthly_limit)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Monthly limit updated successfully',
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f'Error setting monthly limit: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===================== CURRENCY ENDPOINTS =====================

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    """Get all available currencies"""
    try:
        currencies = Currency.query.all()
        
        if not currencies:
            # Add default currencies
            default_currencies = [
                {'currency_id': 1, 'currency_name': 'US Dollar', 'currency_symbol': '$'},
                {'currency_id': 2, 'currency_name': 'Euro', 'currency_symbol': '€'},
                {'currency_id': 3, 'currency_name': 'British Pound', 'currency_symbol': '£'},
                {'currency_id': 4, 'currency_name': 'Indian Rupee', 'currency_symbol': '₹'},
                {'currency_id': 5, 'currency_name': 'Japanese Yen', 'currency_symbol': '¥'},
            ]
            
            for curr in default_currencies:
                currency = Currency(**curr)
                db.session.add(currency)
            
            db.session.commit()
            currencies = Currency.query.all()
        
        currencies_data = [
            {
                'currency_id': curr.currency_id,
                'currency_name': curr.currency_name,
                'currency_symbol': curr.currency_symbol
            }
            for curr in currencies
        ]
        
        return jsonify({'currencies': currencies_data}), 200
        
    except Exception as e:
        logger.error(f'Error fetching currencies: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/currency', methods=['POST'])
def update_user_currency():
    """Get or update user's preferred currency"""
    try:
        data = request.get_json()
        currency_id = data.get('currency_id') if data else None
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # If no currency_id provided, just return current currency
        if not currency_id:
            current_currency = Currency.query.get(user.currency_id) if user.currency_id else Currency.query.get(1)
            if current_currency:
                return jsonify({
                    'currency_id': current_currency.currency_id,
                    'currency_name': current_currency.currency_name,
                    'currency_symbol': current_currency.currency_symbol
                }), 200
            else:
                return jsonify({'error': 'No currency set'}), 404
        
        # Verify currency exists before updating
        currency = Currency.query.get(currency_id)
        if not currency:
            return jsonify({'error': 'Invalid currency'}), 400
        
        user.currency_id = currency_id
        db.session.commit()
        
        return jsonify({
            'message': 'Currency updated successfully',
            'currency': {
                'currency_id': currency.currency_id,
                'currency_name': currency.currency_name,
                'currency_symbol': currency.currency_symbol
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error updating currency: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===================== CATEGORY ENDPOINTS =====================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all expense categories"""
    try:
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get both global and user-specific categories
        categories = ExpenseCategory.query.filter(
            db.or_(
                ExpenseCategory.user_id == None,
                ExpenseCategory.user_id == user_id
            ),
            ExpenseCategory.is_deleted == False
        ).order_by(ExpenseCategory.expense_category_name).all()
        
        if not categories:
            # Create default categories
            default_categories = [
                'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
                'Bills & Utilities', 'Healthcare', 'Travel', 'Education', 'Other'
            ]
            
            for cat_name in default_categories:
                category = ExpenseCategory(
                    expense_category_name=cat_name,
                    user_id=None,
                    is_deleted=False
                )
                db.session.add(category)
            
            db.session.commit()
            categories = ExpenseCategory.query.filter_by(is_deleted=False).all()
        
        categories_data = [
            {
                'category_id': cat.expense_category_id,
                'category_name': cat.expense_category_name,
                'is_global': cat.user_id is None
            }
            for cat in categories
        ]
        
        return jsonify({'categories': categories_data}), 200
        
    except Exception as e:
        logger.error(f'Error fetching categories: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['POST'])
def add_category():
    """Add a new expense category"""
    try:
        data = request.get_json()
        category_name = data.get('category_name')
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not category_name:
            return jsonify({'error': 'Category name is required'}), 400
        
        # Check if category already exists for this user
        existing = ExpenseCategory.query.filter_by(
            expense_category_name=category_name,
            user_id=user_id,
            is_deleted=False
        ).first()
        
        if existing:
            return jsonify({'error': 'Category already exists'}), 400
        
        # Create new category
        new_category = ExpenseCategory(
            expense_category_name=category_name,
            user_id=user_id,
            is_deleted=False
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category added successfully',
            'category': {
                'category_id': new_category.expense_category_id,
                'category_name': new_category.expense_category_name,
                'is_global': False
            }
        }), 201
        
    except Exception as e:
        logger.error(f'Error adding category: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['DELETE'])
def delete_category():
    """Soft delete an expense category"""
    try:
        data = request.get_json()
        category_id = data.get('category_id')
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not category_id:
            return jsonify({'error': 'Category ID is required'}), 400
        
        # Find category (only user's own categories can be deleted)
        category = ExpenseCategory.query.filter_by(
            expense_category_id=category_id,
            user_id=user_id
        ).first()
        
        if not category:
            return jsonify({'error': 'Category not found or cannot be deleted'}), 404
        
        # Soft delete
        category.is_deleted = True
        db.session.commit()
        
        return jsonify({'message': 'Category deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f'Error deleting category: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===================== EXISTING ENDPOINTS =====================

@app.route('/api/months', methods=['GET'])
def get_months():
    """Get all months"""
    try:
        months = Month.query.order_by(Month.month_id).all()
        
        if not months:
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            for i, month_name in enumerate(month_names, 1):
                month = Month(month_id=i, month_name=month_name)
                db.session.add(month)
            
            db.session.commit()
            months = Month.query.order_by(Month.month_id).all()
        
        months_data = [
            {
                'month_id': month.month_id,
                'month_name': month.month_name
            }
            for month in months
        ]
        
        return jsonify({'months': months_data}), 200
        
    except Exception as e:
        logger.error(f'Error fetching months: {e}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Test database connection"""
    try:
        # Test query
        user_count = User.query.count()
        return jsonify({
            'status': 'success',
            'message': 'Database connected successfully',
            'user_count': user_count
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ===================== SUMMARY ENDPOINTS (BONUS) =====================

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get expense summary"""
    try:
        summary_type = request.args.get('type', 'monthly')
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        user_id = get_current_user_id()
        
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if summary_type == 'monthly' and year and month:
            # Get monthly summary
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()
            
            expenses = Expense.query.filter(
                Expense.user_id == user_id,
                Expense.expenditure_date >= start_date,
                Expense.expenditure_date < end_date
            ).all()
            
            total = sum(e.expense_item_price * e.expense_item_count for e in expenses)
            
            # Get category breakdown
            category_totals = {}
            for expense in expenses:
                category = ExpenseCategory.query.get(expense.expense_category_id)
                cat_name = category.expense_category_name if category else 'Unknown'
                if cat_name not in category_totals:
                    category_totals[cat_name] = 0
                category_totals[cat_name] += expense.expense_item_price * expense.expense_item_count
            
            return jsonify({
                'type': 'monthly',
                'year': year,
                'month': month,
                'total_expenses': total,
                'expense_count': len(expenses),
                'categories': category_totals
            }), 200
            
        elif summary_type == 'yearly' and year:
            # Get yearly summary
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year + 1, 1, 1).date()
            
            expenses = Expense.query.filter(
                Expense.user_id == user_id,
                Expense.expenditure_date >= start_date,
                Expense.expenditure_date < end_date
            ).all()
            
            total = sum(e.expense_item_price * e.expense_item_count for e in expenses)
            
            # Get monthly breakdown
            monthly_totals = {month: 0 for month in range(1, 13)}
            for expense in expenses:
                month = expense.expenditure_date.month
                monthly_totals[month] += expense.expense_item_price * expense.expense_item_count
            
            return jsonify({
                'type': 'yearly',
                'year': year,
                'total_expenses': total,
                'expense_count': len(expenses),
                'monthly_breakdown': monthly_totals
            }), 200
        
        return jsonify({'error': 'Invalid summary type or missing parameters'}), 400
        
    except Exception as e:
        logger.error(f'Error getting summary: {e}')
        return jsonify({'error': str(e)}), 500

# ===================== CORS AND ERROR HANDLERS =====================

# CORS is already handled by Flask-CORS above, so we don't need this
# @app.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ===================== APP INITIALIZATION =====================

if __name__ == '__main__':
    with app.app_context():
        try:
            logger.info('Creating database tables if they do not exist...')
            db.create_all()
            logger.info('Database tables created successfully')
            
            # Initialize currencies if not present
            currency_count = Currency.query.count()
            if currency_count == 0:
                logger.info('Adding currencies...')
                currencies = [
                    Currency(currency_id=1, currency_name="USD", currency_symbol="$"),
                    Currency(currency_id=2, currency_name="EUR", currency_symbol="€"),
                    Currency(currency_id=3, currency_name="GBP", currency_symbol="£"),
                    Currency(currency_id=4, currency_name="JPY", currency_symbol="¥"),
                    Currency(currency_id=5, currency_name="CAD", currency_symbol="C$"),
                    Currency(currency_id=6, currency_name="AUD", currency_symbol="A$"),
                    Currency(currency_id=7, currency_name="CHF", currency_symbol="Fr"),
                    Currency(currency_id=8, currency_name="CNY", currency_symbol="¥"),
                    Currency(currency_id=9, currency_name="INR", currency_symbol="₹"),
                    Currency(currency_id=10, currency_name="MXN", currency_symbol="$"),
                ]
                db.session.add_all(currencies)
                db.session.commit()
                logger.info(f'Added {len(currencies)} currencies')
            
            # Initialize months if not present
            month_count = Month.query.count()
            if month_count == 0:
                logger.info('Adding months...')
                months = [
                    Month(month_id=1, month_name="January"),
                    Month(month_id=2, month_name="February"),
                    Month(month_id=3, month_name="March"),
                    Month(month_id=4, month_name="April"),
                    Month(month_id=5, month_name="May"),
                    Month(month_id=6, month_name="June"),
                    Month(month_id=7, month_name="July"),
                    Month(month_id=8, month_name="August"),
                    Month(month_id=9, month_name="September"),
                    Month(month_id=10, month_name="October"),
                    Month(month_id=11, month_name="November"),
                    Month(month_id=12, month_name="December"),
                ]
                db.session.add_all(months)
                db.session.commit()
                logger.info(f'Added {len(months)} months')
            
            # Initialize years if not present
            year_count = Year.query.count()
            if year_count == 0:
                logger.info('Adding years...')
                years = [
                    Year(year_id=1, year_number=2024),
                    Year(year_id=2, year_number=2025),
                    Year(year_id=3, year_number=2026),
                ]
                db.session.add_all(years)
                db.session.commit()
                logger.info(f'Added {len(years)} years')
            
            # Initialize default categories if not present
            category_count = ExpenseCategory.query.filter_by(user_id=None).count()
            if category_count == 0:
                logger.info('Adding default expense categories...')
                categories = [
                    ExpenseCategory(expense_category_name="Food & Dining", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Transportation", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Shopping", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Entertainment", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Bills & Utilities", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Healthcare", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Education", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Travel", user_id=None, is_deleted=False),
                    ExpenseCategory(expense_category_name="Other", user_id=None, is_deleted=False),
                ]
                db.session.add_all(categories)
                db.session.commit()
                logger.info(f'Added {len(categories)} default categories')
            
            # No default user - users must sign up
            user_count = User.query.count()
            if user_count == 0:
                logger.info('No users found - users will be created through signup')
            else:
                logger.info(f'Found {user_count} existing users')
            
        except Exception as e:
            logger.error(f'Error initializing database: {e}')
    
    port = int(os.getenv('PORT', 5002))
    host = os.getenv('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=True)