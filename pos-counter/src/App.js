import React, { useState } from 'react';
import './App.css';

export default function App() {
  const [screen, setScreen] = useState('login');
  const [username, setUsername] = useState('cashier1');
  const [password, setPassword] = useState('demo123');
  const [loginError, setLoginError] = useState('');
  const [token, setToken] = useState(null);
  const [userData, setUserData] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8001/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      setToken(data.access_token);
      setUserData(data.user);
      setScreen('pos');
    } catch (error) {
      setLoginError('Connection error or invalid credentials');
    }
  };

  if (!token) {
    return (
      <div className="login-container">
        <div className="login-card">
          <h1>🏥 PharmSecure POS</h1>
          <h2>Point of Service System</h2>
          
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="cashier1"
              />
            </div>
            
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            
            {loginError && <div className="error">{loginError}</div>}
            
            <button type="submit" className="btn-primary">LOGIN</button>
          </form>
          
          <div className="demo-info">
            <p>Demo: cashier1 / demo123</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pos-container">
      <header className="pos-header">
        <h1>PharmSecure POS</h1>
        <div className="user-info">
          <span>{userData?.full_name || username}</span>
          <button 
            onClick={() => { setToken(null); setScreen('login'); }}
            className="btn-logout"
          >
            Logout
          </button>
        </div>
      </header>
      
      <div className="pos-content">
        <h2>Welcome to PharmSecure POS!</h2>
        <p>✅ Login successful!</p>
        <p>API is connected and ready.</p>
        <p>User: {userData?.username}</p>
        <p>Branch: {userData?.branch_id}</p>
      </div>
    </div>
  );
}
