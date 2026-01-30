// src/components/CampaignWizard.js
import React, { useState, useEffect } from 'react';
import { campaignAPI } from '../services/api';
import './CampaignWizard.css';

function CampaignWizard() {
  const [showWizard, setShowWizard] = useState(true);
  const [currentStep, setCurrentStep] = useState(1);
  const [productName, setProductName] = useState('');
  const [productType, setProductType] = useState('');
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [campaignData, setCampaignData] = useState({
    goal: '',
    budget: '',
    audience: {
      age: { min: 18, max: 65 },
      gender: ['male', 'female'],
      interests: [],
      location: '',
      income: 'all'
    },
    platforms: [],
    duration: 30
  });
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Fetch campaigns from database on component mount
  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const result = await campaignAPI.getAllCampaigns();
      if (result.success) {
        setCampaigns(result.campaigns || []);
        console.log('✅ Campaigns loaded:', result.campaigns);
      }
    } catch (error) {
      console.error('❌ Error fetching campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const goals = [
    { id: 1, title: 'Brand Awareness', icon: 'fas fa-bullhorn', color: '#4361ee', description: 'Increase visibility and brand recognition' },
    { id: 2, title: 'Lead Generation', icon: 'fas fa-users', color: '#7209b7', description: 'Collect contact information for sales' },
    { id: 3, title: 'Sales Conversion', icon: 'fas fa-shopping-cart', color: '#f72585', description: 'Drive direct product sales' },
    { id: 4, title: 'Website Traffic', icon: 'fas fa-globe', color: '#4cc9f0', description: 'Increase visits to your website' },
    { id: 5, title: 'App Installs', icon: 'fas fa-mobile-alt', color: '#f8961e', description: 'Drive mobile app installations' },
    { id: 6, title: 'Event Registration', icon: 'fas fa-calendar-alt', color: '#f94144', description: 'Register people for events/webinars' }
  ];

  const platforms = [
    { id: 1, name: 'Facebook', icon: 'fab fa-facebook', color: '#1877f2', audience: '2.9B' },
    { id: 2, name: 'Instagram', icon: 'fab fa-instagram', color: '#e4405f', audience: '2.0B' },
    { id: 3, name: 'Google Ads', icon: 'fab fa-google', color: '#4285f4', audience: 'Search Users' },
    { id: 4, name: 'LinkedIn', icon: 'fab fa-linkedin', color: '#0a66c2', audience: '930M' },
    { id: 5, name: 'Twitter', icon: 'fab fa-twitter', color: '#1da1f2', audience: '450M' },
    { id: 6, name: 'TikTok', icon: 'fab fa-tiktok', color: '#000000', audience: '1.8B' }
  ];

  const interests = [
    'Technology', 'Sports', 'Fashion', 'Travel', 'Food & Dining', 'Health & Fitness',
    'Music', 'Movies', 'Gaming', 'Business', 'Education', 'Home & Garden',
    'Automotive', 'Parenting', 'Beauty', 'Finance', 'Art & Design', 'Photography'
  ];

  const incomeLevels = [
    { value: 'all', label: 'All Income Levels' },
    { value: 'low', label: 'Low Income (<$30k)' },
    { value: 'middle', label: 'Middle Income ($30k-$100k)' },
    { value: 'high', label: 'High Income (>$100k)' }
  ];

  const steps = [
    { number: 1, label: 'Product', icon: 'fas fa-box' },
    { number: 2, label: 'Goal', icon: 'fas fa-bullseye' },
    { number: 3, label: 'Budget', icon: 'fas fa-dollar-sign' },
    { number: 4, label: 'Audience', icon: 'fas fa-users' },
    { number: 5, label: 'Platforms', icon: 'fas fa-globe' },
    { number: 6, label: 'Duration', icon: 'fas fa-calendar' }
  ];

  const handleNext = () => {
    if (currentStep < 6) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGoalSelect = (goal) => {
    setCampaignData({...campaignData, goal});
  };

  const handlePlatformToggle = (platform) => {
    setCampaignData(prev => {
      const platforms = [...prev.platforms];
      if (platforms.includes(platform)) {
        return {...prev, platforms: platforms.filter(p => p !== platform)};
      } else {
        return {...prev, platforms: [...platforms, platform]};
      }
    });
  };

  const handleInterestToggle = (interest) => {
    setCampaignData(prev => {
      const interests = [...prev.audience.interests];
      if (interests.includes(interest)) {
        return {
          ...prev,
          audience: {
            ...prev.audience,
            interests: interests.filter(i => i !== interest)
          }
        };
      } else {
        return {
          ...prev,
          audience: {
            ...prev.audience,
            interests: [...interests, interest]
          }
        };
      }
    });
  };

  const handleGenderToggle = (gender) => {
    setCampaignData(prev => {
      const genders = [...prev.audience.gender];
      if (genders.includes(gender)) {
        return {
          ...prev,
          audience: {
            ...prev.audience,
            gender: genders.filter(g => g !== gender)
          }
        };
      } else {
        return {
          ...prev,
          audience: {
            ...prev.audience,
            gender: [...genders, gender]
          }
        };
      }
    });
  };

  const handleAgeChange = (type, value) => {
    setCampaignData(prev => ({
      ...prev,
      audience: {
        ...prev.audience,
        age: {
          ...prev.audience.age,
          [type]: parseInt(value) || 18
        }
      }
    }));
  };

  const handleLocationChange = (value) => {
    setCampaignData(prev => ({
      ...prev,
      audience: {
        ...prev.audience,
        location: value
      }
    }));
  };

  const handleIncomeChange = (value) => {
    setCampaignData(prev => ({
      ...prev,
      audience: {
        ...prev.audience,
        income: value
      }
    }));
  };

  const handleDurationChange = (days) => {
    setCampaignData({...campaignData, duration: days});
  };

  // Check if all required fields are filled
  const isFormComplete = () => {
    return (
      productName &&
      productType &&
      campaignData.goal &&
      campaignData.budget &&
      campaignData.audience.interests.length > 0 &&
      campaignData.platforms.length > 0 &&
      campaignData.duration > 0
    );
  };

  // Get AI suggestions - two step process: create campaign then get suggestions
  const getAISuggestions = async () => {
    console.log('🔄 Getting AI suggestions...');
    console.log('📋 Campaign Data:', campaignData);
    
    try {
      setLoading(true);
      
      // Step 1: Create campaign
      console.log('Step 1: Creating campaign...');
      const createResponse = await campaignAPI.createCampaign(campaignData);
      const campaignId = createResponse.campaign_id;
      console.log('✅ Campaign created with ID:', campaignId);
      
      // Step 2: Get AI suggestions
      console.log('Step 2: Getting AI suggestions...');
      const suggestionsResponse = await campaignAPI.getAISuggestions(campaignId);
      console.log('✅ AI suggestions:', suggestionsResponse);
      
      // Store suggestions and display
      setAiSuggestions(suggestionsResponse.recommendations || []);
      setShowSuggestions(true);
      
      // Show success message
      alert('✅ Campaign created and AI suggestions generated!');
      
    } catch (error) {
      console.error('❌ Error:', error);
      alert(`Error: ${error.message}. Check console for details.`);
    } finally {
      setLoading(false);
    }
  };

  const launchCampaign = async () => {
    // Create a new campaign with all the data
    try {
      setLoading(true);
      
      const campaignPayload = {
        productName,
        productType,
        goal: campaignData.goal,
        budget: parseFloat(campaignData.budget),
        duration: campaignData.duration,
        audience: campaignData.audience,
        platforms: campaignData.platforms
      };
      
      console.log('📤 Sending campaign to backend:', campaignPayload);
      const result = await campaignAPI.createCampaign(campaignPayload);
      
      if (result.success) {
        alert('✅ Campaign created successfully!');
        
        // Reset form
        setProductName('');
        setProductType('');
        setCampaignData({
          goal: '',
          budget: '',
          audience: {
            age: { min: 18, max: 65 },
            gender: ['male', 'female'],
            interests: [],
            location: '',
            income: 'all'
          },
          platforms: [],
          duration: 30
        });
        setCurrentStep(1);
        setAiSuggestions(null);
        setShowSuggestions(false);
        setShowWizard(false);
        
        // Refresh campaigns list
        await fetchCampaigns();
      }
    } catch (error) {
      console.error('❌ Error creating campaign:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="campaign-wizard-container">
      {/* Create Campaign Section */}
      <div className={`campaign-wizard ${!showWizard ? 'collapsed' : ''}`}>
        <div className="wizard-header">
          <h2>Create New Campaign</h2>
          <p>Build your marketing campaign with AI insights</p>
        </div>

        {/* Product Information - Step 1 */}
        {currentStep === 1 && (
          <div className="step-content product-step">
            <h3>Product Information</h3>
            <p className="step-description">Tell us about your product first</p>
            
            <div className="product-inputs">
              <div className="form-group">
                <label htmlFor="productName">
                  <i className="fas fa-box"></i> Product Name
                </label>
                <input
                  id="productName"
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g., Nike Air Max Shoes"
                  className="input-field"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="productType">
                  <i className="fas fa-tag"></i> Product Type
                </label>
                <select
                  id="productType"
                  value={productType}
                  onChange={(e) => setProductType(e.target.value)}
                  className="input-field select-field"
                >
                  <option value="">Select a product type</option>
                  <option value="Electronics">Electronics</option>
                  <option value="Clothing">Clothing & Fashion</option>
                  <option value="Food & Beverage">Food & Beverage</option>
                  <option value="Health & Beauty">Health & Beauty</option>
                  <option value="Home & Garden">Home & Garden</option>
                  <option value="Sports & Outdoors">Sports & Outdoors</option>
                  <option value="Books & Media">Books & Media</option>
                  <option value="Automotive">Automotive</option>
                  <option value="Services">Services</option>
                  <option value="Software">Software</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            
            <div className="product-display">
              <h4>Preview</h4>
              <div className="preview-card">
                <div className="preview-content">
                  {productName ? (
                    <>
                      <h5>{productName}</h5>
                      <p>{productType || 'Product type not selected'}</p>
                    </>
                  ) : (
                    <p className="placeholder">Fill in the details above to see preview</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Progress Steps */}
        {currentStep > 1 && (
          <div className="progress-steps">
            {steps.map(step => (
              <div key={step.number} className={`step ${currentStep >= step.number ? 'active' : ''}`}>
                <div className="step-circle">
                  {currentStep > step.number ? (
                    <i className="fas fa-check"></i>
                  ) : (
                    <i className={step.icon}></i>
                  )}
                </div>
                <span className="step-label">{step.label}</span>
                {step.number < 6 && <div className="step-line"></div>}
              </div>
            ))}
          </div>
        )}

      {/* Step Content */}
      <div className="wizard-content">
        {currentStep === 2 && (
          <div className="step-content">
            <h3>Select Campaign Goal</h3>
            <p className="step-description">What do you want to achieve with this campaign?</p>
            
            <div className="goal-grid">
              {goals.map(goal => (
                <div 
                  key={goal.id}
                  className={`goal-card ${campaignData.goal === goal.title ? 'selected' : ''}`}
                  onClick={() => handleGoalSelect(goal.title)}
                  style={{ '--goal-color': goal.color }}
                >
                  <div className="goal-icon" style={{background: goal.color}}>
                    <i className={goal.icon}></i>
                  </div>
                  <h4>{goal.title}</h4>
                  <p>{goal.description}</p>
                  {campaignData.goal === goal.title && (
                    <div className="selected-indicator">
                      <i className="fas fa-check"></i>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div className="step-content">
            <h3>Set Your Budget</h3>
            <p className="step-description">How much do you want to invest in this campaign?</p>
            
            <div className="budget-input">
              <div className="currency">$</div>
              <input
                type="number"
                value={campaignData.budget}
                onChange={(e) => setCampaignData({...campaignData, budget: e.target.value})}
                placeholder="Enter amount"
                className="budget-amount"
                min="100"
                step="100"
              />
            </div>
            
            <div className="budget-presets">
              {['$100', '$500', '$1000', '$2500', '$5000', '$10000'].map(preset => (
                <button
                  key={preset}
                  className="budget-preset"
                  onClick={() => setCampaignData({...campaignData, budget: preset.replace('$', '')})}
                >
                  {preset}
                </button>
              ))}
            </div>
            
            <div className="budget-tip">
              <i className="fas fa-lightbulb"></i>
              <span>Recommended minimum: $500 for optimal results</span>
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div className="step-content">
            <h3>Define Target Audience</h3>
            <p className="step-description">Who do you want to reach with your campaign?</p>
            
            <div className="audience-section">
              {/* Age Range */}
              <div className="audience-group">
                <h4>Age Range</h4>
                <div className="age-slider">
                  <div className="age-inputs">
                    <div className="age-input">
                      <label>Min Age</label>
                      <input
                        type="number"
                        value={campaignData.audience.age.min}
                        onChange={(e) => handleAgeChange('min', e.target.value)}
                        min="13"
                        max="65"
                      />
                    </div>
                    <div className="age-input">
                      <label>Max Age</label>
                      <input
                        type="number"
                        value={campaignData.audience.age.max}
                        onChange={(e) => handleAgeChange('max', e.target.value)}
                        min="18"
                        max="75"
                      />
                    </div>
                  </div>
                  <div className="age-range">
                    <div className="range-bar">
                      <div 
                        className="range-fill"
                        style={{
                          left: `${((campaignData.audience.age.min - 13) / (75 - 13)) * 100}%`,
                          width: `${((campaignData.audience.age.max - campaignData.audience.age.min) / (75 - 13)) * 100}%`
                        }}
                      ></div>
                    </div>
                    <div className="range-labels">
                      <span>13</span>
                      <span>25</span>
                      <span>40</span>
                      <span>55</span>
                      <span>75</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Gender */}
              <div className="audience-group">
                <h4>Gender</h4>
                <div className="gender-options">
                  {[
                    { value: 'male', label: 'Male', icon: 'fas fa-mars' },
                    { value: 'female', label: 'Female', icon: 'fas fa-venus' },
                    { value: 'all', label: 'All', icon: 'fas fa-venus-mars' }
                  ].map(gender => (
                    <button
                      key={gender.value}
                      className={`gender-option ${campaignData.audience.gender.includes(gender.value) || gender.value === 'all' ? 'selected' : ''}`}
                      onClick={() => {
                        if (gender.value === 'all') {
                          setCampaignData(prev => ({
                            ...prev,
                            audience: { ...prev.audience, gender: ['male', 'female'] }
                          }));
                        } else {
                          handleGenderToggle(gender.value);
                        }
                      }}
                    >
                      <i className={gender.icon}></i>
                      <span>{gender.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Interests */}
              <div className="audience-group">
                <h4>Interests ({campaignData.audience.interests.length} selected)</h4>
                <div className="interests-grid">
                  {interests.map(interest => (
                    <button
                      key={interest}
                      className={`interest-tag ${campaignData.audience.interests.includes(interest) ? 'selected' : ''}`}
                      onClick={() => handleInterestToggle(interest)}
                    >
                      {interest}
                      {campaignData.audience.interests.includes(interest) && (
                        <i className="fas fa-check"></i>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Location */}
              <div className="audience-group">
                <h4>Location</h4>
                <div className="location-input">
                  <i className="fas fa-map-marker-alt"></i>
                  <input
                    type="text"
                    value={campaignData.audience.location}
                    onChange={(e) => handleLocationChange(e.target.value)}
                    placeholder="Enter country, region, or city"
                  />
                </div>
                <div className="location-presets">
                  <button onClick={() => handleLocationChange('United States')}>USA</button>
                  <button onClick={() => handleLocationChange('Europe')}>Europe</button>
                  <button onClick={() => handleLocationChange('Asia')}>Asia</button>
                  <button onClick={() => handleLocationChange('Global')}>Global</button>
                </div>
              </div>

              {/* Income Level */}
              <div className="audience-group">
                <h4>Income Level</h4>
                <div className="income-options">
                  {incomeLevels.map(level => (
                    <button
                      key={level.value}
                      className={`income-option ${campaignData.audience.income === level.value ? 'selected' : ''}`}
                      onClick={() => handleIncomeChange(level.value)}
                    >
                      {level.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStep === 5 && (
          <div className="step-content">
            <h3>Select Platforms</h3>
            <p className="step-description">Choose where you want to run your ads</p>
            
            <div className="platforms-grid">
              {platforms.map(platform => (
                <div
                  key={platform.id}
                  className={`platform-card ${campaignData.platforms.includes(platform.name) ? 'selected' : ''}`}
                  onClick={() => handlePlatformToggle(platform.name)}
                >
                  <div className="platform-icon" style={{color: platform.color}}>
                    <i className={platform.icon}></i>
                  </div>
                  <h4>{platform.name}</h4>
                  <p>{platform.audience} users</p>
                  {campaignData.platforms.includes(platform.name) && (
                    <div className="selected-check">
                      <i className="fas fa-check-circle"></i>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div className="platform-tip">
              <i className="fas fa-info-circle"></i>
              <span>Select multiple platforms for better reach. Facebook + Instagram work well together.</span>
            </div>
          </div>
        )}

        {currentStep === 6 && (
          <div className="step-content">
            <h3>Campaign Duration</h3>
            <p className="step-description">How long should the campaign run?</p>
            
            <div className="duration-section">
              <div className="duration-input">
                <input
                  type="range"
                  min="1"
                  max="90"
                  value={campaignData.duration}
                  onChange={(e) => handleDurationChange(parseInt(e.target.value))}
                  className="duration-slider"
                />
                <div className="duration-value">
                  <span>{campaignData.duration} days</span>
                </div>
              </div>
              
              <div className="duration-presets">
                {[7, 14, 30, 60, 90].map(days => (
                  <button
                    key={days}
                    className={`duration-preset ${campaignData.duration === days ? 'active' : ''}`}
                    onClick={() => handleDurationChange(days)}
                  >
                    {days} days
                  </button>
                ))}
              </div>
              
              <div className="duration-tips">
                <div className="tip">
                  <i className="fas fa-bolt"></i>
                  <div>
                    <strong>Short-term (1-14 days):</strong> Best for promotions, flash sales, events
                  </div>
                </div>
                <div className="tip">
                  <i className="fas fa-chart-line"></i>
                  <div>
                    <strong>Medium-term (15-30 days):</strong> Good for brand awareness, product launches
                  </div>
                </div>
                <div className="tip">
                  <i className="fas fa-calendar"></i>
                  <div>
                    <strong>Long-term (31-90 days):</strong> Ideal for ongoing brand building, lead generation
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="wizard-navigation">
        <button 
          className="btn-secondary"
          onClick={handlePrev}
          disabled={currentStep === 1}
        >
          <i className="fas fa-arrow-left"></i> Back
        </button>
        
        {currentStep === 6 ? (
          <div className="final-actions">
            <button 
              className="btn-primary create-campaign-btn"
              onClick={launchCampaign}
              disabled={!isFormComplete() || loading}
            >
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i> Creating...
                </>
              ) : (
                <>
                  <i className="fas fa-plus"></i> Create Campaign
                </>
              )}
            </button>
          </div>
        ) : (
          <button 
            className="btn-primary"
            onClick={handleNext}
            disabled={(currentStep === 1 && (!productName || !productType))}
          >
            Continue
            <i className="fas fa-arrow-right"></i>
          </button>
        )}
      </div>
      </div>

      {/* New Campaigns Display Section */}
      <div className="campaigns-display-section">
        <div className="campaigns-header">
          <h2>
            <i className="fas fa-rocket"></i> Your Campaigns
          </h2>
          <p>Manage and launch your marketing campaigns</p>
          <button 
            className="btn-primary add-new-campaign-btn"
            onClick={() => setShowWizard(true)}
          >
            <i className="fas fa-plus"></i> Create New Campaign
          </button>
        </div>

        {campaigns.length === 0 ? (
          <div className="empty-campaigns-state">
            <i className="fas fa-inbox"></i>
            <h3>No campaigns yet</h3>
            <p>Create your first campaign to get started</p>
            <button 
              className="btn-primary"
              onClick={() => setShowWizard(true)}
            >
              <i className="fas fa-rocket"></i> Create First Campaign
            </button>
          </div>
        ) : (
          <div className="campaigns-grid">
            {campaigns.map(campaign => (
              <div key={campaign.id} className="campaign-card">
                <div className="campaign-card-header">
                  <div className="campaign-info">
                    <h3>{campaign.product_name || campaign.productName}</h3>
                    <span className="product-type">{campaign.product_type || campaign.productType}</span>
                  </div>
                  <span className="campaign-date">
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="campaign-details">
                  <div className="detail-row">
                    <span className="label">Goal:</span>
                    <span className="value">{campaign.goal}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Budget:</span>
                    <span className="value">${campaign.budget}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Duration:</span>
                    <span className="value">{campaign.duration || campaign.duration_days} days</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Platforms:</span>
                    <div className="platforms-list">
                      {(campaign.platforms || []).slice(0, 3).map((platform, idx) => (
                        <span key={idx} className="platform-badge">
                          {typeof platform === 'string' ? platform : platform.platform}
                        </span>
                      ))}
                      {(campaign.platforms || []).length > 3 && (
                        <span className="platform-badge more">+{(campaign.platforms || []).length - 3}</span>
                      )}
                    </div>
                  </div>
                  <div className="detail-row">
                    <span className="label">Audience:</span>
                    <span className="value">
                      {campaign.audience && campaign.audience.interests ? campaign.audience.interests.length : 0} interests, 
                      Ages {campaign.audience?.age_min || 18}-{campaign.audience?.age_max || 65}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Status:</span>
                    <span className="value" style={{
                      textTransform: 'capitalize',
                      color: campaign.status === 'active' ? '#10b981' : campaign.status === 'draft' ? '#f59e0b' : '#6b7280'
                    }}>
                      {campaign.status}
                    </span>
                  </div>
                </div>

                <div className="campaign-actions">
                  <button 
                    className="action-btn ai-suggestions-action"
                    onClick={async () => {
                      try {
                        setSelectedCampaign(campaign);
                        setLoading(true);
                        const result = await campaignAPI.getAISuggestions(campaign.id);
                        setAiSuggestions(result);
                        setShowSuggestions(true);
                        console.log('✅ AI suggestions received:', result);
                      } catch (error) {
                        alert(`Error: ${error.message}`);
                      } finally {
                        setLoading(false);
                      }
                    }}
                    disabled={loading}
                  >
                    <i className="fas fa-brain"></i> {loading ? 'Loading...' : 'Get AI Suggestions'}
                  </button>
                  <button 
                    className="action-btn launch-campaign-action"
                    onClick={async () => {
                      try {
                        setLoading(true);
                        const result = await campaignAPI.launchCampaign(campaign.id);
                        if (result.success) {
                          alert(`🚀 Campaign launched successfully!`);
                          await fetchCampaigns();
                        }
                      } catch (error) {
                        alert(`Error: ${error.message}`);
                      } finally {
                        setLoading(false);
                      }
                    }}
                    disabled={campaign.status === 'active'}
                  >
                    <i className="fas fa-rocket"></i> {campaign.status === 'active' ? 'Active' : 'Launch'}
                  </button>
                  <button 
                    className="action-btn edit-campaign-action"
                    onClick={async () => {
                      try {
                        setLoading(true);
                        await campaignAPI.deleteCampaign(campaign.id);
                        await fetchCampaigns();
                        alert('✅ Campaign deleted successfully');
                      } catch (error) {
                        alert(`Error: ${error.message}`);
                      } finally {
                        setLoading(false);
                      }
                    }}
                  >
                    <i className="fas fa-trash"></i> Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* AI SUGGESTIONS MODAL */}
        {showSuggestions && aiSuggestions && (
          <div className="ai-suggestions-modal-overlay">
            <div className="ai-suggestions-modal">
              <div className="modal-header">
                <h2>
                  <i className="fas fa-lightbulb"></i> AI Campaign Suggestions for {selectedCampaign?.product_name}
                </h2>
                <button 
                  className="close-btn"
                  onClick={() => {
                    setShowSuggestions(false);
                    setAiSuggestions(null);
                  }}
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
              <div className="modal-content">
                {aiSuggestions.success ? (
                  <div className="suggestions-content">
                    <div className="suggestions-text">
                      {aiSuggestions.suggestions?.split('\n').map((line, idx) => (
                        <p key={idx}>{line}</p>
                      ))}
                    </div>
                    
                    {aiSuggestions.historical_insights && Object.keys(aiSuggestions.historical_insights).length > 0 && (
                      <div className="historical-insights">
                        <h3>📊 Platform Historical Performance</h3>
                        {Object.entries(aiSuggestions.historical_insights).map(([platform, insights]) => (
                          insights && (
                            <div key={platform} className="insight-card">
                              <h4>{platform}</h4>
                              <div className="insight-metrics">
                                <div className="metric">
                                  <span className="label">Avg Conversion Rate:</span>
                                  <span className="value">{(insights.avg_conversion_rate * 100).toFixed(2)}%</span>
                                </div>
                                <div className="metric">
                                  <span className="label">Avg ROI:</span>
                                  <span className="value">${insights.avg_roi?.toFixed(2) || 'N/A'}</span>
                                </div>
                                <div className="metric">
                                  <span className="label">Avg Engagement:</span>
                                  <span className="value">{insights.avg_engagement_score?.toFixed(2) || 'N/A'}</span>
                                </div>
                                <div className="metric">
                                  <span className="label">Best Duration:</span>
                                  <span className="value">{insights.best_duration}</span>
                                </div>
                              </div>
                            </div>
                          )
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="error-message">
                    <p>❌ Error: {aiSuggestions.error}</p>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button 
                  className="btn-primary"
                  onClick={() => {
                    setShowSuggestions(false);
                    setAiSuggestions(null);
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


export default CampaignWizard;