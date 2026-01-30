// src/components/AnalyticsChart.js
import React from 'react';
import './AnalyticsChart.css';

function AnalyticsChart() {
  const data = [
    { month: 'Jan', revenue: 4000, clicks: 2400, conversions: 240 },
    { month: 'Feb', revenue: 3000, clicks: 1398, conversions: 221 },
    { month: 'Mar', revenue: 9800, clicks: 2000, conversions: 229 },
    { month: 'Apr', revenue: 3908, clicks: 2780, conversions: 200 },
    { month: 'May', revenue: 4800, clicks: 1890, conversions: 218 },
    { month: 'Jun', revenue: 3800, clicks: 2390, conversions: 250 },
    { month: 'Jul', revenue: 4300, clicks: 3490, conversions: 210 },
  ];

  const maxValue = Math.max(...data.map(d => Math.max(d.revenue, d.clicks, d.conversions * 20)));

  return (
    <div className="analytics-card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Performance Analytics</h2>
          <p className="card-subtitle">Last 7 months overview</p>
        </div>
        <div className="time-filters">
          <button className="time-filter active">Monthly</button>
          <button className="time-filter">Quarterly</button>
          <button className="time-filter">Yearly</button>
        </div>
      </div>

      <div className="chart-container">
        <div className="chart-y-axis">
          {[0, 2500, 5000, 7500, 10000].map(value => (
            <div key={value} className="y-tick">
              <span className="y-label">${value.toLocaleString()}</span>
            </div>
          ))}
        </div>
        
        <div className="chart-bars">
          {data.map((item, index) => (
            <div key={index} className="chart-column">
              <div className="column-group">
                <div 
                  className="bar revenue-bar" 
                  style={{ height: `${(item.revenue / maxValue) * 100}%` }}
                  title={`Revenue: $${item.revenue}`}
                >
                  <div className="bar-tooltip">${item.revenue}</div>
                </div>
                <div 
                  className="bar clicks-bar" 
                  style={{ height: `${(item.clicks / maxValue) * 100}%` }}
                  title={`Clicks: ${item.clicks}`}
                >
                  <div className="bar-tooltip">{item.clicks} clicks</div>
                </div>
              </div>
              <div className="x-label">{item.month}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="chart-legend">
        <div className="legend-item">
          <div className="legend-color revenue"></div>
          <span>Revenue ($)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color clicks"></div>
          <span>Clicks</span>
        </div>
        <div className="legend-item">
          <div className="legend-color conversions"></div>
          <span>Conversions</span>
        </div>
      </div>
    </div>
  );
}

export default AnalyticsChart;