import React, { useEffect, useState } from 'react';

import { API_CONFIG, buildUrl } from './config/api';
const ExpenseTracker = ({ year = 2025, month = new Date().getMonth() + 1, refreshTrigger = 0 }) => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log(`ExpenseTracker: Starting fetch for year=${year}, month=${month}`);
    setLoading(true);
    fetch(buildUrl(API_CONFIG.ENDPOINTS.EXPENSES, { year, month }))
      .then((res) => {
        console.log('ExpenseTracker: Response status:', res.status, res.statusText);
        console.log('ExpenseTracker: Response headers:', [...res.headers.entries()]);
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then((data) => {
        console.log('ExpenseTracker: Received data:', data);
        console.log('ExpenseTracker: Data type:', typeof data, 'Is array:', Array.isArray(data));
        setExpenses(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('ExpenseTracker: Fetch error:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [year, month, refreshTrigger]);

  if (loading) return <div>Loading expenses...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Expenses</h2>
      {expenses.length === 0 ? (
        <div>No expenses found.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>User ID</th>
              <th>Category</th>
              <th>Price</th>
              <th>Date</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {(Array.isArray(expenses) ? expenses : []).filter(Boolean).map((expense) => {
              if (!expense || typeof expense !== 'object') return null;
              let priceNum = 0;
              if (
                expense.hasOwnProperty('expense_item_price') &&
                expense.expense_item_price !== null &&
                expense.expense_item_price !== undefined &&
                !isNaN(Number(expense.expense_item_price))
              ) {
                priceNum = Number(expense.expense_item_price);
              }
              return (
                <tr key={expense.expense_id ?? Math.random()}>
                  <td>{expense?.expense_id ?? '-'}</td>
                  <td>{expense?.user_id ?? '-'}</td>
                  <td>{expense?.expense_category_id ?? '-'}</td>
                  <td>{priceNum.toFixed(2)}</td>
                  <td>{expense?.expenditure_date ? expense.expenditure_date.split('T')[0] : '-'}</td>
                  <td>{expense?.expense_description ?? '-'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ExpenseTracker;
