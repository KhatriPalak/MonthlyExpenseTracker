import React, { useEffect } from 'react';

const AuthCallback = ({ onLogin }) => {
  useEffect(() => {
    // This effect runs once when the component mounts
    try {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('token');
      const userString = params.get('user');

      if (token && userString) {
        console.log('AuthCallback: Found token and user data in URL.');
        
        // Parse the user JSON string
        const user = JSON.parse(userString);

        // Store the token and user data in localStorage
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        console.log('AuthCallback: Saved token and user data to localStorage.');

        // Call the onLogin function passed from App.js to update the parent state
        onLogin(user);

        // Redirect to the main application page
        // Using window.location.replace so the callback URL isn't in the browser history
        window.location.replace('/');

      } else {
        console.error('AuthCallback: Token or user data not found in URL.');
        // Redirect to login page on failure
        window.location.replace('/');
      }
    } catch (error) {
      console.error('AuthCallback: Error processing auth callback:', error);
      // Redirect to login page on error
      window.location.replace('/');
    }
  }, [onLogin]); // The effect depends on the onLogin function

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div>Signing you in...</div>
    </div>
  );
};

export default AuthCallback;