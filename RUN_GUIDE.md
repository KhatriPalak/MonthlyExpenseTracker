# Monthly Expense Tracker - Complete Setup & Testing Guide

## 📋 Prerequisites

Before running the application, ensure you have:
- ✅ Python 3.8+ installed
- ✅ Node.js 14+ and npm installed
- ✅ PostgreSQL installed and running
- ✅ Git installed

## 🚀 Quick Start (5 Minutes)

### Step 1: Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Install Python dependencies
pip3 install -r requirements.txt
pip3 install python-dotenv flask-sqlalchemy passlib requests

# 3. Check your PostgreSQL is running
psql --version

# 4. Verify .env file has correct database credentials
cat .env
# Should show:
# DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/expense_db
# Update password if needed

# 5. Create database if not exists (one-time setup)
PGPASSWORD=yourpassword psql -U postgres -h localhost -c "CREATE DATABASE expense_db;"

# 6. Initialize database tables (one-time setup)
python3 create_tables.py

# 7. Start the integrated backend server
cd app
python3 app_integrated.py
```

✅ Backend should now be running on http://localhost:5002

### Step 2: Frontend Setup

Open a **new terminal window**:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (one-time)
npm install

# 3. Update backend URL in frontend files
# You need to change the hardcoded IP to localhost:5002
# Run this command to see all files that need updating:
grep -r "3.141.164.136:5000" src/

# 4. Start the frontend development server
npm start
```

✅ Frontend should open automatically at http://localhost:3000

## 🔧 Manual Frontend URL Update

The frontend currently has hardcoded URLs. Update these files:

### 1. **src/App.js**
Replace all occurrences of:
```javascript
'http://3.141.164.136:5000'
```
With:
```javascript
'http://localhost:5002'
```

### 2. **src/Login.js**
```javascript
// Line 32: Change
fetch('http://3.141.164.136:5000/api/auth/login', {
// To:
fetch('http://localhost:5002/api/auth/login', {
```

### 3. **src/Signup.js**
```javascript
// Line 52: Change
fetch('http://3.141.164.136:5000/api/auth/signup', {
// To:
fetch('http://localhost:5002/api/auth/signup', {
```

### 4. **src/ExpenseTracker.js**
```javascript
// Line 11: Change
fetch(`http://3.141.164.136:5000/api/expenses?year=${year}&month=${month}`)
// To:
fetch(`http://localhost:5002/api/expenses?year=${year}&month=${month}`)
```

## 🧪 Testing the Application

### A. Test Backend APIs

```bash
cd backend
python3 test_integrated_api.py
```

Expected output:
```
✅ Database connected
✅ Found 9 categories
✅ Found 12 months
✅ User created/logged in
✅ Expenses working
✅ Limits working
✅ Currencies working
```

### B. Test via Command Line (curl)

```bash
# 1. Test database connection
curl http://localhost:5002/api/test-db

# 2. Get categories
curl http://localhost:5002/api/categories

# 3. Create a new user
curl -X POST http://localhost:5002/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"secure123"}'

# 4. Login
curl -X POST http://localhost:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secure123"}'

# 5. Add an expense
curl -X POST http://localhost:5002/api/expenses \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2025,
    "month": 8,
    "expense": {
      "expense_item_price": 45.99,
      "expense_category_id": 1,
      "expense_description": "Grocery shopping",
      "expense_item_count": 1,
      "expenditure_date": "2025-08-29"
    }
  }'

# 6. Get expenses for August 2025
curl "http://localhost:5002/api/expenses?year=2025&month=8"
```

### C. Test in Browser

1. Open http://localhost:3000
2. Click "Sign Up" to create a new account
3. Enter your details and register
4. You'll be logged in automatically
5. Try adding expenses:
   - Select a month
   - Click "Add Expense"
   - Fill in the details
   - Submit
6. Set budget limits:
   - Set a global limit
   - Set monthly limits
7. View summaries and reports

## 📱 Full Application Test Checklist

### Authentication
- [ ] Sign up with new email
- [ ] Login with existing account
- [ ] Logout functionality
- [ ] Session persistence

### Expense Management
- [ ] Add new expense
- [ ] View expenses by month
- [ ] Edit expense
- [ ] Delete expense
- [ ] Filter by category

### Budget Management
- [ ] Set global spending limit
- [ ] Set monthly limits
- [ ] View limit warnings
- [ ] Clear limits

### Categories
- [ ] View default categories
- [ ] Add custom category
- [ ] Delete custom category
- [ ] Use categories in expenses

### Currency
- [ ] View available currencies
- [ ] Change default currency
- [ ] Currency symbol updates

### Reports
- [ ] Monthly summary
- [ ] Yearly summary
- [ ] Category breakdown
- [ ] Export to PDF

## 🐛 Troubleshooting

### Backend Issues

**Problem: "Port 5002 already in use"**
```bash
# Find and kill the process
lsof -i :5002
kill -9 <PID>
```

**Problem: "Database connection failed"**
```bash
# Check PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Restart PostgreSQL
brew services restart postgresql      # macOS
sudo systemctl restart postgresql     # Linux
```

**Problem: "Module not found"**
```bash
# Install missing module
pip3 install <module_name>
```

### Frontend Issues

**Problem: "Cannot connect to backend"**
- Check backend is running on port 5002
- Verify URLs are updated in frontend files
- Check CORS settings in backend

**Problem: "npm start fails"**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm start
```

## 🚢 Production Deployment

### Backend Production Setup

1. Create production .env:
```bash
DATABASE_URL=postgresql://user:pass@your-rds-instance:5432/expense_db
SECRET_KEY=your-production-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
HOST=0.0.0.0
```

2. Use production server:
```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app.app_integrated:app
```

### Frontend Production Build

```bash
cd frontend

# Update API URLs to production backend
# Edit src files to use your production URL

# Build for production
npm run build

# Serve with a web server
npx serve -s build -l 3000
```

## 📊 Database Management

### View Database Content
```bash
# Connect to PostgreSQL
PGPASSWORD=yourpassword psql -U postgres -d expense_db

# Useful queries
\dt                          -- List all tables
SELECT * FROM "user";        -- View users
SELECT * FROM expense;       -- View expenses
SELECT * FROM expense_category; -- View categories
\q                          -- Exit
```

### Reset Database
```bash
# Drop and recreate database
PGPASSWORD=yourpassword psql -U postgres -c "DROP DATABASE expense_db;"
PGPASSWORD=yourpassword psql -U postgres -c "CREATE DATABASE expense_db;"
python3 backend/create_tables.py
```

## 🔐 Default Test Accounts

| Email | Password | Role |
|-------|----------|------|
| user@example.com | password123 | Default User |
| test@example.com | testpass123 | Test User |

## 📝 API Documentation

Full API documentation available at:
- Backend API endpoints: See `backend/app/app_integrated.py`
- Frontend integration: See `frontend/src/App.js`

## 💡 Tips for Testing

1. **Use Browser DevTools**: Press F12 to see network requests and console logs
2. **Check Backend Logs**: Terminal running Flask shows all API calls
3. **Use Postman**: Import the API endpoints for easier testing
4. **Database GUI**: Use pgAdmin or TablePlus to view database directly

## 🎯 Quick Test Scenario

1. Start backend: `python3 backend/app/app_integrated.py`
2. Start frontend: `npm start` (in frontend directory)
3. Sign up with email: `tester@test.com`, password: `test123`
4. Add 3 expenses in different categories
5. Set a monthly limit of $1000
6. Add more expenses to exceed the limit
7. Check the summary page
8. Try deleting an expense
9. Logout and login again
10. Verify data persists

## 📞 Support

If you encounter issues:
1. Check the terminal logs for both frontend and backend
2. Verify all dependencies are installed
3. Ensure PostgreSQL is running
4. Check network tab in browser DevTools
5. Review the analysis.md file for known issues

---
*Last Updated: August 30, 2025*