# Monthly Expense Tracker - Application Flow Documentation

## 🏗️ Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                      │
│                     http://localhost:3003                     │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │   Login/    │  │    Main     │  │     Expense      │    │
│  │   Signup    │──▶│  Dashboard  │──▶│   Management    │    │
│  └─────────────┘  └─────────────┘  └──────────────────┘    │
│                           │                                   │
│                    Uses .env file for                        │
│                    API configuration                         │
└───────────────────────────┬───────────────────────────────────┘
                           │
                    API Calls (HTTP)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Flask/Python)                     │
│                     http://localhost:5002                     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │     Auth     │  │   Expense    │  │     Budget      │   │
│  │   Endpoints  │  │   Endpoints  │  │    Endpoints    │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
│                           │                                   │
│                    SQLAlchemy ORM                            │
└───────────────────────────┬───────────────────────────────────┘
                           │
                        Database
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                        │
│                                                               │
│  Tables: user, expense, expense_category, monthly_limit,     │
│          month, year, currency                               │
└───────────────────────────────────────────────────────────────┘
```

## 📱 User Flow

### 1. **Authentication Flow**
```
User Opens App → Check localStorage for token
                ↓
         Token exists? 
         ↙          ↘
      Yes            No
        ↓             ↓
   Load Dashboard   Show Login
                      ↓
                 User logs in or
                 signs up
                      ↓
                 Store token & user
                      ↓
                 Load Dashboard
```

### 2. **Main Dashboard Flow**
```
Dashboard Loads → Parallel API Calls:
                  ├── Fetch Months
                  ├── Fetch Categories  
                  ├── Fetch Global Limit
                  ├── Fetch Monthly Limits (all months)
                  └── Fetch Expenses (all months)
                        ↓
                  Display Month Cards
                  with expense data
```

### 3. **Add Expense Flow**
```
User clicks "Add Expense" → Show expense form
                           ↓
                     User fills form:
                     - Name (description)
                     - Amount
                     - Date
                     - Category (dropdown)
                           ↓
                     Submit button clicked
                           ↓
                     Frontend validation
                           ↓
                     POST /api/expenses
                           ↓
                     Backend saves to DB
                           ↓
                     Refresh month's expenses
                           ↓
                     Update UI immediately
```

### 4. **Budget Management Flow**
```
Set Global Limit → POST /api/global_limit
                   ↓
                   Applies to all months
                   without specific limits

Set Monthly Limit → POST /api/limit
                    ↓
                    Overrides global limit
                    for that specific month
```

## 🔄 Data Flow

### Frontend State Management
```javascript
// Main state variables in App.js
{
  user: {},              // Current logged-in user
  year: 2025,           // Selected year
  months: [],           // List of months
  categories: [],       // Expense categories
  expenses: {           // Expenses by month
    "2025-1": [...],    // Key format: "year-month"
    "2025-2": [...],
  },
  monthLimits: {        // Monthly budget limits
    1: 1000,            // Month ID: Amount
    2: 1500,
  },
  globalLimit: 5000,    // Default limit for all months
}
```

### API Endpoints

#### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - User login

#### Expenses
- `GET /api/expenses?year=X&month=Y` - Get expenses for specific month
- `POST /api/expenses` - Add new expense
- `DELETE /api/expenses` - Delete an expense

#### Categories
- `GET /api/categories` - Get all categories
- `POST /api/categories` - Add new category
- `DELETE /api/categories` - Delete a category

#### Budget Limits
- `GET /api/global_limit` - Get global spending limit
- `POST /api/global_limit` - Set global spending limit
- `GET /api/limit?year=X&month=Y` - Get monthly limit
- `POST /api/limit` - Set monthly limit

#### Other
- `GET /api/months` - Get list of months
- `GET /api/currencies` - Get available currencies
- `POST /api/user/currency` - Update user's currency

## 🗄️ Database Schema

```sql
-- Core Tables
user (user_id, username, email, password, global_limit, currency_id)
expense (expense_id, user_id, amount, category_id, description, date)
expense_category (category_id, name, user_id, is_deleted)

-- Reference Tables
month (month_id, month_name)
year (year_id, year_number)
currency (currency_id, name, symbol)

-- Relationship Tables
monthly_limit (limit_id, user_id, month_id, year_id, amount)
```

## 🔑 Key Features

### 1. **Expense Management**
- Add, view, and delete expenses
- Categorize expenses
- Track by month and year
- Add descriptions and dates

### 2. **Budget Tracking**
- Set global spending limits
- Override with monthly limits
- Visual indicators for overspending
- Real-time budget calculations

### 3. **Category System**
- Default global categories
- User-specific custom categories
- Soft delete for data integrity
- Category suggestions while typing

### 4. **Multi-Currency Support**
- Multiple currency options
- User-specific currency preference
- Currency symbols in UI

### 5. **Data Caching**
- LocalStorage for quick loading
- Background data refresh
- Cache invalidation on updates

## 🚀 Performance Optimizations

1. **Parallel Data Loading**
   - All API calls made simultaneously on load
   - No waterfall loading

2. **Smart Caching**
   - Cache recent data in localStorage
   - Show cached data immediately
   - Refresh in background

3. **Optimistic UI Updates**
   - Update UI before server confirms
   - Rollback on error

4. **Lazy Loading**
   - Load only visible month data first
   - Load other months as needed

## 🛠️ Development Setup

### Environment Variables
```bash
# Frontend (.env)
REACT_APP_API_URL=http://localhost:5002
REACT_APP_ENV=development
REACT_APP_DEBUG=true

# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/expense_db
SECRET_KEY=your-secret-key
FLASK_ENV=development
```

### Commands
```bash
# Backend
cd backend/app
python3 app_integrated.py

# Frontend  
cd frontend
npm start

# Database
python3 backend/create_tables.py  # Initialize database
```

## 📊 Data Flow Example: Adding an Expense

1. **User Action**: Fills form and clicks "Save Expense"

2. **Frontend Processing**:
   ```javascript
   // Collect form data
   const expense = {
     name: "Grocery Shopping",
     amount: 45.99,
     date: "2025-08-30",
     category_id: 1,
     description: "Weekly groceries"
   }
   
   // Send to backend
   POST /api/expenses
   Body: { year: 2025, month: 8, expense: {...} }
   ```

3. **Backend Processing**:
   ```python
   # Validate data
   # Get user_id from session/token
   # Create expense record
   new_expense = Expense(
     user_id=1,
     expense_item_price=45.99,
     expense_category_id=1,
     expenditure_date="2025-08-30"
   )
   db.session.add(new_expense)
   db.session.commit()
   ```

4. **Database Update**:
   ```sql
   INSERT INTO expense (user_id, expense_item_price, ...) 
   VALUES (1, 45.99, ...);
   ```

5. **Frontend Update**:
   ```javascript
   // Refresh expenses for the month
   const updatedExpenses = await fetch('/api/expenses?year=2025&month=8')
   setExpenses({...expenses, "2025-8": updatedExpenses})
   // UI automatically re-renders with new expense
   ```

## 🔒 Security Measures

1. **Authentication**: JWT tokens for session management
2. **Password Security**: Bcrypt hashing
3. **CORS**: Configured for specific origins
4. **Input Validation**: Both frontend and backend
5. **SQL Injection Prevention**: Using SQLAlchemy ORM
6. **Environment Variables**: Sensitive data not in code

## 📈 Future Enhancements

- [ ] Data visualization/charts
- [ ] Export to PDF/CSV
- [ ] Recurring expenses
- [ ] Budget alerts/notifications
- [ ] Mobile app version
- [ ] Multi-user households
- [ ] Receipt photo uploads
- [ ] Expense analytics/insights
- [ ] Bill reminders
- [ ] Savings goals tracking

---

*Last Updated: August 2025*
*Application Version: 1.0*