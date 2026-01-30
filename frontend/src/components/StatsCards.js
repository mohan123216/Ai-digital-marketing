// src/components/StatsCards.js
import React from 'react';
import './StatsCards.css';

function StatsCards() {
  const statsData = [
    {
      id: 1,
      title: "Total Revenue",
      value: "$124,580",
      change: "+24.5%",
      trend: "up",
      icon: "fas fa-chart-line",
      color: "linear-gradient(135deg, #4cc9f0, #4361ee)",
      progress: 78
    },
    {
      id: 2,
      title: "Active Campaigns",
      value: "12",
      change: "+3 new",
      trend: "up",
      icon: "fas fa-bullseye",
      color: "linear-gradient(135deg, #f72585, #7209b7)",
      progress: 65
    },
    {
      id: 3,
      title: "Total Clicks",
      value: "45.2K",
      change: "+18.2%",
      trend: "up",
      icon: "fas fa-mouse-pointer",
      color: "linear-gradient(135deg, #f8961e, #f94144)",
      progress: 82
    },
    {
      id: 4,
      title: "Audience Reach",
      value: "1.2M",
      change: "+12.4%",
      trend: "up",
      icon: "fas fa-users",
      color: "linear-gradient(135deg, #7209b7, #4361ee)",
      progress: 92
    }
  ];

  return (
    <div className="stats-grid">
      {statsData.map((stat) => (
        <div key={stat.id} className="stat-card" style={{animationDelay: `${stat.id * 0.1}s`}}>
          <div className="stat-header">
            <div className="stat-icon" style={{background: stat.color}}>
              <i className={stat.icon}></i>
            </div>
            <div className="stat-trend">
              <span className={`trend-indicator ${stat.trend}`}>
                <i className={`fas fa-arrow-${stat.trend}`}></i>
                {stat.change}
              </span>
            </div>
          </div>
          
          <div className="stat-content">
            <h3 className="stat-value">{stat.value}</h3>
            <p className="stat-title">{stat.title}</p>
          </div>
          
          <div className="stat-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ 
                  background: stat.color,
                  width: `${stat.progress}%`
                }}
              ></div>
            </div>
            <span className="progress-label">{stat.progress}% of target</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default StatsCards;