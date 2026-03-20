export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const request = async (path, token, options = {}) => {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
};

export const api = {
  signup: (payload) =>
    request("/api/v1/auth/signup", null, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: (payload) =>
    request("/api/v1/auth/login", null, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getMe: (token) => request("/api/v1/me", token),
  getInsights: () => request("/api/v1/insights"),
  getSegments: () => request("/api/v1/segments"),
  getProductTypes: () => request("/api/v1/product-types"),
  getHistory: (token) => request("/api/v1/history", token),
  createRecommendation: (token, payload) =>
    request("/api/v1/recommendations", token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  launchGoogleAds: (token, payload) =>
    request("/api/v1/google-ads/launch", token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  launchMetaAds: (token, payload) =>
    request("/api/v1/meta-ads/launch", token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getGoogleAdsLaunchStatus: (token, payload) =>
    request("/api/v1/google-ads/launch-status", token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getMetaAdsLaunchStatus: (token, payload) =>
    request("/api/v1/meta-ads/launch-status", token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  // ── Ads (launch ads inside campaigns) ──────────────────────────────────
  launchAd: (token, campaignRunId, payload) =>
    request(`/api/v1/google-ads/campaigns/${campaignRunId}/ads`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getAds: (token, campaignRunId) =>
    request(`/api/v1/google-ads/campaigns/${campaignRunId}/ads`, token),
  getCampaignMetrics: (token, campaignRunId) =>
    request(`/api/v1/google-ads/campaigns/${campaignRunId}/metrics`, token),
  getMetaCampaignMetrics: (token, campaignRunId, platform = "") => {
    const qp = platform ? `?platform=${encodeURIComponent(platform)}` : "";
    return request(`/api/v1/meta-ads/campaigns/${campaignRunId}/metrics${qp}`, token);
  },

  // Upload image or video ad (multipart/form-data)
  launchMediaAd: async (token, campaignRunId, formData) => {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const response = await fetch(
      `${API_BASE_URL}/api/v1/google-ads/campaigns/${campaignRunId}/ads/media`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }, // NO Content-Type – browser sets it with boundary
        body: formData,
      }
    );
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `Upload failed with status ${response.status}`);
    }
    return response.json();
  },
  // ── Optimization Agent (Google Ads) ─────────────────────────────────────────
  optimizeCampaign: (token, campaignRunId, dryRun = false, useMockData = false, userOverrides = null) =>
    request(`/api/v1/google-ads/campaigns/${campaignRunId}/optimize`, token, {
      method: "POST",
      body: JSON.stringify({
        campaign_run_id: campaignRunId,
        platform: "Google Ads",
        dry_run: dryRun,
        use_mock_data: useMockData,
        user_overrides: userOverrides,
      }),
    }),
  // ── Optimization Agent (Meta Ads) ────────────────────────────────────────────
  optimizeMetaCampaign: (token, campaignRunId, dryRun = false, useMockData = false, userOverrides = null) =>
    request(`/api/v1/meta-ads/campaigns/${campaignRunId}/optimize`, token, {
      method: "POST",
      body: JSON.stringify({
        campaign_run_id: campaignRunId,
        dry_run: dryRun,
        use_mock_data: useMockData,
        user_overrides: userOverrides,
      }),
    }),
};
