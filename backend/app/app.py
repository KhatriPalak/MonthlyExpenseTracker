
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import logging
import hashlib
import secrets
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=False)

@app.before_request
def log_request_info():
    logger.info('Request: %s %s', request.method, request.url)
    logger.info('Headers: %s', dict(request.headers))
    if request.data:
        logger.info('Body: %s', request.data.decode('utf-8'))

@app.after_request
def log_response_info(response):
    logger.info('Response: %s %s', response.status_code, response.status)
    logger.info('Response Headers: %s', dict(response.headers))
    return response

# Database config
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PW = os.environ.get('POSTGRES_PW', 'postgres')
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'localhost:5432')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'expense_db')
DB_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PW}@{POSTGRES_URL}/{POSTGRES_DB}'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)  # Foreign key to user table
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # Soft delete flag

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

class GlobalLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float, nullable=False)

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

    def set_password(self, password):
        """Hash and set the password"""
        self.password = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return self.password == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'global_limit': self.global_limit
        }

@app.route('/api/months', methods=['GET'])
def get_months():
    """Fetch all months from the database"""
    try:
        logger.info('GET /api/months called')
        
        # Fetch months from database
        months = Month.query.order_by(Month.month_id).all()
        
        if not months:
            # If no months in database, create default months
            logger.info('No months found in database, creating default months')
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            months_data = []
            for i, month_name in enumerate(month_names, 1):
                # Create month in database
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
            # Return existing months from database
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
    """Fetch all expense categories for the current user (including global categories)"""
    try:
        logger.info('GET /api/categories called')
        
        # For now, using user_id = 1 (you can modify this to get from auth token)
        user_id = 1
        
        # Query categories - try with is_deleted filter, fall back if column doesn't exist
        try:
            categories = ExpenseCategory.query.filter(
                ((ExpenseCategory.user_id == None) | (ExpenseCategory.user_id == user_id)),
                ExpenseCategory.is_deleted == False
            ).order_by(ExpenseCategory.expense_category_name).all()
            logger.info('Queried categories with is_deleted filter')
        except Exception as e:
            logger.warning('is_deleted column not available, using fallback query: %s', e)
            categories = ExpenseCategory.query.filter(
                (ExpenseCategory.user_id == None) | (ExpenseCategory.user_id == user_id)
            ).order_by(ExpenseCategory.expense_category_name).all()
        
        categories_data = [
            {
                'category_id': category.expense_category_id,
                'category_name': category.expense_category_name.title(),  # Show with first letter capital
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

@app.route('/api/categories', methods=['POST'])
def add_category():
    """Add a new user-specific category or reactivate existing one"""
    try:
        logger.info('POST /api/categories called')
        data = request.json
        
        category_name_input = data.get('category_name', '').strip()
        if not category_name_input:
            return jsonify({'error': 'Category name is required'}), 400
        
        # For now, using user_id = 1 (you can modify this to get from auth token)
        user_id = 1
        
        # Store in database as trimmed and lowercase
        category_name_db = category_name_input.lower().strip()
        
        # Check if category already exists for this user (including deleted ones)
        existing = ExpenseCategory.query.filter(
            ExpenseCategory.expense_category_name == category_name_db,
            ExpenseCategory.user_id == user_id
        ).first()
        
        if existing:
            # Check if category is deleted and can be reactivated
            try:
                if existing.is_deleted:
                    # Reactivate the deleted category
                    existing.is_deleted = False
                    db.session.commit()
                    logger.info('Reactivated deleted category: %s for user %d', category_name_input, user_id)
                    
                    return jsonify({
                        'success': True,
                        'category': {
                            'category_id': existing.expense_category_id,
                            'category_name': category_name_input.title(),  # Return with proper capitalization
                            'is_global': False
                        }
                    }), 200
                else:
                    return jsonify({'error': 'Category already exists'}), 400
            except AttributeError:
                # is_deleted column doesn't exist, just check if category exists
                return jsonify({'error': 'Category already exists'}), 400
        
        # Check if a global category with the same name exists
        try:
            global_existing = ExpenseCategory.query.filter(
                ExpenseCategory.expense_category_name == category_name_db,
                ExpenseCategory.user_id == None,
                ExpenseCategory.is_deleted == False
            ).first()
        except Exception:
            # is_deleted column doesn't exist, check without is_deleted filter
            global_existing = ExpenseCategory.query.filter(
                ExpenseCategory.expense_category_name == category_name_db,
                ExpenseCategory.user_id == None
            ).first()
        
        if global_existing:
            return jsonify({'error': 'A global category with this name already exists'}), 400
        
        # Create new category
        try:
            new_category = ExpenseCategory(
                expense_category_name=category_name_db,
                user_id=user_id,
                is_deleted=False
            )
        except Exception:
            # is_deleted column doesn't exist, create without it
            new_category = ExpenseCategory(
                expense_category_name=category_name_db,
                user_id=user_id
            )
        
        db.session.add(new_category)
        db.session.commit()
        
        logger.info('Created new category: %s (stored as: %s) for user %d', category_name_input, category_name_db, user_id)
        
        return jsonify({
            'success': True,
            'category': {
                'category_id': new_category.expense_category_id,
                'category_name': category_name_input.title(),  # Return with proper capitalization
                'is_global': False
            }
        }), 201
        
    except Exception as e:
        logger.error('Error creating category: %s', e)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Soft delete a category by setting is_deleted = True"""
    try:
        logger.info('DELETE /api/categories/%d called', category_id)
        
        # For now, using user_id = 1 (you can modify this to get from auth token)
        user_id = 1
        
        # Find the category
        category = ExpenseCategory.query.filter_by(
            expense_category_id=category_id
        ).first()
        
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Check if category is already deleted (if is_deleted column exists)
        try:
            if hasattr(category, 'is_deleted') and category.is_deleted:
                return jsonify({'error': 'Category already deleted'}), 404
        except Exception as e:
            logger.warning('Could not check is_deleted status: %s', e)
        
        # Allow deletion of both user-specific categories and global categories
        # Users can only delete their own categories, but can also delete global categories
        if category.user_id is not None and category.user_id != user_id:
            return jsonify({'error': 'You can only delete your own categories'}), 403
        
        category_name = category.expense_category_name.title()
        
        # Perform soft delete by setting is_deleted to True
        try:
            if hasattr(category, 'is_deleted'):
                category.is_deleted = True
                db.session.commit()
                logger.info('Soft deleted category: %s (ID: %d)', category_name, category_id)
            else:
                # Fallback: is_deleted column doesn't exist, return error
                logger.warning('Cannot soft delete - is_deleted column not found for category: %s (ID: %d)', category_name, category_id)
                return jsonify({'error': 'Soft delete not supported - is_deleted column missing. Please run database migration.'}), 500
        except Exception as e:
            logger.error('Error setting is_deleted flag: %s', e)
            db.session.rollback()
            return jsonify({'error': f'Failed to delete category: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Category "{category_name}" deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error('Error deleting category: %s', e)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    logger.info('GET /api/expenses called')
    year_raw = request.args.get('year')
    month_raw = request.args.get('month')
    logger.info('Query params - year: %s, month: %s', year_raw, month_raw)
    
    if year_raw is None or month_raw is None:
        logger.error('Missing year or month parameter')
        return jsonify({'error': 'Missing year or month parameter'}), 400
    
    try:
        year = int(year_raw)
        month = int(month_raw)
        logger.info('Parsed year: %d, month: %d', year, month)
    except (TypeError, ValueError):
        logger.error('Invalid year or month format')
        return jsonify({'error': 'Year and month must be integers'}), 400
    
    try:
        from sqlalchemy import extract
        exp_objs = Expense.query.filter(
            extract('year', Expense.expenditure_date) == year,
            extract('month', Expense.expenditure_date) == month
        ).all()
        logger.info('Found %d expense records', len(exp_objs))
    except Exception as e:
        logger.error('Database query error: %s', str(e))
        return jsonify({'error': 'Database error'}), 500
    result = [
        {
            'expense_id': exp.expense_id,
            'user_id': exp.user_id,
            'expense_item_price': exp.expense_item_price,
            'expense_category_id': exp.expense_category_id,
            'expense_description': exp.expense_description,
            'expense_item_count': exp.expense_item_count,
            'expenditure_date': exp.expenditure_date.isoformat()
        } for exp in exp_objs
    ]
    logger.info('Returning %d expenses', len(result))
    return jsonify(result)


@app.route('/api/expenses', methods=['POST'])
def add_expense():
    logger.info('POST /api/expenses called')
    try:
        data = request.json
        logger.info('Request data: %s', data)
        
        year_raw = data.get('year')
        month_raw = data.get('month')
        expense = data.get('expense')
        
        if year_raw is None or month_raw is None or expense is None:
            logger.error('Missing required data: year=%s, month=%s, expense=%s', year_raw, month_raw, expense)
            return jsonify({'error': 'Missing year, month, or expense data'}), 400
            
        try:
            year = int(year_raw)
            month = int(month_raw)
        except (TypeError, ValueError) as e:
            logger.error('Invalid year/month format: %s', e)
            return jsonify({'error': 'Year and month must be integers'}), 400
        
        # Parse the expense date
        from datetime import datetime
        try:
            expenditure_date = datetime.strptime(expense.get('date', ''), '%Y-%m-%d').date()
        except ValueError as e:
            logger.error('Invalid date format: %s', e)
            return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
        
        # Create expense object with correct field mapping
        exp_obj = Expense(
            user_id=1,  # Default user ID for now
            expense_item_price=float(expense.get('amount', 0)),
            expense_category_id=int(expense.get('category_id', 1)),  # Use provided category_id or default to 1
            expense_description=f"{expense.get('name', 'Unknown')} - {expense.get('description', '')}".strip(' -'),
            expense_item_count=1,
            expenditure_date=expenditure_date
        )
        
        logger.info('Created expense object: %s', exp_obj.__dict__)
        db.session.add(exp_obj)
        db.session.commit()
        logger.info('Expense saved successfully with ID: %s', exp_obj.expense_id)
        
        return jsonify({
            'success': True, 
            'expense_id': exp_obj.expense_id,
            'message': 'Expense added successfully'
        }), 201
        
    except Exception as e:
        logger.error('Error in add_expense: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/expenses', methods=['DELETE'])
def delete_expense():
    logger.info('DELETE /api/expenses called')
    data = request.json
    logger.info('Request data: %s', data)
    
    expense_id_raw = data.get('expense_id')
    if expense_id_raw is None:
        logger.error('Missing expense_id')
        return jsonify({'error': 'Missing expense_id'}), 400
        
    try:
        expense_id = int(expense_id_raw)
        logger.info('Parsed expense_id: %d', expense_id)
    except (TypeError, ValueError):
        logger.error('Invalid expense_id format')
        return jsonify({'error': 'expense_id must be an integer'}), 400
        
    try:
        exp_obj = Expense.query.filter_by(expense_id=expense_id).first()
        if exp_obj:
            logger.info('Found expense to delete: %s', exp_obj.__dict__)
            db.session.delete(exp_obj)
            db.session.commit()
            logger.info('Expense deleted successfully')
            return jsonify({'success': True})
        else:
            logger.warning('Expense not found with id: %d', expense_id)
            return jsonify({'success': False, 'error': 'Expense not found'}), 404
    except Exception as e:
        logger.error('Error deleting expense: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/limit', methods=['OPTIONS'])
def handle_limit_options():
    logger.info('OPTIONS /api/limit called')
    return '', 200

@app.route('/api/limit', methods=['GET'])
def get_limit():
    logger.info('GET /api/limit called')
    year_raw = request.args.get('year')
    month_raw = request.args.get('month')
    logger.info('Query params - year: %s, month: %s', year_raw, month_raw)
    
    if year_raw is None or month_raw is None:
        logger.error('Missing year or month parameter')
        return jsonify({'error': 'Missing year or month parameter'}), 400
    
    try:
        calendar_year = int(year_raw)  # This is the calendar year like 2025
        month_id = int(month_raw)      # This is the database month_id
        logger.info('Parsed calendar year: %d, month_id: %d', calendar_year, month_id)
    except (TypeError, ValueError):
        logger.error('Invalid year or month format')
        return jsonify({'error': 'Year and month must be integers'}), 400
    
    try:
        # Find the year_id that corresponds to the calendar year
        year_obj = Year.query.filter_by(year_number=calendar_year).first()
        if not year_obj:
            logger.warning('Year %d not found in database', calendar_year)
            return jsonify({'monthly_limit': 0})
        
        year_id = year_obj.year_id
        logger.info('Found year_id: %d for calendar year: %d', year_id, calendar_year)
        
        # Now look for the monthly limit
        lim_obj = MonthlyLimit.query.filter_by(month_id=month_id, year_id=year_id).first()
        if lim_obj:
            monthly_limit_val = lim_obj.monthly_limit_amount
            logger.info('Found monthly limit: %s for month_id: %d, year_id: %d', monthly_limit_val, month_id, year_id)
            return jsonify({'monthly_limit': monthly_limit_val})
        else:
            logger.info('No monthly limit found for month_id: %d, year_id: %d', month_id, year_id)
            return jsonify({'monthly_limit': 0})
            
    except Exception as e:
        logger.error('Database error in get_limit: %s', str(e))
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/limit', methods=['POST'])
def set_limit():
    logger.info('POST /api/limit called')
    try:
        data = request.json
        logger.info('Request data: %s', data)
        
        year_raw = data.get('year')
        month_raw = data.get('month')
        limit_val_raw = data.get('limit')
        
        if year_raw is None or month_raw is None or limit_val_raw is None:
            logger.error('Missing required fields: year=%s, month=%s, limit=%s', year_raw, month_raw, limit_val_raw)
            return jsonify({'error': 'Missing year, month, or limit value'}), 400
        
        try:
            year_number = int(year_raw)
            month_number = int(month_raw)  # This is the month number (1-12)
            limit_val = float(limit_val_raw)
        except (TypeError, ValueError) as e:
            logger.error('Invalid data types: %s', e)
            return jsonify({'error': 'Year, month must be integers and limit must be a number'}), 400
        
        # Ensure year exists in year table
        year_obj = Year.query.filter_by(year_number=year_number).first()
        if not year_obj:
            logger.info('Creating new year: %s', year_number)
            year_obj = Year(year_number=year_number)
            db.session.add(year_obj)
            db.session.flush()  # Get the year_id without committing
        
        # Get the month_id (should be the same as month_number for months 1-12)
        month_id = month_number
        year_id = year_obj.year_id
        
        logger.info('Setting limit for user_id=1, month_id=%s, year_id=%s, limit=%s', 
                   month_id, year_id, limit_val)
        
        # Check if monthly limit already exists
        lim_obj = MonthlyLimit.query.filter_by(
            user_id=1, 
            month_id=month_id, 
            year_id=year_id
        ).first()
        
        if lim_obj:
            logger.info('Updating existing monthly limit')
            lim_obj.monthly_limit_amount = limit_val
        else:
            logger.info('Creating new monthly limit')
            lim_obj = MonthlyLimit(
                user_id=1, 
                month_id=month_id, 
                year_id=year_id, 
                monthly_limit_amount=limit_val
            )
            db.session.add(lim_obj)
        
        db.session.commit()
        logger.info('Monthly limit saved successfully')
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error('Error setting monthly limit: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/global_limit', methods=['GET'])
def get_global_limit():
    try:
        # For now, get global limit for user with ID 1 (since we don't have proper authentication yet)
        # In the future, this should use the authenticated user
        user = User.query.filter_by(user_id=1).first()
        if user:
            logger.info('Retrieved global limit for user %s: %s', user.user_id, user.global_limit)
            return jsonify({'global_limit': user.global_limit or 0})
        else:
            logger.warning('User with ID 1 not found, returning default global limit of 0')
            return jsonify({'global_limit': 0})
            
    except Exception as e:
        logger.error('Error getting global limit: %s', e)
        return jsonify({'global_limit': 0})

@app.route('/api/global_limit', methods=['POST'])
def set_global_limit():
    try:
        value = float(request.json['global_limit'])
        currency_id = request.json.get('currency_id')  # Optional currency_id
        logger.info('Setting global limit to: %s, currency_id: %s', value, currency_id)
        
        # For now, update user with ID 1 (since we don't have proper authentication yet)
        # In the future, this should use the authenticated user
        user = User.query.filter_by(user_id=1).first()
        if user:
            user.global_limit = value
            # Update currency if provided
            if currency_id is not None:
                user.currency_id = currency_id
                logger.info('Updated currency for user %s to %s', user.user_id, currency_id)
            db.session.commit()
            logger.info('Updated global limit for user %s to %s', user.user_id, value)
            return jsonify({'success': True})
        else:
            logger.error('User with ID 1 not found')
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error('Error setting global limit: %s', e)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Authentication endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    logger.info('POST /api/auth/signup called')
    try:
        data = request.json
        logger.info('Signup request data: %s', {k: v if k != 'password' else '***' for k, v in data.items()})
        
        name = data.get('name')  # We'll store the full name separately if needed
        email = data.get('email')
        password = data.get('password')
        
        if not name or not email or not password:
            logger.error('Missing required fields for signup')
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        # Check if user already exists by email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            logger.error('User with email %s already exists', email)
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Check if username (email) already exists
        existing_username = User.query.filter_by(username=email).first()
        if existing_username:
            logger.error('User with username %s already exists', email)
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Create new user - use email as username to ensure uniqueness
        user = User(username=email, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate a simple token (in production, use JWT)
        token = secrets.token_urlsafe(32)
        
        logger.info('User created successfully with ID: %s', user.user_id)
        return jsonify({
            'user': user.to_dict(),
            'token': token,
            'message': 'Account created successfully'
        }), 201
        
    except Exception as e:
        logger.error('Error in signup: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    logger.info('POST /api/auth/login called')
    try:
        data = request.json
        logger.info('Login request data: %s', {k: v if k != 'password' else '***' for k, v in data.items()})
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            logger.error('Missing email or password for login')
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            logger.error('User with email %s not found', email)
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check password
        if not user.check_password(password):
            logger.error('Invalid password for user %s', email)
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate a simple token (in production, use JWT)
        token = secrets.token_urlsafe(32)
        
        logger.info('User %s logged in successfully', email)
        return jsonify({
            'user': user.to_dict(),
            'token': token,
            'message': 'Login successful'
        }), 200
        
    except Exception as e:
        logger.error('Error in login: %s', e, exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/summary', methods=['GET'])
def get_expense_summary():
    """Get expense summary for different time periods"""
    try:
        logger.info('GET /api/summary called')
        
        # Get query parameters
        summary_type = request.args.get('type', 'monthly')  # monthly, yearly, custom
        year = request.args.get('year', 2025, type=int)
        month = request.args.get('month', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        user_id = 1  # For now, using user_id = 1
        
        logger.info('Summary request - type: %s, year: %s, month: %s, start_date: %s, end_date: %s', 
                   summary_type, year, month, start_date, end_date)
        
        if summary_type == 'monthly':
            if not month:
                return jsonify({'error': 'Month is required for monthly summary'}), 400
            
            # Get monthly expenses
            from sqlalchemy import extract
            expenses = Expense.query.filter(
                Expense.user_id == user_id,
                extract('year', Expense.expenditure_date) == year,
                extract('month', Expense.expenditure_date) == month
            ).all()
            
        elif summary_type == 'yearly':
            # Get yearly expenses
            from sqlalchemy import extract
            expenses = Expense.query.filter(
                Expense.user_id == user_id,
                extract('year', Expense.expenditure_date) == year
            ).all()
            
        elif summary_type == 'custom':
            if not start_date or not end_date:
                return jsonify({'error': 'Start date and end date are required for custom summary'}), 400
            
            # Get expenses between dates
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            expenses = Expense.query.filter(
                Expense.user_id == user_id,
                Expense.expenditure_date >= start_date_obj,
                Expense.expenditure_date <= end_date_obj
            ).all()
            
        else:
            return jsonify({'error': 'Invalid summary type'}), 400
        
        # Calculate summary data
        total_amount = sum(expense.expense_item_price for expense in expenses)
        total_count = len(expenses)
        
        # Category breakdown
        category_breakdown = {}
        for expense in expenses:
            # Get category name (you might need to join with category table)
            category_name = 'Uncategorized'  # Default
            try:
                category = ExpenseCategory.query.filter_by(
                    expense_category_id=expense.expense_category_id
                ).first()
                if category:
                    category_name = category.expense_category_name.title()
            except:
                pass
            
            if category_name not in category_breakdown:
                category_breakdown[category_name] = {'total': 0, 'count': 0}
            
            category_breakdown[category_name]['total'] += expense.expense_item_price
            category_breakdown[category_name]['count'] += 1
        
        # Monthly breakdown for yearly summary
        monthly_breakdown = {}
        if summary_type == 'yearly':
            for expense in expenses:
                month_name = expense.expenditure_date.strftime('%B')
                if month_name not in monthly_breakdown:
                    monthly_breakdown[month_name] = {'total': 0, 'count': 0}
                
                monthly_breakdown[month_name]['total'] += expense.expense_item_price
                monthly_breakdown[month_name]['count'] += 1
        
        # Prepare response
        summary_data = {
            'type': summary_type,
            'period': {
                'year': year,
                'month': month if summary_type == 'monthly' else None,
                'start_date': start_date if summary_type == 'custom' else None,
                'end_date': end_date if summary_type == 'custom' else None
            },
            'total_amount': total_amount,
            'total_count': total_count,
            'category_breakdown': category_breakdown,
            'monthly_breakdown': monthly_breakdown if summary_type == 'yearly' else None,
            'expenses': [
                {
                    'expense_id': expense.expense_id,
                    'amount': expense.expense_item_price,
                    'description': expense.expense_description,
                    'date': expense.expenditure_date.isoformat(),
                    'category_id': expense.expense_category_id
                } for expense in expenses
            ]
        }
        
        logger.info('Summary calculated - total: $%.2f, count: %d, categories: %d',
                   total_amount, total_count, len(category_breakdown))
        
        return jsonify({'summary': summary_data}), 200
        
    except Exception as e:
        logger.error('Error getting expense summary: %s', e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    """Get all available currencies"""
    try:
        logger.info('GET /api/currencies called')
        currencies = Currency.query.all()
        
        currency_list = []
        for currency in currencies:
            currency_list.append({
                'currency_id': currency.currency_id,
                'currency_name': currency.currency_name,
                'currency_symbol': currency.currency_symbol
            })
        
        logger.info('Retrieved %d currencies', len(currency_list))
        return jsonify({'currencies': currency_list}), 200
        
    except Exception as e:
        logger.error('Error getting currencies: %s', e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/currency', methods=['POST'])
def update_user_currency():
    """Update user's preferred currency"""
    try:
        logger.info('POST /api/user/currency called')
        data = request.get_json()
        currency_id = data.get('currency_id')
        
        if not currency_id:
            return jsonify({'error': 'Currency ID is required'}), 400
        
        # For now, update user with ID 1 (since we don't have proper authentication yet)
        user = User.query.filter_by(user_id=1).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify currency exists
        currency = Currency.query.filter_by(currency_id=currency_id).first()
        if not currency:
            return jsonify({'error': 'Invalid currency ID'}), 400
        
        user.currency_id = currency_id
        db.session.commit()
        
        logger.info('Updated user currency to %d', currency_id)
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error('Error updating user currency: %s', e)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/currency', methods=['GET'])
def get_user_currency():
    """Get user's current currency"""
    try:
        logger.info('GET /api/user/currency called')
        
        # For now, get user with ID 1 (since we don't have proper authentication yet)
        user = User.query.filter_by(user_id=1).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get currency details
        currency = Currency.query.filter_by(currency_id=user.currency_id).first()
        if not currency:
            # Default to USD if no currency found
            currency = Currency.query.filter_by(currency_id=1).first()
        
        result = {
            'currency_id': currency.currency_id if currency else 1,
            'currency_name': currency.currency_name if currency else 'US Dollar',
            'currency_symbol': currency.currency_symbol if currency else '$'
        }
        
        logger.info('Retrieved user currency: %s', result)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error('Error getting user currency: %s', e)
        return jsonify({'error': str(e)}), 500


# Add manual CORS headers for all requests
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=True)
