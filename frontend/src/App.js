// src/App.js
import React, { useEffect, useState } from 'react';
import './styles/App.css';
import Navbar from './components/Navbar';
import StatsCards from './components/StatsCards';
import AnalyticsChart from './components/AnalyticsChart';
import CampaignWizard from './components/CampaignWizard';
import AIRecommendations from './components/AIRecommendations';
import AuthPage from './components/AuthPage';
import { authAPI } from './services/api';

function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setAuthLoading(false);
      return;
    }

    authAPI.getMe()
      .then((result) => {
        if (result?.user) {
          setUser(result.user);
        }
      })
      .catch(() => {
        localStorage.removeItem('auth_token');
        setUser(null);
      })
      .finally(() => {
        setAuthLoading(false);
      });
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  if (authLoading) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-card">
          <i className="fas fa-circle-notch fa-spin"></i>
          <p>Loading your workspace...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage onAuthSuccess={setUser} />;
  }

  return (
    <div className="App">
      <Navbar user={user} onLogout={handleLogout} />
      
      <main className="main-content">
        <div className="container">
          {/* Welcome Section */}
          <div className="welcome-section">
            <h1>Welcome back, <span className="gradient-text">{user.name || user.email}</span> 👋</h1>
            <p className="subtitle">Here's what's happening with your campaigns today</p>
          </div>

          {/* Stats Cards */}
          <StatsCards />

          {/* Main Content Grid */}
          <div className="content-grid">
            <div className="main-column">
              <AnalyticsChart />
              <CampaignWizard />
            </div>
            
            <div className="sidebar-column">
              <AIRecommendations />
              
              {/* Quick Stats Widget */}
              <div className="quick-stats-widget">
                <div className="widget-header">
                  <h3>Quick Stats</h3>
                  <i className="fas fa-sync-alt"></i>
                </div>
                <div className="stats-list">
                  <div className="stat-item">
                    <span className="stat-label">CTR</span>
                    <span className="stat-value positive">2.8%</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">CPC</span>
                    <span className="stat-value negative">$1.45</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">ROAS</span>
                    <span className="stat-value positive">4.2x</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">CPA</span>
                    <span className="stat-value positive">$24.50</span>
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="recent-activity">
                <div className="widget-header">
                  <h3>Recent Activity</h3>
                  <button className="view-all">View All</button>
                </div>
                <div className="activity-list">
                  <div className="activity-item">
                    <div className="activity-icon success">
                      <i className="fas fa-check"></i>
                    </div>
                    <div className="activity-content">
                      <p>Campaign "Summer Sale" launched successfully</p>
                      <span className="activity-time">2 min ago</span>
                    </div>
                  </div>
                  <div className="activity-item">
                    <div className="activity-icon warning">
                      <i className="fas fa-exclamation"></i>
                    </div>
                    <div className="activity-content">
                      <p>CTR dropped by 15% on Facebook Ads</p>
                      <span className="activity-time">1 hour ago</span>
                    </div>
                  </div>
                  <div className="activity-item">
                    <div className="activity-icon info">
                      <i className="fas fa-lightbulb"></i>
                    </div>
                    <div className="activity-content">
                      <p>AI suggestion: Increase budget for performing campaigns</p>
                      <span className="activity-time">3 hours ago</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* AI Chat Assistant */}
      <div className="ai-assistant">
        <button className="assistant-toggle">
          <i className="fas fa-robot"></i>
        </button>
      </div>
    </div>
  );
}

export default App;