// src/components/Navbar.js
import React, { useState } from 'react';
import './Navbar.css';

function Navbar() {
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifications] = useState(3);

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <div className="navbar-logo">
          <div className="logo-icon">
            <i className="fas fa-rocket"></i>
          </div>
          <div className="logo-text">
            <h1>AI<span>Marketer</span></h1>
            <p>Intelligent Campaign Automation</p>
          </div>
        </div>

        {/* Search Bar */}
        <div className={`navbar-search ${searchOpen ? 'active' : ''}`}>
          <i className="fas fa-search"></i>
          <input 
            type="text" 
            placeholder="Ask AI anything about your campaigns..."
            onFocus={() => setSearchOpen(true)}
            onBlur={() => setSearchOpen(false)}
          />
        </div>

        {/* Navigation Items */}
        <div className="navbar-menu">
          <div className="nav-item">
            <i className="fas fa-chart-line"></i>
            <span>Analytics</span>
          </div>
          <div className="nav-item">
            <i className="fas fa-bullseye"></i>
            <span>Campaigns</span>
            <span className="badge">12</span>
          </div>
          <div className="nav-item">
            <i className="fas fa-users"></i>
            <span>Audience</span>
          </div>

          {/* Notifications */}
          <div className="nav-item notification-bell">
            <i className="fas fa-bell"></i>
            {notifications > 0 && (
              <span className="notification-count">{notifications}</span>
            )}
          </div>

          {/* User Profile */}
          <div className="user-profile">
            <div className="avatar">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=John" alt="User" />
              <span className="status online"></span>
            </div>
            <div className="user-info">
              <p className="user-name">John Marketing</p>
              <p className="user-role">Premium User</p>
            </div>
            <i className="fas fa-chevron-down"></i>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;