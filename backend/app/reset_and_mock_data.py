import bcrypt
from db import SessionLocal
from models import User, ExpenseCategory, Month, Year, MonthlyLimit, Expense
from datetime import date

# Delete all records from tables
session = SessionLocal()
session.query(Expense).delete()
session.query(MonthlyLimit).delete()
session.query(Year).delete()
session.query(Month).delete()
session.query(ExpenseCategory).delete()
session.query(User).delete()
session.commit()

# Add mock users with hashed passwords
def hash_pwd(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

user1 = User(username='alice', password=hash_pwd('password123'), email='alice@example.com', global_limit=5000)
user2 = User(username='bob', password=hash_pwd('securepass'), email='bob@example.com', global_limit=3000)
session.add_all([user1, user2])
session.commit()

# Add expense categories
cat1 = ExpenseCategory(expense_category_name='Groceries')
cat2 = ExpenseCategory(expense_category_name='Utilities')
cat3 = ExpenseCategory(expense_category_name='Entertainment')
session.add_all([cat1, cat2, cat3])
session.commit()

# Add months
months = [Month(month_name=m) for m in ['January','February','March','April','May','June','July','August','September','October','November','December']]
session.add_all(months)
session.commit()

# Add years
years = [Year(year_number=y) for y in range(2020, 2026)]
session.add_all(years)
session.commit()

# Add monthly limits
ml1 = MonthlyLimit(user_id=user1.user_id, monthly_limit_amount=400, month_id=months[6].month_id, year_id=years[-1].year_id)
ml2 = MonthlyLimit(user_id=user2.user_id, monthly_limit_amount=350, month_id=months[6].month_id, year_id=years[-1].year_id)
session.add_all([ml1, ml2])
session.commit()

# Add expenses
exp1 = Expense(user_id=user1.user_id, expense_item_price=50.0, expense_category_id=cat1.expense_category_id, expense_description='Weekly groceries', expense_item_count=1, expenditure_date=date(2025,7,5))
exp2 = Expense(user_id=user1.user_id, expense_item_price=120.0, expense_category_id=cat2.expense_category_id, expense_description='Electricity bill', expense_item_count=1, expenditure_date=date(2025,7,10))
exp3 = Expense(user_id=user2.user_id, expense_item_price=60.0, expense_category_id=cat3.expense_category_id, expense_description='Movie night', expense_item_count=2, expenditure_date=date(2025,7,15))
session.add_all([exp1, exp2, exp3])
session.commit()
session.close()
print('Database reset and mock data inserted.')
