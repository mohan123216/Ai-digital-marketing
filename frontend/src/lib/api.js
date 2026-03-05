const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
};
