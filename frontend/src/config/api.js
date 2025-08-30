// API Configuration
// This file centralizes all API endpoint configurations

// Get base URL from environment variable or use default
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5002';

// API Endpoints
const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/api/auth/login`,
  SIGNUP: `${API_BASE_URL}/api/auth/signup`,
  LOGOUT: `${API_BASE_URL}/api/auth/logout`,
  
  // Expenses
  EXPENSES: `${API_BASE_URL}/api/expenses`,
  
  // Categories
  CATEGORIES: `${API_BASE_URL}/api/categories`,
  
  // Limits
  GLOBAL_LIMIT: `${API_BASE_URL}/api/global_limit`,
  MONTHLY_LIMIT: `${API_BASE_URL}/api/limit`,
  
  // Currencies
  CURRENCIES: `${API_BASE_URL}/api/currencies`,
  USER_CURRENCY: `${API_BASE_URL}/api/user/currency`,
  
  // Months
  MONTHS: `${API_BASE_URL}/api/months`,
  
  // Summary
  SUMMARY: `${API_BASE_URL}/api/summary`,
  
  // Database Test
  TEST_DB: `${API_BASE_URL}/api/test-db`,
};

// Helper function to build URL with query parameters
export const buildUrl = (endpoint, params) => {
  const url = new URL(endpoint);
  Object.keys(params || {}).forEach(key => 
    url.searchParams.append(key, params[key])
  );
  return url.toString();
};

// Export configuration
export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  ENDPOINTS: API_ENDPOINTS,
  TIMEOUT: 30000, // 30 seconds
  HEADERS: {
    'Content-Type': 'application/json',
  },
};

// Debug logging
if (process.env.REACT_APP_DEBUG === 'true') {
  console.log('🔧 API Configuration:', {
    BASE_URL: API_BASE_URL,
    ENV: process.env.REACT_APP_ENV || 'development'
  });
}

export default API_CONFIG;