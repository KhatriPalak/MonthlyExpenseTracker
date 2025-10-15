import React, { useEffect, useState } from 'react';
import './Auth.css';

// A simple Google G icon using SVG
const GoogleIcon = () => (
  <svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="18px" height="18px" viewBox="0 0 48 48">
    <g>
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
      <path fill="none" d="M0 0h48v48H0z"></path>
    </g>
  </svg>
);

const Login = () => {
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const errorParam = params.get('error');
    if (errorParam === 'mismatching_state') {
      setError('An authentication error occurred. Please try signing in again.');
    }
  }, []);

  const handleGoogleLogin = () => {
    // Construct the full URL for the backend's Google login endpoint.
    // This ensures it works whether you access the frontend via localhost, IP, or a domain name.
    const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const backendUrl = isDevelopment
      ? `${window.location.protocol}//${window.location.hostname}:5002/login/google`
      : `${window.location.protocol}//${window.location.hostname}/login/google`;
    window.location.href = backendUrl;
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">💰 Expense Tracker</h1>
        <h2 className="auth-subtitle">Sign In / Sign Up</h2>
        <p className="auth-description">Use your Google account to continue</p>
        
        {error && <div className="auth-error">{error}</div>}

        <button 
          type="button" 
          className="google-auth-button"
          onClick={handleGoogleLogin}
        >
          <GoogleIcon />
          <span>Sign in with Google</span>
        </button>
      </div>
    </div>
  );
};

export default Login;