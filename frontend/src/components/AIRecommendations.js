// src/components/AIRecommendations.js
import React from 'react';
import './AIRecommendations.css';

function AIRecommendations() {
  const recommendations = [
    {
      id: 1,
      title: 'Increase Facebook Ad Budget',
      description: 'Your Facebook campaigns are performing 45% better than average. Consider increasing budget by 30%.',
      confidence: 92,
      impact: 'High',
      icon: 'fas fa-chart-line',
      color: '#4cc9f0'
    },
    {
      id: 2,
      title: 'Optimize Ad Creatives',
      description: 'CTR decreased by 15% this week. Test new creatives with AI-generated suggestions.',
      confidence: 85,
      impact: 'Medium',
      icon: 'fas fa-paint-brush',
      color: '#f8961e'
    },
    {
      id: 3,
      title: 'Expand Target Audience',
      description: 'Opportunity to reach 250K similar users on Instagram based on lookalike analysis.',
      confidence: 78,
      impact: 'High',
      icon: 'fas fa-users',
      color: '#f72585'
    }
  ];

  return (
    <div className="ai-recommendations">
      <div className="section-header">
        <div className="header-left">
          <div className="ai-icon">
            <i className="fas fa-brain"></i>
          </div>
          <div>
            <h2>AI Recommendations</h2>
            <p>Powered by machine learning algorithms</p>
          </div>
        </div>
        <button className="apply-all-btn">
          <i className="fas fa-bolt"></i> Apply All
        </button>
      </div>

      <div className="recommendations-list">
        {recommendations.map((rec, index) => (
          <div 
            key={rec.id} 
            className="recommendation-card"
            style={{animationDelay: `${index * 0.1}s`}}
          >
            <div className="rec-header">
              <div className="rec-icon" style={{background: rec.color}}>
                <i className={rec.icon}></i>
              </div>
              <div className="rec-title-section">
                <h3>{rec.title}</h3>
                <span className={`impact-badge ${rec.impact.toLowerCase()}`}>
                  {rec.impact} Impact
                </span>
              </div>
            </div>
            
            <p className="rec-description">{rec.description}</p>
            
            <div className="rec-footer">
              <div className="confidence-meter">
                <div className="meter-label">AI Confidence</div>
                <div className="meter-bar">
                  <div 
                    className="meter-fill" 
                    style={{ 
                      width: `${rec.confidence}%`,
                      background: rec.color
                    }}
                  ></div>
                </div>
                <span className="confidence-score">{rec.confidence}%</span>
              </div>
              
              <div className="rec-actions">
                <button className="action-btn learn-more">
                  <i className="fas fa-info-circle"></i> Details
                </button>
                <button className="action-btn apply">
                  <i className="fas fa-check"></i> Apply
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AIRecommendations;