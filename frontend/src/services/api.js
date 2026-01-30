const API_BASE_URL = 'http://localhost:8000';

export const campaignAPI = {
  // ==================== CAMPAIGN ENDPOINTS ====================
  
  async createCampaign(campaignData) {
    console.log('📤 Creating campaign:', campaignData);
    
    const response = await fetch(`${API_BASE_URL}/api/campaigns`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(campaignData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create campaign');
    }
    
    const result = await response.json();
    console.log('✅ Campaign created:', result);
    return result;
  },
  
  async getAllCampaigns() {
    console.log('📤 Fetching all campaigns');
    
    const response = await fetch(`${API_BASE_URL}/api/campaigns`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch campaigns');
    }
    
    const result = await response.json();
    console.log('✅ Campaigns fetched:', result);
    return result;
  },
  
  async getCampaignById(campaignId) {
    console.log('📤 Fetching campaign:', campaignId);
    
    const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch campaign');
    }
    
    const result = await response.json();
    console.log('✅ Campaign details:', result);
    return result;
  },
  
  async updateCampaign(campaignId, campaignData) {
    console.log('📤 Updating campaign:', campaignId, campaignData);
    
    const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(campaignData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update campaign');
    }
    
    const result = await response.json();
    console.log('✅ Campaign updated:', result);
    return result;
  },
  
  async deleteCampaign(campaignId) {
    console.log('📤 Deleting campaign:', campaignId);
    
    const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete campaign');
    }
    
    const result = await response.json();
    console.log('✅ Campaign deleted:', result);
    return result;
  },
  
  async launchCampaign(campaignId) {
    console.log('📤 Launching campaign:', campaignId);
    
    const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}/launch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to launch campaign');
    }
    
    const result = await response.json();
    console.log('✅ Campaign launched:', result);
    return result;
  },
  
  // ==================== AI ENDPOINTS ====================
  
  async getAISuggestions(campaignId) {
    console.log('📤 Getting AI suggestions for campaign:', campaignId);
    
    const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}/ai-suggestions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get AI suggestions');
    }
    
    const result = await response.json();
    console.log('✅ AI suggestions received:', result);
    return result;
  }
};