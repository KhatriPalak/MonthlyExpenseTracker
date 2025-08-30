import React, { useState } from 'react';
import { API_CONFIG } from './config/api';

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    console.log('Login: Form submitted with data:', formData);
    
    if (!formData.email || !formData.password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      console.log('Login: Making POST request to /api/auth/login');
      const response = await fetch(API_CONFIG.ENDPOINTS.LOGIN, {
        method: 'POST',
        headers: API_CONFIG.HEADERS,
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      console.log('Login: Response status:', response.status, response.statusText);
      console.log('Login: Response headers:', [...response.headers.entries()]);
      
      const data = await response.json();
      console.log('Login: Response data:', data);
      
      if (response.ok) {
        console.log('Login: Success! User:', data.user);
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('token', data.token);
        onLogin(data.user);
      } else {
        console.log('Login: Failed with error:', data.error);
        setError(data.error || 'Invalid email or password');
      }
    } catch (err) {
      console.log('Login: Error:', err);
      setError('Unable to connect to server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Welcome Back</h2>
        <p className="auth-subtitle">Login to manage your expenses</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;