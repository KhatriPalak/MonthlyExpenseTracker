
import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './Login';
import Signup from './Signup';

function App() {
  // Authentication state
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'

  // Expense tracker state (moved to top to avoid conditional hooks)
  const [year, setYear] = useState(2025);
  const [globalLimit, setGlobalLimit] = useState(0);
  const [tempGlobalLimit, setTempGlobalLimit] = useState(0);
  const [monthLimits, setMonthLimits] = useState({});
  const [tempMonthLimits, setTempMonthLimits] = useState({});
  const [expenses, setExpenses] = useState({});
  const [showExpenseForm, setShowExpenseForm] = useState({});
  const [expenseFormData, setExpenseFormData] = useState({});
  const [globalLimitSuccess, setGlobalLimitSuccess] = useState('');
  const [monthLimitSuccess, setMonthLimitSuccess] = useState({});
  const [dataLoaded, setDataLoaded] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [categoryInput, setCategoryInput] = useState({});
  const [showCategorySuggestions, setShowCategorySuggestions] = useState({});
  const [filteredCategories, setFilteredCategories] = useState({});
  
  // Modal and temporary category states
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [currentMonthId, setCurrentMonthId] = useState(null);
  const [tempCategories, setTempCategories] = useState([]); // Categories created during session but not saved yet
  
  // Delete confirmation modal states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [categoryToDelete, setCategoryToDelete] = useState(null);
  // Initialize months immediately with default data for instant display
  const [months, setMonths] = useState([
    { month_id: 13, month_name: "January" },
    { month_id: 14, month_name: "February" },
    { month_id: 15, month_name: "March" },
    { month_id: 16, month_name: "April" },
    { month_id: 17, month_name: "May" },
    { month_id: 18, month_name: "June" },
    { month_id: 19, month_name: "July" },
    { month_id: 20, month_name: "August" },
    { month_id: 21, month_name: "September" },
    { month_id: 22, month_name: "October" },
    { month_id: 23, month_name: "November" },
    { month_id: 24, month_name: "December" }
  ]);

  // Check for existing authentication on app load and initialize cached data
  useEffect(() => {
    console.log('App: Checking for existing authentication and loading cached data');
    const savedUser = localStorage.getItem('user');
    const savedToken = localStorage.getItem('token');
    
    if (savedUser && savedToken) {
      try {
        const userData = JSON.parse(savedUser);
        console.log('App: Found saved user data:', userData);
        setUser(userData);
        
        // Always fetch fresh data from database - don't rely on cache for critical data
        console.log('App: User authenticated - will always fetch fresh data from PostgreSQL');
      } catch (error) {
        console.error('App: Error parsing saved user data:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
    setIsLoading(false);
  }, [year]);

  // Fetch months from database in background (non-blocking)
  useEffect(() => {
    console.log('App: Background fetching months from database');
    
    // Check for cached months (optional update)
    const cachedMonths = localStorage.getItem('cached_months');
    const cacheTimestamp = localStorage.getItem('cached_months_timestamp');
    const now = Date.now();
    
    if (cachedMonths && cacheTimestamp && (now - parseInt(cacheTimestamp)) < 300000) { // 5 minute cache
      try {
        const cachedMonthsData = JSON.parse(cachedMonths);
        console.log('App: Updating with cached months data');
        setMonths(cachedMonthsData);
        return;
      } catch (error) {
        console.log('App: Invalid cached months, continuing with default');
      }
    }
    
    // Fetch fresh months data in background (non-blocking)
    fetch('http://localhost:5000/api/months', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(2000)
    })
      .then(res => res.json())
      .then(data => {
        console.log('App: Background months data received:', data);
        if (data.months) {
          setMonths(data.months);
          // Cache months data for future use
          localStorage.setItem('cached_months', JSON.stringify(data.months));
          localStorage.setItem('cached_months_timestamp', now.toString());
        }
      })
      .catch(error => {
        console.log('App: Background months fetch failed, using defaults:', error);
        // Keep default months, just cache them
        localStorage.setItem('cached_months', JSON.stringify(months));
        localStorage.setItem('cached_months_timestamp', now.toString());
      });
  }, [months]);

  // Immediate data fetching - load all data synchronously on user/year change
  useEffect(() => {
    if (!user) return;
    
    const fetchAllDataImmediately = async () => {
      console.log('⚡ App: Loading ALL data immediately for user:', user.id, 'year:', year);
      setDataLoading(true);
      setDataLoaded(false);
      
      // Force clear all cache before fetching - no cached data issues
      const cacheKey = `expense_data_${user.id}_${year}`;
      localStorage.removeItem(cacheKey);
      console.log('🧹 App: Cleared all cached data to force fresh load from database');
      
      try {
        // Create all API calls to run in parallel for fastest loading
        console.log('🚀 Starting parallel fetch of all data from PostgreSQL...');
        
        const globalLimitPromise = fetch('http://localhost:5000/api/global_limit', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(8000)
        });
        
        // Create all monthly limit fetch promises
        const monthLimitPromises = months.map(monthObj => 
          fetch(`http://localhost:5000/api/limit?year=${year}&month=${monthObj.month_id}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(8000)
          }).then(response => ({ monthId: monthObj.month_id, response }))
        );
        
        // Create all expense fetch promises
        const expensePromises = months.map(monthObj => {
          const calendarMonth = monthObj.month_id - 12; // Convert database month_id (13-24) to calendar month (1-12)
          return fetch(`http://localhost:5000/api/expenses?year=${year}&month=${calendarMonth}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(8000)
          }).then(response => ({ monthId: monthObj.month_id, response }))
        });
        
        // Fetch categories
        const categoriesPromise = fetch('http://localhost:5000/api/categories', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(8000)
        });
        
        // Execute all requests in parallel
        console.log('⚡ Executing all API calls in parallel...');
        const [globalLimitResponse, categoriesResponse, ...monthLimitResponses] = await Promise.allSettled([
          globalLimitPromise,
          categoriesPromise,
          ...monthLimitPromises
        ]);
        
        // Process and show critical data (limits) immediately
        let globalLimitValue = 0;
        if (globalLimitResponse.status === 'fulfilled') {
          try {
            const globalData = await globalLimitResponse.value.json();
            globalLimitValue = globalData.global_limit || 0;
            console.log('✅ Global limit loaded immediately:', globalLimitValue);
            setGlobalLimit(globalLimitValue); // Show immediately
            setTempGlobalLimit(globalLimitValue);
          } catch (error) {
            console.log('❌ Global limit parse error:', error);
          }
        }
        
        // Process monthly limits immediately
        const limitData = {};
        const tempLimitData = {};
        for (const result of monthLimitResponses) {
          if (result.status === 'fulfilled' && result.value) {
            try {
              const { monthId, response } = result.value;
              const monthData = await response.json();
              if (monthData.monthly_limit && monthData.monthly_limit > 0) {
                limitData[monthId] = monthData.monthly_limit;
                tempLimitData[monthId] = monthData.monthly_limit;
                console.log(`✅ Monthly limit loaded immediately for month ${monthId}: $${monthData.monthly_limit}`);
              }
            } catch (error) {
              console.log('❌ Monthly limit parse error:', error);
            }
          }
        }
        
        // Apply limits immediately for faster perceived loading
        setMonthLimits(limitData);
        setTempMonthLimits(tempLimitData);
        console.log('🚀 Critical limit data applied immediately');
        
        // Load categories immediately
        if (categoriesResponse.status === 'fulfilled') {
          try {
            const categoriesData = await categoriesResponse.value.json();
            setCategories(categoriesData.categories || []);
            console.log('✅ Categories loaded:', categoriesData.categories);
          } catch (error) {
            console.log('❌ Categories parse error:', error);
          }
        }
        
        // Now fetch expenses (less critical, can show loading state longer)
        const expenseResponses = await Promise.allSettled(expensePromises);
        
        // Process expenses (limits already processed above)
        const expenseData = {};
        for (const result of expenseResponses) {
          if (result.status === 'fulfilled' && result.value) {
            try {
              const { monthId, response } = result.value;
              const expenseList = await response.json();
              expenseData[`${year}-${monthId}`] = Array.isArray(expenseList) ? expenseList : [];
              console.log(`✅ Expenses loaded for month ${monthId}: ${expenseData[`${year}-${monthId}`].length} items`);
            } catch (error) {
              console.log('❌ Expenses parse error:', error);
              // Get monthId from result.value if available
              const monthId = result.value?.monthId;
              if (monthId) {
                expenseData[`${year}-${monthId}`] = [];
              }
            }
          } else {
            // Set empty array for failed requests
            const monthId = result.value?.monthId;
            if (monthId) {
              expenseData[`${year}-${monthId}`] = [];
            }
          }
        }
        
        // Apply final expense data to state (limits already applied above)
        console.log('🚀 Applying final expense data to UI state...');
        console.log('📊 Setting expenses for months:', Object.keys(expenseData));
        
        // Only set expenses (limits already set above for faster loading)
        setExpenses(expenseData);
        
        // Mark data as loaded
        setDataLoaded(true);
        setDataLoading(false);
        
        // Cache the data for performance
        const cacheKey = `expense_data_${user.id}_${year}`;
        const dataToCache = {
          globalLimit: globalLimitValue,
          monthLimits: limitData,
          expenses: expenseData
        };
        localStorage.setItem(cacheKey, JSON.stringify(dataToCache));
        localStorage.setItem(`${cacheKey}_timestamp`, Date.now().toString());
        
        console.log('✅ ALL data loaded and applied immediately to UI');
        
      } catch (error) {
        console.error('❌ Error in immediate data fetch:', error);
        // Set safe defaults on error
        setGlobalLimit(0);
        setTempGlobalLimit(0);
        setMonthLimits({});
        setTempMonthLimits({});
        setExpenses({});
        setDataLoaded(true); // Mark as loaded even on error to stop showing loading state
        setDataLoading(false);
      }
    };
    
    // Run immediate data fetch
    fetchAllDataImmediately();
  }, [user, year]); // Only depend on user and year changes

  // Function to refresh expenses for a specific month
  const refreshExpensesForMonth = async (monthId) => {
    try {
      console.log(`App: Refreshing expenses for month ${monthId}`);
      console.log(`App: Current year: ${year}`);
      console.log(`App: Expense key will be: ${year}-${monthId}`);
      const calendarMonth = monthId - 12; // Convert database month_id (13-24) to calendar month (1-12)
      const res = await fetch(`http://localhost:5000/api/expenses?year=${year}&month=${calendarMonth}`);
      const data = await res.json();
      console.log(`App: Refreshed expenses for month ${monthId}:`, data);
      console.log(`App: Setting expenses with key: ${year}-${monthId}`);
      setExpenses(exp => {
        const newExpenses = { ...exp, [`${year}-${monthId}`]: data };
        console.log(`App: Updated expenses state:`, newExpenses);
        return newExpenses;
      });
    } catch (error) {
      console.error(`App: Error refreshing expenses for month ${monthId}:`, error);
    }
  };

  // Authentication handlers
  // Authentication handlers
  const handleLogin = (userData) => {
    console.log('App: User logged in:', userData);
    
    // Clear all cached data for fresh PostgreSQL fetch
    const cacheKey = `expense_data_${userData.id}_${year}`;
    localStorage.removeItem(cacheKey);
    localStorage.removeItem(`${cacheKey}_timestamp`);
    console.log('App: Cleared cache for fresh data fetch from PostgreSQL');
    
    // Clear session markers to force fresh data load
    sessionStorage.removeItem('hasLoadedData');
    console.log('App: Cleared session markers for fresh PostgreSQL data load');
    
    setUser(userData);
  };

  const handleSignup = (userData) => {
    console.log('App: User signed up:', userData);
    
    // Clear any existing cached data
    const cacheKey = `expense_data_${userData.id}_${year}`;
    localStorage.removeItem(cacheKey);
    localStorage.removeItem(`${cacheKey}_timestamp`);
    console.log('App: Cleared cache for new user');
    
    // Clear session markers to force fresh data load
    sessionStorage.removeItem('hasLoadedData');
    console.log('App: Cleared session markers for fresh PostgreSQL data load');
    
    setUser(userData);
  };

  const handleLogout = () => {
    console.log('App: User logging out');
    
    // Clear session markers and cached data
    sessionStorage.clear();
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    
    // Clear all cached expense data
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('expense_data_') || key.startsWith('session_')) {
        localStorage.removeItem(key);
      }
    });
    
    setUser(null);
  };

  // Helper function to invalidate cached data
  const invalidateCache = () => {
    const cacheKey = `expense_data_${user?.id}_${year}`;
    localStorage.removeItem(cacheKey);
    localStorage.removeItem(`${cacheKey}_timestamp`);
    console.log('App: Cache invalidated');
  };

  // Force refresh all data from backend
  const forceRefreshData = async () => {
    console.log('🔄 Force refreshing all data...');
    
    // Clear all relevant cache
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('expense_data_') || key.startsWith('cached_months')) {
        localStorage.removeItem(key);
      }
    });
    
    // Reload the page to force a complete refresh
    window.location.reload();
  };

  // Delete expense from backend
  const handleDeleteExpense = async (monthIdx, expenseId) => {
    if (!expenseId) return;
    try {
      console.log(`App: Deleting expense ${expenseId} from month ${monthIdx}`);
      const response = await fetch('http://localhost:5000/api/expenses', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expense_id: expenseId })
      });
      
      if (response.ok) {
        console.log(`App: Expense ${expenseId} deleted successfully`);
        // Invalidate cache to ensure fresh data
        invalidateCache();
        // Refresh expenses for this month
        await refreshExpensesForMonth(monthIdx);
      } else {
        console.error('App: Failed to delete expense:', response.status);
      }
    } catch (error) {
      console.error('App: Error deleting expense:', error);
    }
  };

  // Handle expense form input changes
  const handleExpenseInputChange = (monthIdx, field, value) => {
    setExpenseFormData(form => ({
      ...form,
      [monthIdx]: {
        ...form[monthIdx],
        [field]: value
      }
    }));
  };

  // Submit new expense to backend
  const handleExpenseSubmit = async (monthIdx) => {
    console.log('handleExpenseSubmit: Starting with monthIdx:', monthIdx);
    console.log('handleExpenseSubmit: Current year:', year);
    console.log('handleExpenseSubmit: Current expenseFormData:', expenseFormData);
    
    const form = expenseFormData[monthIdx] || {};
    console.log('handleExpenseSubmit: Form data:', form);
    
    if (!form.name || !form.amount || !form.date || !form.category) {
      console.error('handleExpenseSubmit: Missing required fields:', { name: form.name, amount: form.amount, date: form.date, category: form.category });
      alert('Please fill in all required fields (including category)');
      return;
    }
    
    let categoryId = Number(form.category);
    
    // Check if this is a temporary category that needs to be created in the database
    if (categoryId < 0) { // Negative IDs indicate temp categories
      const tempCategory = tempCategories.find(cat => cat.category_id === categoryId);
      if (tempCategory) {
        try {
          console.log('Creating new category in database:', tempCategory.category_name);
          
          // Create the category in the database first
          const categoryResponse = await fetch('http://localhost:5000/api/categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_name: tempCategory.category_name })
          });
          
          if (!categoryResponse.ok) {
            const error = await categoryResponse.json();
            throw new Error(error.error || 'Failed to create category');
          }
          
          const categoryResult = await categoryResponse.json();
          categoryId = categoryResult.category.category_id;
          
          // Update the categories list with the real category
          setCategories(prev => [...prev, categoryResult.category]);
          
          // Remove from temp categories
          setTempCategories(prev => prev.filter(cat => cat.category_id !== tempCategory.category_id));
          
          console.log('Category created successfully with ID:', categoryId);
          
        } catch (error) {
          console.error('Error creating category:', error);
          alert(`Failed to create category: ${error.message}`);
          return;
        }
      }
    }
    
    const expense = {
      name: form.name,
      amount: Number(form.amount),
      date: form.date,
      description: form.description || '',
      category_id: categoryId
    };
    console.log('handleExpenseSubmit: Prepared expense object:', expense);
    
    const requestBody = { year, month: monthIdx, expense };
    console.log('handleExpenseSubmit: Request body:', JSON.stringify(requestBody, null, 2));
    
    try {
      console.log('handleExpenseSubmit: Making POST request to /api/expenses');
      const response = await fetch('http://localhost:5000/api/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      console.log('handleExpenseSubmit: Response status:', response.status, response.statusText);
      console.log('handleExpenseSubmit: Response headers:', [...response.headers.entries()]);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('handleExpenseSubmit: Response not ok:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const responseData = await response.json();
      console.log('handleExpenseSubmit: Response data:', responseData);
      
      setExpenseFormData(form => ({ ...form, [monthIdx]: {} }));
      setShowExpenseForm(forms => ({ ...forms, [monthIdx]: false }));
      setCategoryInput(prev => ({ ...prev, [monthIdx]: '' }));
      setShowCategorySuggestions(prev => ({ ...prev, [monthIdx]: false }));
      console.log('handleExpenseSubmit: Form cleared, refreshing expenses');
      
      // Invalidate cache to ensure fresh data
      invalidateCache();
      // Refresh expenses for this month
      await refreshExpensesForMonth(monthIdx);
      console.log('handleExpenseSubmit: Expenses refreshed successfully');
      
      // Show success message
      alert('Expense saved successfully!');
      
    } catch (error) {
      console.error('handleExpenseSubmit: Error occurred:', error);
      console.error('handleExpenseSubmit: Error stack:', error.stack);
      alert(`Failed to save expense: ${error.message}`);
    }
  };

  // Handle category input changes and filtering
  const handleCategoryInputChange = (monthId, value) => {
    setCategoryInput(prev => ({ ...prev, [monthId]: value }));
    
    if (value.trim()) {
      // Combine real categories and temp categories, then filter and sort
      const allCategories = [...categories, ...tempCategories];
      const filtered = allCategories
        .filter(category =>
          category && category.category_name && 
          category.category_name.toLowerCase().includes(value.toLowerCase())
        )
        .sort((a, b) => a.category_name.localeCompare(b.category_name));
      
      setFilteredCategories(prev => ({ ...prev, [monthId]: filtered }));
      setShowCategorySuggestions(prev => ({ ...prev, [monthId]: true }));
    } else {
      setShowCategorySuggestions(prev => ({ ...prev, [monthId]: false }));
      setFilteredCategories(prev => ({ ...prev, [monthId]: [] }));
    }
  };

  // Handle category selection from suggestions
  const handleCategorySelect = (monthId, category) => {
    setCategoryInput(prev => ({ ...prev, [monthId]: category.category_name }));
    setExpenseFormData(form => ({
      ...form,
      [monthId]: {
        ...form[monthId],
        category: category.category_id
      }
    }));
    setShowCategorySuggestions(prev => ({ ...prev, [monthId]: false }));
  };

  // Handle deleting a category
  const handleDeleteCategory = (categoryId, categoryName, isTemp = false) => {
    // Store category info for deletion and show modal
    setCategoryToDelete({
      id: categoryId,
      name: categoryName,
      isTemp: isTemp
    });
    setShowDeleteModal(true);
  };

  // Confirm and execute category deletion
  const confirmDeleteCategory = async () => {
    if (!categoryToDelete) return;

    const { id: categoryId, name: categoryName, isTemp } = categoryToDelete;

    try {
      if (isTemp) {
        // Remove from temporary categories
        setTempCategories(prev => prev.filter(cat => cat.category_id !== categoryId));
        console.log('Temporary category deleted:', categoryName);
      } else {
        // Delete from database
        console.log('Deleting category from database:', categoryName);
        
        const response = await fetch(`http://localhost:5000/api/categories/${categoryId}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Failed to delete category');
        }

        // Remove from categories list
        setCategories(prev => prev.filter(cat => cat.category_id !== categoryId));
        console.log('Category deleted successfully from database:', categoryName);
      }

      // Clear any form data using this category
      Object.keys(expenseFormData).forEach(monthId => {
        const form = expenseFormData[monthId];
        if (form && form.category === categoryId) {
          setExpenseFormData(prev => ({
            ...prev,
            [monthId]: {
              ...prev[monthId],
              category: ''
            }
          }));
          setCategoryInput(prev => ({ ...prev, [monthId]: '' }));
        }
      });

      // Close modal and reset state
      setShowDeleteModal(false);
      setCategoryToDelete(null);

    } catch (error) {
      console.error('Error deleting category:', error);
      alert(`Failed to delete category: ${error.message}`);
    }
  };

  // Cancel category deletion
  const cancelDeleteCategory = () => {
    setShowDeleteModal(false);
    setCategoryToDelete(null);
  };

  // Handle opening the category modal
  const openCategoryModal = (monthId) => {
    setCurrentMonthId(monthId);
    setNewCategoryName('');
    setShowCategoryModal(true);
    setShowCategorySuggestions(prev => ({ ...prev, [monthId]: false }));
  };

  // Handle creating temporary category (not saved to database until Save button)
  const handleCreateTempCategory = () => {
    const categoryName = newCategoryName.trim();
    if (!categoryName || !currentMonthId) return;

    // Check if category already exists (in both real categories and temp categories)
    const allCategories = [...categories, ...tempCategories];
    const existingCategory = allCategories.find(cat => 
      cat && cat.category_name &&
      cat.category_name.toLowerCase() === categoryName.toLowerCase()
    );

    if (existingCategory) {
      alert('Category already exists!');
      return;
    }

    // Create temporary category with negative ID (will be replaced when saved to database)
    // Store with title case for display consistency
    const tempCategory = {
      category_id: -(Date.now()), // Negative ID to distinguish from real categories
      category_name: categoryName.charAt(0).toUpperCase() + categoryName.slice(1).toLowerCase(),
      is_global: false,
      is_temp: true // Flag to identify temporary categories
    };

    // Add to temp categories
    setTempCategories(prev => [...prev, tempCategory]);

    // Set as selected category
    setCategoryInput(prev => ({ ...prev, [currentMonthId]: tempCategory.category_name }));
    setExpenseFormData(form => ({
      ...form,
      [currentMonthId]: {
        ...form[currentMonthId],
        category: tempCategory.category_id,
        categoryName: tempCategory.category_name // Store name for temporary categories
      }
    }));

    // Close modal
    setShowCategoryModal(false);
    setNewCategoryName('');
    setCurrentMonthId(null);
  };

  // Handle adding new category when user types a non-existing category
  const handleAddNewCategory = async (monthId, categoryName) => {
    if (!categoryName.trim()) return;

    try {
      const response = await fetch('http://localhost:5000/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_name: categoryName.trim() })
      });

      if (response.ok) {
        const result = await response.json();
        // Add the new category to the list
        setCategories(prev => [...prev, result.category]);
        
        // Set the new category as selected
        setExpenseFormData(form => ({
          ...form,
          [monthId]: {
            ...form[monthId],
            category: result.category.category_id
          }
        }));

        setCategoryInput(prev => ({ ...prev, [monthId]: result.category.category_name }));
        setShowCategorySuggestions(prev => ({ ...prev, [monthId]: false }));
        
        console.log('Category added successfully:', result.category);
      } else {
        const error = await response.json();
        alert(`Failed to add category: ${error.error}`);
      }
    } catch (error) {
      console.error('Error adding category:', error);
      alert('Failed to add category. Please try again.');
    }
  };

  // Handle category input blur (when user finishes typing)
  const handleCategoryInputBlur = (monthId) => {
    setTimeout(() => {
      const inputValue = categoryInput[monthId]?.trim();
      if (inputValue) {
        // Check if the input matches an existing category (including temp categories)
        const allCategories = [...categories, ...tempCategories];
        const existingCategory = allCategories.find(cat => 
          cat && cat.category_name &&
          cat.category_name.toLowerCase() === inputValue.toLowerCase()
        );
        
        if (existingCategory) {
          // Select the existing category
          handleCategorySelect(monthId, existingCategory);
        } else {
          // Clear form category selection since it's not a valid category yet
          setExpenseFormData(form => ({
            ...form,
            [monthId]: {
              ...form[monthId],
              category: ''
            }
          }));
        }
      }
      setShowCategorySuggestions(prev => ({ ...prev, [monthId]: false }));
    }, 200); // Small delay to allow for suggestion clicks
  };

  // Update global limit input (temporary state only)
  const handleGlobalLimitChange = (e) => {
    const value = e.target.value;
    setTempGlobalLimit(value);
  };

  // Save global limit to backend and update the actual global limit
  const saveGlobalLimit = async () => {
    try {
      console.log('Saving global limit:', tempGlobalLimit);
      const response = await fetch('http://localhost:5000/api/global_limit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ global_limit: Number(tempGlobalLimit) })
      });
      
      if (response.ok) {
        console.log('Global limit saved successfully');
        setGlobalLimit(Number(tempGlobalLimit)); // Update the actual global limit used in calculations
        setGlobalLimitSuccess('Global limit saved successfully!');
        setTimeout(() => setGlobalLimitSuccess(''), 3000); // Clear message after 3 seconds
        // Invalidate cache to ensure fresh data
        invalidateCache();
      } else {
        throw new Error('Failed to save global limit');
      }
    } catch (error) {
      console.error('Error saving global limit:', error);
      setGlobalLimitSuccess('Failed to save global limit');
      setTimeout(() => setGlobalLimitSuccess(''), 3000);
    }
  };

  // Update month limit input (temporary state only)
  const handleLimitChange = (monthIdx, value) => {
    console.log('App: handleLimitChange called with monthIdx:', monthIdx, 'value:', value);
    setTempMonthLimits(limits => ({ ...limits, [monthIdx]: value }));
  };

  // Force refresh monthly limits from database
  const refreshMonthlyLimits = async () => {
    try {
      console.log('🔄 Force refreshing monthly limits from PostgreSQL');
      const limitData = {};
      const tempLimitData = {};
      
      for (const monthObj of months) {
        const monthId = monthObj.month_id;
        try {
          const monthResponse = await fetch(`http://localhost:5000/api/limit?year=${year}&month=${monthId}`, {
            signal: AbortSignal.timeout(5000)
          });
          
          if (monthResponse.ok) {
            const monthData = await monthResponse.json();
            if (monthData.limit > 0) {
              limitData[monthId] = monthData.limit;
              tempLimitData[monthId] = monthData.limit.toString();
            }
          }
        } catch (error) {
          console.log(`❌ Failed to fetch limit for month ${monthId}:`, error);
        }
      }
      
      console.log('🔄 Refreshed monthly limits:', limitData);
      setMonthLimits(limitData);
      setTempMonthLimits(tempLimitData);
    } catch (error) {
      console.error('Error refreshing monthly limits:', error);
    }
  };

  // Clear monthly limit (remove it entirely)
  const clearMonthlyLimit = async (monthIdx) => {
    try {
      console.log('Clearing monthly limit for month:', monthIdx);
      
      // Send 0 to backend to clear the limit
      const requestData = { year, month: monthIdx, limit: 0 };
      console.log('App: Sending POST to /api/limit to clear limit:', requestData);
      
      const response = await fetch('http://localhost:5000/api/limit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });
      
      if (response.ok) {
        console.log('App: Monthly limit cleared successfully');
        
        // Remove the monthly limit from state (will fall back to global)
        setMonthLimits(limits => {
          const newLimits = { ...limits };
          delete newLimits[monthIdx];
          console.log('App: Removed monthly limit from state, new limits:', newLimits);
          return newLimits;
        });
        setTempMonthLimits(limits => {
          const newLimits = { ...limits };
          delete newLimits[monthIdx];
          return newLimits;
        });
        
        // Invalidate cache to ensure fresh data on next load
        invalidateCache();
        
        setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: 'Monthly limit cleared - using global limit' }));
        setTimeout(() => {
          setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: '' }));
        }, 3000);
      } else {
        throw new Error('Failed to clear monthly limit');
      }
    } catch (error) {
      console.error('App: Error clearing monthly limit:', error);
      setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: 'Failed to clear monthly limit' }));
      setTimeout(() => {
        setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: '' }));
      }, 3000);
    }
  };

  // Save monthly limit to backend
  const saveMonthlyLimit = async (monthIdx) => {
    try {
      const value = tempMonthLimits[monthIdx] || '';
      console.log('Saving monthly limit for month:', monthIdx, 'value:', value);
      
      // Don't save empty values - user should use Clear button instead
      if (!value || value.trim() === '') {
        setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: 'Please enter a limit amount or use Clear to remove' }));
        setTimeout(() => {
          setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: '' }));
        }, 3000);
        return;
      }
      
      const limitValue = Number(value);
      if (limitValue <= 0) {
        setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: 'Limit must be greater than 0' }));
        setTimeout(() => {
          setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: '' }));
        }, 3000);
        return;
      }
      
      const requestData = { year, month: monthIdx, limit: limitValue };
      console.log('App: Sending POST to /api/limit with data:', requestData);
      
      const response = await fetch('http://localhost:5000/api/limit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('App: POST /api/limit response data:', data);
        
        // IMMEDIATELY update the monthLimits state with the saved value
        setMonthLimits(prev => {
          const updated = { ...prev, [monthIdx]: limitValue };
          console.log('App: Updated monthLimits state after save:', updated);
          return updated;
        });
        
        // Invalidate cache to ensure fresh data on next load
        invalidateCache();
        
        setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: 'Monthly limit saved successfully!' }));
        setTimeout(() => {
          setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: '' }));
        }, 3000);
        
        console.log('App: Monthly limit saved and state updated successfully');
      } else {
        const errorText = await response.text();
        console.error('App: Error response from /api/limit:', errorText);
        setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: 'Failed to save monthly limit' }));
        setTimeout(() => {
          setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: '' }));
        }, 3000);
      }
    } catch (error) {
      console.error('App: Error saving monthly limit:', error);
      setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: 'Failed to save monthly limit' }));
      setTimeout(() => {
        setMonthLimitSuccess(prev => ({ ...prev, [monthIdx]: '' }));
      }, 3000);
    }
  }

  const handleAddExpense = (monthIdx) => {
    setShowExpenseForm(forms => ({ ...forms, [monthIdx]: !forms[monthIdx] }));
    // If closing the form, clear category input
    if (showExpenseForm[monthIdx]) {
      setCategoryInput(prev => ({ ...prev, [monthIdx]: '' }));
      setShowCategorySuggestions(prev => ({ ...prev, [monthIdx]: false }));
    }
  };

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    );
  }

  // Show authentication pages if user is not logged in
  if (!user) {
    return (
      <>
        {authMode === 'login' ? (
          <Login 
            onLogin={handleLogin}
            onSwitchToSignup={() => setAuthMode('signup')}
          />
        ) : (
          <Signup 
            onSignup={handleSignup}
            onSwitchToLogin={() => setAuthMode('login')}
          />
        )}
      </>
    );
  }

  return (
    <>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
      <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Beautiful gradient orbs */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'none'
      }}>
        <div style={{
          position: 'absolute',
          top: '10%',
          left: '10%',
          width: '400px',
          height: '400px',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'float 20s ease-in-out infinite',
          filter: 'blur(60px)'
        }}></div>
        <div style={{
          position: 'absolute',
          top: '30%',
          right: '15%',
          width: '350px',
          height: '350px',
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.08) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'float 15s ease-in-out infinite reverse',
          filter: 'blur(50px)'
        }}></div>
        <div style={{
          position: 'absolute',
          bottom: '20%',
          left: '50%',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(14, 165, 233, 0.06) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'float 25s ease-in-out infinite',
          filter: 'blur(40px)'
        }}></div>
      </div>

      {/* Subtle pattern overlay */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 1,
        pointerEvents: 'none',
        background: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23e2e8f0' fill-opacity='0.1'%3E%3Cpath d='m0 40l40-40h-40v40zm40 0v-40h-40l40 40z'/%3E%3C/g%3E%3C/svg%3E")`,
        opacity: 0.3
      }}></div>

      <header style={{
        position: 'relative',
        zIndex: 10,
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(148, 163, 184, 0.2)',
        padding: '24px 0',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.02), 0 1px 2px rgba(0, 0, 0, 0.06)'
      }}>
        <div style={{
          maxWidth: '1600px',
          margin: '0 auto',
          padding: '0 40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h1 style={{
              fontSize: 'clamp(2rem, 5vw, 3.5rem)',
              fontWeight: '800',
              background: 'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              margin: 0,
              letterSpacing: '-0.03em',
              fontFamily: "'Inter', sans-serif"
            }}>
              ExpenseFlow
            </h1>
            <p style={{
              color: '#64748b',
              fontSize: '14px',
              margin: '8px 0 0 0',
              fontWeight: '500',
              letterSpacing: '0.05em'
            }}>
              Smart Financial Management
            </p>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '24px'
          }}>
            <div style={{
              color: '#475569',
              fontSize: '14px',
              fontWeight: '600',
              padding: '8px 16px',
              background: 'rgba(99, 102, 241, 0.1)',
              borderRadius: '12px',
              border: '1px solid rgba(99, 102, 241, 0.2)'
            }}>
              {user.name}
            </div>
            <button 
              onClick={handleLogout}
              style={{
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                border: 'none',
                borderRadius: '12px',
                padding: '12px 24px',
                color: 'white',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 6px rgba(239, 68, 68, 0.2)',
                fontFamily: "'Inter', sans-serif"
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 15px rgba(239, 68, 68, 0.3)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 6px rgba(239, 68, 68, 0.2)';
              }}
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main style={{
        position: 'relative',
        zIndex: 10,
        maxWidth: '1600px',
        margin: '0 auto',
        padding: '60px 40px',
        display: 'grid',
        gridTemplateColumns: '400px 1fr',
        gap: '60px',
        minHeight: 'calc(100vh - 120px)'
      }}>
        {/* Left Panel - Elegant Light */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(148, 163, 184, 0.2)',
          borderRadius: '24px',
          padding: '32px',
          height: 'fit-content',
          position: 'sticky',
          top: '60px',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.05), 0 4px 6px rgba(0, 0, 0, 0.02)'
        }}>
          {/* Year Selector */}
          <div style={{ marginBottom: '40px' }}>
            <label style={{
              display: 'block',
              color: '#475569',
              fontSize: '14px',
              fontWeight: '600',
              marginBottom: '12px',
              fontFamily: "'Inter', sans-serif"
            }}>
              Year
            </label>
            <select 
              value={year} 
              onChange={e => setYear(Number(e.target.value))}
              style={{
                width: '100%',
                background: 'white',
                border: '2px solid #e2e8f0',
                borderRadius: '16px',
                padding: '16px 20px',
                color: '#1e293b',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer',
                outline: 'none',
                transition: 'all 0.3s ease',
                fontFamily: "'Inter', sans-serif",
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                boxSizing: 'border-box'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#6366f1';
                e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e2e8f0';
                e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
              }}
            >
              {[2024, 2025, 2026].map(y => (
                <option key={y} value={y} style={{ background: 'white', color: '#1e293b' }}>{y}</option>
              ))}
            </select>
          </div>

          {/* Global Limit */}
          <div>
            <label style={{
              display: 'block',
              color: '#475569',
              fontSize: '14px',
              fontWeight: '600',
              marginBottom: '12px',
              fontFamily: "'Inter', sans-serif"
            }}>
              Global Monthly Limit
            </label>
            <input 
              type="number" 
              placeholder="Enter amount..." 
              min="0" 
              step="0.01" 
              value={tempGlobalLimit} 
              onChange={handleGlobalLimitChange}
              style={{
                width: '100%',
                background: 'white',
                border: '2px solid #e2e8f0',
                borderRadius: '16px',
                padding: '16px 20px',
                color: '#1e293b',
                fontSize: '16px',
                marginBottom: '20px',
                outline: 'none',
                transition: 'all 0.3s ease',
                fontFamily: "'Inter', sans-serif",
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                boxSizing: 'border-box'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#6366f1';
                e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e2e8f0';
                e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
              }}
            />
            <button 
              onClick={saveGlobalLimit}
              style={{
                width: '100%',
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                border: 'none',
                borderRadius: '16px',
                padding: '16px 20px',
                color: 'white',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                fontFamily: "'Inter', sans-serif",
                boxShadow: '0 4px 6px rgba(99, 102, 241, 0.2)'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 15px rgba(99, 102, 241, 0.3)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 6px rgba(99, 102, 241, 0.2)';
              }}
            >
              Save Global Limit
            </button>
            {globalLimitSuccess && (
              <div style={{
                marginTop: '16px',
                padding: '16px',
                background: globalLimitSuccess.includes('Failed') ? 
                  'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)',
                border: `2px solid ${globalLimitSuccess.includes('Failed') ? 
                  '#ef4444' : '#22c55e'}`,
                borderRadius: '12px',
                color: globalLimitSuccess.includes('Failed') ? '#dc2626' : '#16a34a',
                fontSize: '14px',
                fontWeight: '500',
                fontFamily: "'Inter', sans-serif"
              }}>
                {globalLimitSuccess}
              </div>
            )}
          </div>
        </div>
        {/* Right Panel - Beautiful Light Design */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '24px'
        }}>
          {months.map((monthObj) => {
            const monthId = monthObj.month_id;
            const monthName = monthObj.month_name;
            
            // Never show loading states for instant display
            const isLoadingMonthlyLimits = false;
            console.log(`🔍 Month ${monthId}: monthLimits[${monthId}] =`, monthLimits[monthId]);
            console.log(`🔍 Month ${monthId}: monthLimits full object =`, monthLimits);
            const hasMonthlyLimit = monthLimits[monthId] && monthLimits[monthId] > 0;
            console.log(`🔍 Month ${monthId}: hasMonthlyLimit =`, hasMonthlyLimit);
            
            // Always use the best available limit data
            const limit = hasMonthlyLimit ? monthLimits[monthId] : globalLimit;
            const expList = Array.isArray(expenses[`${year}-${monthId}`]) ? expenses[`${year}-${monthId}`] : [];
            const total = expList.reduce((sum, exp) => {
              const price = exp.expense_item_price || 0;
              return sum + (typeof price === 'number' ? price : parseFloat(price) || 0);
            }, 0);
              const limitExceeded = limit > 0 && total > limit;
              const progress = limit > 0 ? Math.min((total / limit) * 100, 100) : 0;
              const isExpanded = showExpenseForm[monthId];
              
              return (
                <div 
                  key={monthId}
                  style={{
                    background: 'rgba(255, 255, 255, 0.9)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                    borderRadius: '24px',
                    borderLeft: `6px solid ${limitExceeded ? '#ef4444' : limit > 0 ? '#22c55e' : '#94a3b8'}`,
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.05), 0 4px 6px rgba(0, 0, 0, 0.02)',
                    overflow: 'hidden'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.06)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.05), 0 4px 6px rgba(0, 0, 0, 0.02)';
                  }}
                >
                  {/* Month Header */}
                  <div 
                    onClick={() => handleAddExpense(monthId)}
                    style={{
                      padding: '32px 40px',
                      cursor: 'pointer',
                      borderBottom: isExpanded ? '1px solid rgba(148, 163, 184, 0.2)' : 'none',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start'
                    }}>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'baseline',
                          gap: '24px',
                          marginBottom: '24px'
                        }}>
                          <h2 style={{
                            fontSize: '28px',
                            fontWeight: '700',
                            color: '#1e293b',
                            margin: 0,
                            fontFamily: "'Inter', sans-serif"
                          }}>
                            {monthName}
                          </h2>
                          
                          <div style={{
                            fontSize: '36px',
                            fontWeight: '800',
                            color: limitExceeded ? '#ef4444' : '#1e293b',
                            fontFamily: "'Inter', sans-serif"
                          }}>
                            ${!isNaN(Number(total)) ? Number(total).toFixed(2) : '0.00'}
                          </div>
                        </div>

                        {/* Progress Bar */}
                        {!isLoadingMonthlyLimits && limit > 0 && (
                          <div style={{
                            background: '#f1f5f9',
                            height: '8px',
                            borderRadius: '12px',
                            overflow: 'hidden',
                            marginBottom: '20px',
                            border: '1px solid rgba(148, 163, 184, 0.1)'
                          }}>
                            <div style={{
                              width: `${progress}%`,
                              height: '100%',
                              background: limitExceeded ? 
                                'linear-gradient(90deg, #ef4444 0%, #dc2626 100%)' : 
                                'linear-gradient(90deg, #22c55e 0%, #16a34a 100%)',
                              transition: 'all 0.5s ease',
                              borderRadius: '12px'
                            }}></div>
                          </div>
                        )}

                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                          gap: '24px',
                          fontSize: '14px',
                          fontWeight: '500',
                          fontFamily: "'Inter', sans-serif"
                        }}>
                          <div style={{
                            padding: '16px',
                            background: isLoadingMonthlyLimits ? 'rgba(148, 163, 184, 0.05)' : (hasMonthlyLimit ? 'rgba(168, 85, 247, 0.05)' : 'rgba(99, 102, 241, 0.05)'),
                            borderRadius: '16px',
                            border: `1px solid ${isLoadingMonthlyLimits ? 'rgba(148, 163, 184, 0.1)' : (hasMonthlyLimit ? 'rgba(168, 85, 247, 0.1)' : 'rgba(99, 102, 241, 0.1)')}`
                          }}>
                            <div style={{ 
                              color: isLoadingMonthlyLimits ? '#64748b' : (hasMonthlyLimit ? '#a855f7' : '#6366f1'), 
                              marginBottom: '8px', 
                              fontWeight: '600' 
                            }}>
                              {isLoadingMonthlyLimits ? 'Loading Limits...' : (hasMonthlyLimit ? 'Monthly Limit' : 'Budget Limit')}
                            </div>
                            <div style={{ color: '#1e293b', fontSize: '18px', fontWeight: '700' }}>
                              {isLoadingMonthlyLimits ? (
                                <span style={{ 
                                  color: '#64748b',
                                  fontSize: '14px',
                                  fontStyle: 'italic'
                                }}>
                                  Please wait...
                                </span>
                              ) : dataLoading ? (
                                <span style={{
                                  color: '#94a3b8',
                                  fontStyle: 'italic'
                                }}>
                                  Loading...
                                </span>
                              ) : (
                                limit > 0 ? `$${limit.toFixed(2)}` : 'No Limit'
                              )}
                            </div>
                            {!isLoadingMonthlyLimits && hasMonthlyLimit && (
                              <div style={{ 
                                color: '#a855f7', 
                                fontSize: '12px', 
                                fontWeight: '500',
                                marginTop: '4px'
                              }}>
                                Custom Override
                              </div>
                            )}
                            {!isLoadingMonthlyLimits && !hasMonthlyLimit && globalLimit > 0 && (
                              <div style={{ 
                                color: '#64748b', 
                                fontSize: '12px', 
                                fontWeight: '500',
                                marginTop: '4px'
                              }}>
                                From Global
                              </div>
                            )}
                          </div>
                          
                          <div style={{
                            padding: '16px',
                            background: limitExceeded ? 'rgba(239, 68, 68, 0.05)' : 'rgba(34, 197, 94, 0.05)',
                            borderRadius: '16px',
                            border: `1px solid ${limitExceeded ? 'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)'}`
                          }}>
                            <div style={{ 
                              color: limitExceeded ? '#ef4444' : '#22c55e', 
                              marginBottom: '8px', 
                              fontWeight: '600' 
                            }}>Status</div>
                            <div style={{ 
                              color: limitExceeded ? '#dc2626' : '#16a34a',
                              fontSize: '16px',
                              fontWeight: '700'
                            }}>
                              {dataLoading ? 'Loading...' : 
                                (limit > 0 ? 
                                  (limitExceeded ? `Over by $${(total - limit).toFixed(2)}` : `Under by $${(limit - total).toFixed(2)}`) 
                                  : 'No Tracking'
                                )
                              }
                            </div>
                          </div>
                          
                          <div style={{
                            padding: '16px',
                            background: 'rgba(168, 85, 247, 0.05)',
                            borderRadius: '16px',
                            border: '1px solid rgba(168, 85, 247, 0.1)'
                          }}>
                            <div style={{ color: '#a855f7', marginBottom: '8px', fontWeight: '600' }}>Expenses</div>
                            <div style={{ color: '#1e293b', fontSize: '18px', fontWeight: '700' }}>
                              {dataLoading ? 'Loading...' : `${expList.length} items`}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div style={{
                        fontSize: '24px',
                        color: '#94a3b8',
                        transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s ease',
                        padding: '8px',
                        borderRadius: '12px',
                        background: isExpanded ? 'rgba(99, 102, 241, 0.1)' : 'transparent'
                      }}>
                        ▼
                      </div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {showExpenseForm[monthId] && (
                    <div style={{
                      padding: '40px',
                      background: 'rgba(0, 0, 0, 0.4)',
                      animation: 'slideDown 0.3s ease-out',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '40px'
                    }}>
                      {/* Month Controls */}
                      <div style={{
                        padding: '32px',
                        background: 'rgba(255, 255, 255, 0.8)',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                        borderRadius: '20px',
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
                      }}>
                        <h3 style={{
                          fontSize: '16px',
                          fontWeight: '600',
                          color: '#1e293b',
                          margin: '0 0 24px 0',
                          fontFamily: "'Inter', sans-serif"
                        }}>
                          Monthly Limit Control
                        </h3>
                        
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: '1fr auto auto',
                          gap: '16px',
                          alignItems: 'end'
                        }}>
                          <div>
                            <label style={{
                              display: 'block',
                              color: '#475569',
                              fontSize: '14px',
                              fontWeight: '600',
                              marginBottom: '12px',
                              fontFamily: "'Inter', sans-serif"
                            }}>
                              Amount
                            </label>
                            <input 
                              type="number" 
                              placeholder={globalLimit > 0 ? `Global: $${globalLimit}` : "Enter amount..."} 
                              value={tempMonthLimits[monthId] || ''} 
                              onChange={e => handleLimitChange(monthId, e.target.value)}
                              style={{
                                width: '100%',
                                background: 'white',
                                border: '2px solid #e2e8f0',
                                borderRadius: '12px',
                                padding: '16px 20px',
                                color: '#1e293b',
                                fontSize: '16px',
                                outline: 'none',
                                transition: 'all 0.3s ease',
                                fontFamily: "'Inter', sans-serif",
                                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)'
                              }}
                              onFocus={(e) => {
                                e.target.style.borderColor = '#6366f1';
                                e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                              }}
                              onBlur={(e) => {
                                e.target.style.borderColor = '#e2e8f0';
                                e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                              }}
                            />
                          </div>
                          
                          <button 
                            onClick={() => saveMonthlyLimit(monthId)}
                            style={{
                              background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                              border: 'none',
                              borderRadius: '12px',
                              padding: '16px 20px',
                              color: 'white',
                              fontSize: '14px',
                              fontWeight: '600',
                              cursor: 'pointer',
                              transition: 'all 0.3s ease',
                              fontFamily: "'Inter', sans-serif",
                              boxShadow: '0 4px 6px rgba(99, 102, 241, 0.2)'
                            }}
                            onMouseOver={(e) => {
                              e.target.style.transform = 'translateY(-2px)';
                              e.target.style.boxShadow = '0 8px 15px rgba(99, 102, 241, 0.3)';
                            }}
                            onMouseOut={(e) => {
                              e.target.style.transform = 'translateY(0)';
                              e.target.style.boxShadow = '0 4px 6px rgba(99, 102, 241, 0.2)';
                            }}
                          >
                            Save
                          </button>
                          
                          {hasMonthlyLimit && (
                            <button 
                              onClick={() => clearMonthlyLimit(monthId)}
                              style={{
                                background: 'transparent',
                                border: '2px solid #ef4444',
                                borderRadius: '12px',
                                padding: '16px 20px',
                                color: '#ef4444',
                                fontSize: '14px',
                                fontWeight: '600',
                                cursor: 'pointer',
                                transition: 'all 0.3s ease',
                                fontFamily: "'Inter', sans-serif"
                              }}
                              onMouseOver={(e) => {
                                e.target.style.background = '#ef4444';
                                e.target.style.color = 'white';
                                e.target.style.transform = 'translateY(-2px)';
                              }}
                              onMouseOut={(e) => {
                                e.target.style.background = 'transparent';
                                e.target.style.color = '#ef4444';
                                e.target.style.transform = 'translateY(0)';
                              }}
                            >
                              Clear
                            </button>
                          )}
                        </div>
                        
                        {!hasMonthlyLimit && globalLimit > 0 && (
                          <div style={{
                            marginTop: '16px',
                            color: '#64748b',
                            fontSize: '14px',
                            fontFamily: "'Inter', sans-serif"
                          }}>
                            Using global limit: ${globalLimit}
                          </div>
                        )}
                        
                        {monthLimitSuccess[monthId] && (
                          <div style={{
                            marginTop: '16px',
                            padding: '16px',
                            background: monthLimitSuccess[monthId].includes('Failed') ? 
                              'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)',
                            border: `2px solid ${monthLimitSuccess[monthId].includes('Failed') ? 
                              '#ef4444' : '#22c55e'}`,
                            borderRadius: '12px',
                            color: monthLimitSuccess[monthId].includes('Failed') ? '#dc2626' : '#16a34a',
                            fontSize: '14px',
                            fontWeight: '500',
                            fontFamily: "'Inter', sans-serif"
                          }}>
                            {monthLimitSuccess[monthId]}
                          </div>
                        )}
                      </div>

                      {/* Add Expense Form */}
                      <div style={{
                        background: 'rgba(255, 255, 255, 0.8)',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                        borderRadius: '20px',
                        padding: '32px',
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
                      }}>
                        <h3 style={{
                          fontSize: '16px',
                          fontWeight: '600',
                          color: '#1e293b',
                          margin: '0 0 24px 0',
                          fontFamily: "'Inter', sans-serif"
                        }}>
                          Add New Expense
                        </h3>

                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '20px',
                          marginBottom: '24px'
                        }}>
                          {/* Name and Amount Row */}
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gap: '20px'
                          }}>
                            <div>
                              <label style={{
                                color: '#475569',
                                fontSize: '14px',
                                fontWeight: '600',
                                marginBottom: '8px',
                                display: 'block',
                                fontFamily: "'Inter', sans-serif"
                              }}>Name</label>
                              <input 
                                type="text" 
                                placeholder="Expense name..."
                                value={expenseFormData[monthId]?.name || ''} 
                                onChange={e => handleExpenseInputChange(monthId, 'name', e.target.value)}
                                style={{
                                  width: '100%',
                                  padding: '16px 20px',
                                  borderRadius: '12px',
                                  border: '2px solid #e2e8f0',
                                  background: 'white',
                                  color: '#1e293b',
                                  fontSize: '16px',
                                  fontWeight: '500',
                                  outline: 'none',
                                  transition: 'all 0.3s ease',
                                  fontFamily: "'Inter', sans-serif",
                                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                                  boxSizing: 'border-box'
                                }}
                                onFocus={(e) => {
                                  e.target.style.borderColor = '#6366f1';
                                  e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                                }}
                                onBlur={(e) => {
                                  e.target.style.borderColor = '#e2e8f0';
                                  e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                                }}
                              />
                            </div>

                            <div>
                              <label style={{
                                color: '#475569',
                                fontSize: '14px',
                                fontWeight: '600',
                                marginBottom: '8px',
                                display: 'block',
                                fontFamily: "'Inter', sans-serif"
                              }}>Amount</label>
                              <input 
                                type="number" 
                                placeholder="0.00"
                                value={expenseFormData[monthId]?.amount || ''} 
                                onChange={e => handleExpenseInputChange(monthId, 'amount', e.target.value)}
                                style={{
                                  width: '100%',
                                  padding: '16px 20px',
                                  borderRadius: '12px',
                                  border: '2px solid #e2e8f0',
                                  background: 'white',
                                  color: '#1e293b',
                                  fontSize: '16px',
                                  fontWeight: '500',
                                  outline: 'none',
                                  transition: 'all 0.3s ease',
                                  fontFamily: "'Inter', sans-serif",
                                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                                  boxSizing: 'border-box'
                                }}
                                onFocus={(e) => {
                                  e.target.style.borderColor = '#6366f1';
                                  e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                                }}
                                onBlur={(e) => {
                                  e.target.style.borderColor = '#e2e8f0';
                                  e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                                }}
                              />
                            </div>
                          </div>

                          {/* Date and Category Row */}
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gap: '20px'
                          }}>
                            <div>
                              <label style={{
                                color: '#475569',
                                fontSize: '14px',
                                fontWeight: '600',
                                marginBottom: '8px',
                                display: 'block',
                                fontFamily: "'Inter', sans-serif"
                              }}>Date</label>
                              <select 
                                value={expenseFormData[monthId]?.date || ''} 
                                onChange={e => handleExpenseInputChange(monthId, 'date', e.target.value)}
                                style={{
                                  width: '100%',
                                  padding: '16px 20px',
                                  borderRadius: '12px',
                                  border: '2px solid #e2e8f0',
                                  background: 'white',
                                  color: '#1e293b',
                                  fontSize: '16px',
                                  fontWeight: '500',
                                  outline: 'none',
                                  transition: 'all 0.3s ease',
                                  fontFamily: "'Inter', sans-serif",
                                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                                  boxSizing: 'border-box',
                                  cursor: 'pointer'
                                }}
                                onFocus={(e) => {
                                  e.target.style.borderColor = '#6366f1';
                                  e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                                }}
                                onBlur={(e) => {
                                  e.target.style.borderColor = '#e2e8f0';
                                  e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                                }}
                              >
                                <option value="" disabled>Select {monthName} date...</option>
                                {(() => {
                                  // Generate all dates for the current month
                                  const monthIndex = monthId - 13; // monthId starts at 13 for January
                                  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
                                  const dates = [];
                                  
                                  for (let day = 1; day <= daysInMonth; day++) {
                                    const date = new Date(year, monthIndex, day);
                                    const dateString = date.toISOString().split('T')[0];
                                    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
                                    dates.push(
                                      <option key={day} value={dateString} style={{ background: 'white', color: '#1e293b' }}>
                                        {monthName} {day}, {year} ({dayName})
                                      </option>
                                    );
                                  }
                                  return dates;
                                })()}
                              </select>
                            </div>

                            <div>
                              <label style={{
                                color: '#475569',
                                fontSize: '14px',
                                fontWeight: '600',
                                marginBottom: '8px',
                                display: 'block',
                                fontFamily: "'Inter', sans-serif"
                              }}>Category</label>
                              <div style={{ position: 'relative' }}>
                                <input 
                                  type="text"
                                  placeholder="Type to search or add new category..."
                                  value={categoryInput[monthId] || ''}
                                  onChange={e => handleCategoryInputChange(monthId, e.target.value)}
                                  onBlur={(e) => {
                                    e.target.style.borderColor = '#e2e8f0';
                                    e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                                    handleCategoryInputBlur(monthId);
                                  }}
                                  onFocus={(e) => {
                                    e.target.style.borderColor = '#6366f1';
                                    e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                                    
                                    // Combine real categories and temp categories
                                    const allCategories = [...categories, ...tempCategories];
                                    
                                    // Show all categories initially, or filtered categories if user has typed something
                                    if (categoryInput[monthId]?.trim()) {
                                      const filtered = allCategories
                                        .filter(category =>
                                          category && category.category_name && 
                                          category.category_name.toLowerCase().includes(categoryInput[monthId].toLowerCase())
                                        )
                                        .sort((a, b) => a.category_name.localeCompare(b.category_name));
                                      setFilteredCategories(prev => ({ ...prev, [monthId]: filtered }));
                                    } else {
                                      // Show all categories when field is empty, sorted
                                      const sortedCategories = allCategories
                                        .filter(category => category && category.category_name)
                                        .sort((a, b) => a.category_name.localeCompare(b.category_name));
                                      setFilteredCategories(prev => ({ ...prev, [monthId]: sortedCategories }));
                                    }
                                    setShowCategorySuggestions(prev => ({ ...prev, [monthId]: true }));
                                  }}
                                  style={{
                                    width: '100%',
                                    padding: '16px 20px',
                                    borderRadius: '12px',
                                    border: '2px solid #e2e8f0',
                                    background: 'white',
                                    color: '#1e293b',
                                    fontSize: '16px',
                                    fontWeight: '500',
                                    outline: 'none',
                                    transition: 'all 0.3s ease',
                                    fontFamily: "'Inter', sans-serif",
                                    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                                    boxSizing: 'border-box'
                                  }}
                                />
                                
                                {/* Category Suggestions Dropdown */}
                                {showCategorySuggestions[monthId] && (
                                  <div style={{
                                    position: 'absolute',
                                    top: '100%',
                                    left: 0,
                                    right: 0,
                                    backgroundColor: 'white',
                                    border: '2px solid #e2e8f0',
                                    borderTop: 'none',
                                    borderRadius: '0 0 12px 12px',
                                    boxShadow: '0 8px 16px rgba(0, 0, 0, 0.1)',
                                    zIndex: 1000,
                                    maxHeight: '200px',
                                    overflowY: 'auto'
                                  }}>
                                    {/* Show "Add Category" button at top when field is first clicked (empty) */}
                                    {!categoryInput[monthId]?.trim() && (
                                      <div
                                        onMouseDown={() => openCategoryModal(monthId)}
                                        style={{
                                          padding: '12px 20px',
                                          cursor: 'pointer',
                                          fontSize: '16px',
                                          fontWeight: '600',
                                          color: '#6366f1',
                                          fontFamily: "'Inter', sans-serif",
                                          transition: 'background-color 0.2s ease',
                                          background: '#fafbff',
                                          borderBottom: '2px solid #e2e8f0'
                                        }}
                                        onMouseOver={(e) => {
                                          e.target.style.backgroundColor = '#f0f0ff';
                                        }}
                                        onMouseOut={(e) => {
                                          e.target.style.backgroundColor = '#fafbff';
                                        }}
                                      >
                                        ➕ Add New Category
                                      </div>
                                    )}
                                    
                                    {/* Show existing category matches */}
                                    {filteredCategories[monthId]?.map(category => (
                                      <div
                                        key={category.category_id}
                                        style={{
                                          padding: '12px 20px',
                                          borderBottom: '1px solid #f1f5f9',
                                          fontSize: '16px',
                                          fontWeight: '500',
                                          color: '#1e293b',
                                          fontFamily: "'Inter', sans-serif",
                                          transition: 'background-color 0.2s ease',
                                          display: 'flex',
                                          alignItems: 'center',
                                          justifyContent: 'space-between'
                                        }}
                                        onMouseOver={(e) => {
                                          e.currentTarget.style.backgroundColor = '#f8fafc';
                                        }}
                                        onMouseOut={(e) => {
                                          e.currentTarget.style.backgroundColor = 'white';
                                        }}
                                      >
                                        <div
                                          onMouseDown={(e) => {
                                            e.stopPropagation();
                                            handleCategorySelect(monthId, category);
                                          }}
                                          style={{
                                            cursor: 'pointer',
                                            flex: 1,
                                            display: 'flex',
                                            alignItems: 'center'
                                          }}
                                        >
                                          {category.category_name}
                                          {category.is_global && (
                                            <span style={{
                                              fontSize: '12px',
                                              color: '#64748b',
                                              marginLeft: '8px',
                                              fontWeight: '400'
                                            }}>
                                              (Global)
                                            </span>
                                          )}
                                          {category.is_temp && (
                                            <span style={{
                                              fontSize: '12px',
                                              color: '#f59e0b',
                                              marginLeft: '8px',
                                              fontWeight: '400'
                                            }}>
                                              (New)
                                            </span>
                                          )}
                                        </div>
                                        
                                        {/* Delete button (only for non-global categories or temp categories) */}
                                        {(!category.is_global || category.is_temp) && (
                                          <button
                                            onMouseDown={(e) => {
                                              e.stopPropagation();
                                              handleDeleteCategory(
                                                category.category_id, 
                                                category.category_name, 
                                                category.is_temp
                                              );
                                            }}
                                            style={{
                                              background: 'none',
                                              border: 'none',
                                              color: '#ef4444',
                                              fontSize: '18px',
                                              fontWeight: 'bold',
                                              cursor: 'pointer',
                                              padding: '4px 8px',
                                              borderRadius: '4px',
                                              transition: 'all 0.2s ease',
                                              marginLeft: '8px',
                                              display: 'flex',
                                              alignItems: 'center',
                                              justifyContent: 'center',
                                              minWidth: '24px',
                                              height: '24px'
                                            }}
                                            onMouseOver={(e) => {
                                              e.target.style.backgroundColor = '#fee2e2';
                                              e.target.style.color = '#dc2626';
                                            }}
                                            onMouseOut={(e) => {
                                              e.target.style.backgroundColor = 'transparent';
                                              e.target.style.color = '#ef4444';
                                            }}
                                            title={`Delete "${category.category_name}"`}
                                          >
                                            ×
                                          </button>
                                        )}
                                      </div>
                                    ))}
                                    
                                    {/* Show "Add [typed text] as new category" option if user has typed something and no exact match found */}
                                    {(() => {
                                      const inputValue = categoryInput[monthId]?.trim();
                                      const allCategories = [...categories, ...tempCategories];
                                      const exactMatch = allCategories.find(cat => 
                                        cat && cat.category_name && inputValue &&
                                        cat.category_name.toLowerCase() === inputValue.toLowerCase()
                                      );
                                      const hasFilteredResults = filteredCategories[monthId]?.length > 0;
                                      
                                      if (inputValue && !exactMatch) {
                                        return (
                                          <div
                                            onMouseDown={() => handleAddNewCategory(monthId, inputValue)}
                                            style={{
                                              padding: '12px 20px',
                                              cursor: 'pointer',
                                              fontSize: '16px',
                                              fontWeight: '600',
                                              color: '#6366f1',
                                              fontFamily: "'Inter', sans-serif",
                                              transition: 'background-color 0.2s ease',
                                              borderTop: hasFilteredResults ? '2px solid #f1f5f9' : 'none',
                                              background: '#fafbff'
                                            }}
                                            onMouseOver={(e) => {
                                              e.target.style.backgroundColor = '#f0f0ff';
                                            }}
                                            onMouseOut={(e) => {
                                              e.target.style.backgroundColor = '#fafbff';
                                            }}
                                          >
                                            ➕ Add "{inputValue}" as new category
                                          </div>
                                        );
                                      }
                                      return null;
                                    })()}
                                    
                                    {/* Show message when no categories exist yet */}
                                    {filteredCategories[monthId]?.length === 0 && !categoryInput[monthId]?.trim() && categories.length === 0 && tempCategories.length === 0 && (
                                      <div style={{
                                        padding: '12px 20px',
                                        fontSize: '14px',
                                        color: '#64748b',
                                        fontStyle: 'italic',
                                        fontFamily: "'Inter', sans-serif"
                                      }}>
                                        No categories available. Click "Add New Category" to create one!
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Description Field - Full Width */}
                          <div>
                            <label style={{
                              color: '#475569',
                              fontSize: '14px',
                              fontWeight: '600',
                              marginBottom: '8px',
                              display: 'block',
                              fontFamily: "'Inter', sans-serif"
                            }}>Description</label>
                            <input 
                              type="text" 
                              placeholder="Optional description..."
                              value={expenseFormData[monthId]?.description || ''} 
                              onChange={e => handleExpenseInputChange(monthId, 'description', e.target.value)}
                              style={{
                                width: '100%',
                                padding: '16px 20px',
                                borderRadius: '12px',
                                border: '2px solid #e2e8f0',
                                background: 'white',
                                color: '#1e293b',
                                fontSize: '16px',
                                fontWeight: '500',
                                outline: 'none',
                                transition: 'all 0.3s ease',
                                fontFamily: "'Inter', sans-serif",
                                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                                boxSizing: 'border-box'
                              }}
                              onFocus={(e) => {
                                e.target.style.borderColor = '#6366f1';
                                e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                              }}
                              onBlur={(e) => {
                                e.target.style.borderColor = '#e2e8f0';
                                e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                              }}
                            />
                          </div>
                        </div>

                        <div style={{
                          display: 'flex',
                          gap: '16px',
                          justifyContent: 'flex-end'
                        }}>
                          <button 
                            onClick={() => {
                              setShowExpenseForm(forms => ({ ...forms, [monthId]: false }));
                              setCategoryInput(prev => ({ ...prev, [monthId]: '' }));
                              setShowCategorySuggestions(prev => ({ ...prev, [monthId]: false }));
                            }}
                            style={{
                              background: 'white',
                              border: '2px solid #e2e8f0',
                              borderRadius: '12px',
                              padding: '16px 24px',
                              color: '#475569',
                              fontSize: '16px',
                              fontWeight: '600',
                              cursor: 'pointer',
                              transition: 'all 0.3s ease',
                              fontFamily: "'Inter', sans-serif"
                            }}
                            onMouseOver={(e) => {
                              e.target.style.borderColor = '#cbd5e1';
                              e.target.style.background = '#f8fafc';
                            }}
                            onMouseOut={(e) => {
                              e.target.style.borderColor = '#e2e8f0';
                              e.target.style.background = 'white';
                            }}
                          >
                            Cancel
                          </button>
                          <button 
                            onClick={() => handleExpenseSubmit(monthId)}
                            style={{
                              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                              border: 'none',
                              borderRadius: '12px',
                              padding: '16px 32px',
                              color: 'white',
                              fontSize: '16px',
                              fontWeight: '600',
                              cursor: 'pointer',
                              transition: 'all 0.3s ease',
                              fontFamily: "'Inter', sans-serif",
                              boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
                            }}
                            onMouseOver={(e) => {
                              e.target.style.transform = 'translateY(-2px)';
                              e.target.style.boxShadow = '0 6px 20px rgba(99, 102, 241, 0.4)';
                            }}
                            onMouseOut={(e) => {
                              e.target.style.transform = 'translateY(0)';
                              e.target.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.3)';
                            }}
                          >
                            Save Expense
                          </button>
                        </div>
                      </div>

                      {/* Expenses List */}
                      <div style={{
                        background: 'white',
                        border: '2px solid #e2e8f0',
                        borderRadius: '16px',
                        overflow: 'hidden',
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.02)'
                      }}>
                        <div style={{
                          padding: '24px 32px',
                          background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
                          borderBottom: '2px solid #e2e8f0'
                        }}>
                          <h4 style={{
                            margin: '0',
                            color: '#475569',
                            fontSize: '18px',
                            fontWeight: '700',
                            fontFamily: "'Inter', sans-serif"
                          }}>
                            Current Expenses ({expList.length})
                          </h4>
                        </div>
                        
                        <div style={{ padding: '32px' }}>
                          {expList.length === 0 ? (
                            <div style={{
                              textAlign: 'center',
                              padding: '40px 20px',
                              color: '#94a3b8',
                              fontSize: '16px',
                              fontWeight: '500',
                              fontFamily: "'Inter', sans-serif"
                            }}>
                              No expenses recorded yet
                            </div>
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                              {expList.map((exp, i) => {
                                if (!exp || typeof exp !== 'object') return null;
                                const amountNum = Number(exp.expense_item_price || 0);
                                const fullDescription = exp.expense_description || 'Unknown';
                                const [name, ...descParts] = fullDescription.split(' - ');
                                const description = descParts.join(' - ') || 'No description';
                                const date = exp.expenditure_date ? exp.expenditure_date.split('T')[0] : 'No date';
                                
                                return (
                                  <div 
                                    key={exp.expense_id || i}
                                    style={{
                                      background: 'white',
                                      border: '2px solid #e2e8f0',
                                      borderRadius: '12px',
                                      padding: '20px 24px',
                                      display: 'flex',
                                      justifyContent: 'space-between',
                                      alignItems: 'center',
                                      transition: 'all 0.3s ease',
                                      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)'
                                    }}
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.borderColor = '#cbd5e1';
                                      e.currentTarget.style.transform = 'translateY(-2px)';
                                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.borderColor = '#e2e8f0';
                                      e.currentTarget.style.transform = 'translateY(0)';
                                      e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                                    }}
                                  >
                                    <div style={{ flex: 1 }}>
                                      <div style={{
                                        color: '#1e293b',
                                        fontSize: '18px',
                                        fontWeight: '700',
                                        marginBottom: '4px',
                                        fontFamily: "'Inter', sans-serif"
                                      }}>
                                        {name || 'Unknown'}
                                      </div>
                                      <div style={{
                                        color: '#64748b',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        fontFamily: "'Inter', sans-serif"
                                      }}>
                                        {description} • {date}
                                      </div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                                      <div style={{
                                        color: '#6366f1',
                                        fontSize: '20px',
                                        fontWeight: '700',
                                        textAlign: 'right',
                                        fontFamily: "'Inter', sans-serif"
                                      }}>
                                        ${!isNaN(amountNum) ? amountNum.toFixed(2) : '0.00'}
                                      </div>
                                      <button 
                                        title="Delete expense" 
                                        onClick={() => handleDeleteExpense(monthId, exp.expense_id)}
                                        style={{
                                          width: '36px',
                                          height: '36px',
                                          background: 'white',
                                          color: '#ef4444',
                                          border: '2px solid #fecaca',
                                          borderRadius: '8px',
                                          cursor: 'pointer',
                                          fontSize: '16px',
                                          fontWeight: '600',
                                          display: 'flex',
                                          alignItems: 'center',
                                          justifyContent: 'center',
                                          transition: 'all 0.3s ease',
                                          fontFamily: "'Inter', sans-serif"
                                        }}
                                        onMouseEnter={(e) => {
                                          e.target.style.background = '#ef4444';
                                          e.target.style.color = '#ffffff';
                                          e.target.style.borderColor = '#ef4444';
                                          e.target.style.transform = 'scale(1.05)';
                                        }}
                                        onMouseLeave={(e) => {
                                          e.target.style.background = 'white';
                                          e.target.style.color = '#ef4444';
                                          e.target.style.borderColor = '#fecaca';
                                          e.target.style.transform = 'scale(1)';
                                        }}
                                      >
                                        ×
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
              </div>
            );
          })}
        </div>
      </main>
      
      {/* Category Creation Modal */}
      {showCategoryModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '32px',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
            minWidth: '400px',
            maxWidth: '500px'
          }}>
            <h3 style={{
              margin: '0 0 24px 0',
              fontSize: '24px',
              fontWeight: '700',
              color: '#1e293b',
              fontFamily: "'Inter', sans-serif"
            }}>
              Add New Category
            </h3>
            
            <div style={{ marginBottom: '24px' }}>
              <label style={{
                color: '#475569',
                fontSize: '14px',
                fontWeight: '600',
                marginBottom: '8px',
                display: 'block',
                fontFamily: "'Inter', sans-serif"
              }}>
                Category Name
              </label>
              <input
                type="text"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateTempCategory();
                  } else if (e.key === 'Escape') {
                    setShowCategoryModal(false);
                    setNewCategoryName('');
                  }
                }}
                placeholder="Enter category name..."
                autoFocus
                style={{
                  width: '100%',
                  padding: '16px 20px',
                  borderRadius: '12px',
                  border: '2px solid #e2e8f0',
                  background: 'white',
                  color: '#1e293b',
                  fontSize: '16px',
                  fontWeight: '500',
                  outline: 'none',
                  transition: 'all 0.3s ease',
                  fontFamily: "'Inter', sans-serif",
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#6366f1';
                  e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e2e8f0';
                  e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.02)';
                }}
              />
            </div>
            
            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'flex-end'
            }}>
              <button
                onClick={() => {
                  setShowCategoryModal(false);
                  setNewCategoryName('');
                }}
                style={{
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: '2px solid #e2e8f0',
                  background: 'white',
                  color: '#64748b',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  fontFamily: "'Inter', sans-serif"
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#f8fafc';
                  e.target.style.borderColor = '#cbd5e1';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'white';
                  e.target.style.borderColor = '#e2e8f0';
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTempCategory}
                disabled={!newCategoryName.trim()}
                style={{
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: '2px solid #6366f1',
                  background: newCategoryName.trim() ? '#6366f1' : '#e2e8f0',
                  color: newCategoryName.trim() ? 'white' : '#94a3b8',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: newCategoryName.trim() ? 'pointer' : 'not-allowed',
                  transition: 'all 0.3s ease',
                  fontFamily: "'Inter', sans-serif"
                }}
                onMouseEnter={(e) => {
                  if (newCategoryName.trim()) {
                    e.target.style.backgroundColor = '#5856eb';
                    e.target.style.borderColor = '#5856eb';
                  }
                }}
                onMouseLeave={(e) => {
                  if (newCategoryName.trim()) {
                    e.target.style.backgroundColor = '#6366f1';
                    e.target.style.borderColor = '#6366f1';
                  }
                }}
              >
                Add Category
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Category Delete Confirmation Modal */}
      {showDeleteModal && categoryToDelete && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '32px',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
            minWidth: '400px',
            maxWidth: '500px'
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              fontSize: '24px',
              fontWeight: '700',
              color: '#dc2626',
              fontFamily: "'Inter', sans-serif",
              display: 'flex',
              alignItems: 'center'
            }}>
              <span style={{
                fontSize: '28px',
                marginRight: '12px'
              }}>⚠️</span>
              Delete Category
            </h3>
            
            <p style={{
              margin: '0 0 24px 0',
              fontSize: '16px',
              color: '#475569',
              lineHeight: '1.6',
              fontFamily: "'Inter', sans-serif"
            }}>
              Are you sure you want to delete the category{' '}
              <span style={{
                fontWeight: '600',
                color: '#1e293b'
              }}>
                "{categoryToDelete.name}"
              </span>?
              <br />
              <span style={{
                fontSize: '14px',
                color: '#64748b',
                marginTop: '8px',
                display: 'block'
              }}>
                This action cannot be undone.
              </span>
            </p>
            
            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'flex-end'
            }}>
              <button
                onClick={cancelDeleteCategory}
                style={{
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: '2px solid #e2e8f0',
                  background: 'white',
                  color: '#64748b',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  fontFamily: "'Inter', sans-serif"
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#f8fafc';
                  e.target.style.borderColor = '#cbd5e1';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'white';
                  e.target.style.borderColor = '#e2e8f0';
                }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteCategory}
                style={{
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: '2px solid #dc2626',
                  background: '#dc2626',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  fontFamily: "'Inter', sans-serif"
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#b91c1c';
                  e.target.style.borderColor = '#b91c1c';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = '#dc2626';
                  e.target.style.borderColor = '#dc2626';
                }}
              >
                Delete Category
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
}

export default App;
