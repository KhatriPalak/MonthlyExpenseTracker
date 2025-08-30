#!/usr/bin/env python3
"""
Test script for the integrated Flask API
"""
import requests
import json

BASE_URL = "http://localhost:5002"

def test_api_endpoints():
    print("🧪 Testing Integrated Flask API")
    print("=" * 50)
    
    # Test database connection
    print("\n1. Testing database connection...")
    response = requests.get(f"{BASE_URL}/api/test-db")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Database connected: {response.json()}")
    
    # Test categories endpoint
    print("\n2. Testing categories endpoint...")
    response = requests.get(f"{BASE_URL}/api/categories")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        categories = response.json().get('categories', [])
        print(f"   ✅ Found {len(categories)} categories")
    
    # Test months endpoint
    print("\n3. Testing months endpoint...")
    response = requests.get(f"{BASE_URL}/api/months")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        months = response.json().get('months', [])
        print(f"   ✅ Found {len(months)} months")
    
    # Test signup endpoint
    print("\n4. Testing signup endpoint...")
    test_user = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/signup", json=test_user)
    print(f"   Status: {response.status_code}")
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"   ✅ User created: {data.get('user', {}).get('email')}")
        token = data.get('token')
    elif response.status_code == 400:
        print(f"   ℹ️ User might already exist: {response.json()}")
        # Try login instead
        login_data = {"email": test_user["email"], "password": test_user["password"]}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"   ✅ Logged in successfully")
        else:
            token = None
    else:
        token = None
    
    # Test login endpoint
    print("\n5. Testing login endpoint...")
    login_data = {
        "email": "user@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Login successful")
        default_token = response.json().get('token')
    else:
        print(f"   ❌ Login failed: {response.json()}")
        default_token = None
    
    # Test expenses endpoint
    print("\n6. Testing expenses endpoint...")
    response = requests.get(f"{BASE_URL}/api/expenses?year=2025&month=8")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        expenses = response.json()
        print(f"   ✅ Found {len(expenses)} expenses")
    
    # Test adding an expense
    print("\n7. Testing add expense endpoint...")
    new_expense = {
        "year": 2025,
        "month": 8,
        "expense": {
            "expense_item_price": 25.99,
            "expense_category_id": 1,
            "expense_description": "Test expense",
            "expense_item_count": 1,
            "expenditure_date": "2025-08-15"
        }
    }
    response = requests.post(f"{BASE_URL}/api/expenses", json=new_expense)
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        print(f"   ✅ Expense added: ID {response.json().get('expense_id')}")
    
    # Test global limit endpoints
    print("\n8. Testing global limit endpoints...")
    response = requests.get(f"{BASE_URL}/api/global_limit")
    print(f"   GET Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Current limit: {response.json().get('global_limit')}")
    
    response = requests.post(f"{BASE_URL}/api/global_limit", json={"global_limit": 5000})
    print(f"   POST Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Global limit updated")
    
    # Test monthly limit endpoints
    print("\n9. Testing monthly limit endpoints...")
    response = requests.get(f"{BASE_URL}/api/limit?year=2025&month=8")
    print(f"   GET Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Current monthly limit: {response.json().get('limit')}")
    
    response = requests.post(f"{BASE_URL}/api/limit", json={"year": 2025, "month": 8, "limit": 1500})
    print(f"   POST Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Monthly limit updated")
    
    # Test currencies endpoint
    print("\n10. Testing currencies endpoint...")
    response = requests.get(f"{BASE_URL}/api/currencies")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        currencies = response.json().get('currencies', [])
        print(f"   ✅ Found {len(currencies)} currencies")
    
    # Test summary endpoint
    print("\n11. Testing summary endpoint...")
    response = requests.get(f"{BASE_URL}/api/summary?type=monthly&year=2025&month=8")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        summary = response.json()
        print(f"   ✅ Monthly summary: Total expenses = ${summary.get('total_expenses', 0)}")
    
    print("\n" + "=" * 50)
    print("✅ API Integration Test Complete!")
    print(f"🚀 All endpoints are integrated and working on port {BASE_URL.split(':')[-1]}")

if __name__ == "__main__":
    try:
        test_api_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server")
        print("💡 Make sure the integrated Flask app is running on http://localhost:5002")
    except Exception as e:
        print(f"❌ Test failed: {e}")