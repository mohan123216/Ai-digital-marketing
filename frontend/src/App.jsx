import { useEffect, useMemo, useState } from "react";
import { api } from "./lib/api";

const TOKEN_KEY = "planner_access_token";

const goalOptions = [
  { value: "roi", label: "Max ROI" },
  { value: "conversions", label: "Conversions" },
  { value: "leads", label: "Lead Generation" },
  { value: "traffic", label: "Website Traffic" },
  { value: "engagement", label: "Engagement" },
  { value: "brand_awareness", label: "Brand Awareness" },
];

const initialCampaign = {
  campaign_goal: "roi",
  product_name: "",
  product_category: "",
  location: "United States",
  gender: "All",
  customer_segment: "",
  budget_min: 2000,
  budget_max: 7000,
  duration_days: 30,
};

const formatDate = (iso) => new Date(iso).toLocaleString();

const formatAudience = (rec) =>
  `${rec?.target_segment || "General"} | ${rec?.target_location || "N/A"} | ${rec?.target_age_group || "N/A"}`;

export default function App() {
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [segments, setSegments] = useState([]);
  const [productTypes, setProductTypes] = useState([]);
  const [insights, setInsights] = useState([]);
  const [campaign, setCampaign] = useState(initialCampaign);
  const [result, setResult] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [loadingAuth, setLoadingAuth] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [planError, setPlanError] = useState("");
  const [launchModal, setLaunchModal] = useState({ open: false, platform: null, status: 'idle' });
  const [launchedKeys, setLaunchedKeys] = useState(new Set());

  useEffect(() => {
    const loadCatalog = async () => {
      try {
        const [segmentsResponse, productTypesResponse, insightsResponse] = await Promise.all([
          api.getSegments(),
          api.getProductTypes(),
          api.getInsights(),
        ]);
        setSegments(segmentsResponse.segments || []);
        setProductTypes(productTypesResponse.product_types || []);
        setInsights(insightsResponse.insights || []);
      } catch (_error) {
        setSegments([]);
        setProductTypes([]);
        setInsights([]);
      }
    };

    loadCatalog();
  }, []);

  useEffect(() => {
    if (!accessToken) {
      setUser(null);
      setHistory([]);
      setLaunchedKeys(new Set());
      return;
    }

    const loadProfileAndHistory = async () => {
      try {
        const [profile, rows] = await Promise.all([api.getMe(accessToken), api.getHistory(accessToken)]);
        setUser(profile);
        setHistory(rows);
        // Rebuild launched keys from DB records on every login/refresh
        const keys = new Set();
        rows.forEach(item => {
          (item.launched_platforms || []).forEach(platform => {
            keys.add(`${item.id}::${platform}`);
          });
        });
        setLaunchedKeys(keys);
      } catch (_error) {
        localStorage.removeItem(TOKEN_KEY);
        setAccessToken("");
      }
    };

    loadProfileAndHistory();
  }, [accessToken]);

  const authTitle = useMemo(
    () => (authMode === "login" ? "Welcome Back" : "Create Account"),
    [authMode]
  );

  const submitAuth = async (event) => {
    event.preventDefault();
    setLoadingAuth(true);
    setAuthError("");

    try {
      if (authMode === "signup" && password !== confirmPassword) {
        throw new Error("Passwords do not match.");
      }

      const payload = { email: email.trim().toLowerCase(), password };
      const response = authMode === "login" ? await api.login(payload) : await api.signup(payload);

      localStorage.setItem(TOKEN_KEY, response.access_token);
      setAccessToken(response.access_token);
      setUser(response.user);
      setPassword("");
      setConfirmPassword("");
    } catch (error) {
      setAuthError(error.message || "Authentication failed.");
    } finally {
      setLoadingAuth(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setAccessToken("");
    setUser(null);
    setHistory([]);
    setResult(null);
    setCampaign(initialCampaign);
  };

  const loadHistoryItem = (item) => {
    // When an item is selected from history, repopulate the input values exactly as they were initially provided
    const previousInput = item.output?.campaign_input || {};
    setCampaign({
      ...initialCampaign,
      campaign_goal: item.campaign_goal || initialCampaign.campaign_goal,
      product_name: item.product_name || initialCampaign.product_name,
      budget_min: item.budget_min || previousInput.budget_range?.min || initialCampaign.budget_min,
      budget_max: item.budget_max || previousInput.budget_range?.max || initialCampaign.budget_max,
      product_category: previousInput.product_category || initialCampaign.product_category,
      location: previousInput.target_audience?.location || initialCampaign.location,
      gender: previousInput.target_audience?.gender || initialCampaign.gender,
      customer_segment: previousInput.target_audience?.customer_segment || initialCampaign.customer_segment,
      duration_days: previousInput.duration_days || initialCampaign.duration_days,
    });
    setResult({ ...item.output, id: item.id });
    // Restore the launched state for this specific history item
    const platformsLaunched = item.launched_platforms || [];
    // Keep all existing keys but ensure this item's platforms are represented
    setLaunchedKeys(prev => {
      const next = new Set(prev);
      platformsLaunched.forEach(platform => next.add(`${item.id}::${platform}`));
      return next;
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const generatePlan = async (event) => {
    event.preventDefault();
    if (!accessToken) return;

    if (Number(campaign.budget_min) > Number(campaign.budget_max)) {
      setPlanError("Minimum budget cannot exceed maximum budget.");
      return;
    }

    setLoadingPlan(true);
    setPlanError("");

    const payload = {
      campaign_goal: campaign.campaign_goal,
      product_name: campaign.product_name,
      product_category: campaign.product_category || null,
      target_audience: {
        location: campaign.location,
        gender: campaign.gender,
        interests: [],
        customer_segment: campaign.customer_segment || null,
      },
      budget_range: {
        min: Number(campaign.budget_min),
        max: Number(campaign.budget_max),
      },
      duration_days: Number(campaign.duration_days),
      start_date: new Date().toISOString().split("T")[0],
    };

    try {
      const recommendation = await api.createRecommendation(accessToken, payload);
      const rows = await api.getHistory(accessToken);
      setHistory(rows);

      // Rebuild launchedKeys from fresh DB history
      const keys = new Set();
      rows.forEach(item => {
        (item.launched_platforms || []).forEach(platform => {
          keys.add(`${item.id}::${platform}`);
        });
      });
      setLaunchedKeys(keys);

      // Find the ID of the newly created campaign run mapping from history
      // Note: `api.createRecommendation` doesn't currently return the database ID directly. 
      // Assuming latest history row belongs to this request.
      if (rows && rows.length > 0) {
        setResult({ ...recommendation, id: rows[0].id });
      } else {
        setResult(recommendation);
      }

    } catch (error) {
      setPlanError(error.message || "Could not generate campaign recommendation.");
    } finally {
      setLoadingPlan(false);
    }
  };

  const handleLaunch = async (rec) => {
    const platform = rec.platform;
    setLaunchModal({ open: true, platform: platform, status: 'launching', message: `Deploying assets to ${platform}...` });
    const campaignId = result?.id || "unknown_campaign_id";
    const recommendationPayload = {
      ...rec,
      duration_days: Number(campaign.duration_days || 30),
      campaign_goal: campaign.campaign_goal,
      product_name: campaign.product_name,
      product_category: campaign.product_category || null,
    };

    if (platform === "Google Ads") {
      try {
        const response = await api.launchGoogleAds(accessToken, {
          campaign_id: campaignId,
          recommendation: recommendationPayload,
          dry_run: false
        });

        if (response.status === "already_launched") {
          setLaunchModal({ open: true, platform: platform, status: 'error', message: response.message });
        } else {
          setLaunchModal({ open: true, platform: platform, status: 'success', message: response.message });
          // Mark this recommendation as launched so the button disappears
          const launchKey = `${result.id}::${platform}`;
          setLaunchedKeys(prev => new Set([...prev, launchKey]));
        }

      } catch (error) {
        console.error("Launch error:", error);
        setLaunchModal({ open: true, platform: platform, status: 'error', message: error.message || "Failed to launch on Google Ads." });
      }

      setTimeout(() => {
        setLaunchModal(prev => ({ ...prev, open: false }));
      }, 3500);

    } else if (platform === "Instagram" || platform === "Facebook") {
      try {
        const response = await api.launchMetaAds(accessToken, {
          campaign_id: campaignId,
          recommendation: recommendationPayload,
          dry_run: false,
        });

        if (response.status === "already_launched") {
          setLaunchModal({ open: true, platform: platform, status: 'error', message: response.message });
        } else {
          setLaunchModal({ open: true, platform: platform, status: 'success', message: response.message });
          const launchKey = `${result?.id}::${platform}`;
          setLaunchedKeys(prev => new Set([...prev, launchKey]));
        }
      } catch (error) {
        console.error("Meta launch error:", error);
        setLaunchModal({ open: true, platform: platform, status: 'error', message: error.message || `Failed to launch on ${platform}.` });
      }

      setTimeout(() => {
        setLaunchModal(prev => ({ ...prev, open: false }));
      }, 3500);

    } else {
      // Fallback simulation for platforms without an integrated launcher yet.
      setTimeout(() => {
        setLaunchModal({ open: true, platform: platform, status: 'success', message: `Campaign is now live on ${platform}. (Simulated)` });
        // Mark as launched for simulated platforms too
        const launchKey = `${result?.id}::${platform}`;
        setLaunchedKeys(prev => new Set([...prev, launchKey]));
        setTimeout(() => {
          setLaunchModal({ open: false, platform: null, status: 'idle', message: '' });
        }, 2500);
      }, 2000);
    }
  };

  if (!accessToken) {
    return (
      <main className="auth-shell">
        <section className="auth-layout">
          <article className="auth-art">
            <p className="kicker">Nexus Engine</p>
            <h1>Marketing predictions elevated.</h1>
            <p className="subtext" style={{ fontSize: "1.1rem", lineHeight: "1.6" }}>
              Next-generation ROI estimation. Sign up once, predict cross-platform performance, and instantly launch automated campaigns.
            </p>
            <div className="auth-badges">
              <span>Encrypted Access</span>
              <span>Predictive Models</span>
              <span>1-Click Launch Activation</span>
            </div>
          </article>

          <article className="auth-panel">
            <h2>{authTitle}</h2>
            <p className="subtext" style={{ marginBottom: "2rem" }}>
              {authMode === "login"
                ? "Use your email and password to log in to the portal."
                : "Initialize a secure account to continue."}
            </p>

            <form onSubmit={submitAuth} className="stack">
              <label>
                Email Address
                <input
                  type="email"
                  value={email}
                  placeholder="name@domain.com"
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="email"
                />
              </label>

              <label>
                Password
                <input
                  type="password"
                  value={password}
                  placeholder="••••••••"
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  minLength={6}
                  autoComplete={authMode === "login" ? "current-password" : "new-password"}
                />
              </label>

              {authMode === "signup" && (
                <label>
                  Confirm Password
                  <input
                    type="password"
                    value={confirmPassword}
                    placeholder="••••••••"
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                </label>
              )}

              {authError && <p className="alert">{authError}</p>}

              <button type="submit" disabled={loadingAuth} style={{ marginTop: "0.5rem" }}>
                {loadingAuth ? "Authorizing..." : authMode === "login" ? "Enter Portal" : "Initialize Account"}
              </button>
            </form>

            <button
              type="button"
              className="ghost"
              style={{ marginTop: "1rem", width: "100%" }}
              onClick={() => {
                setAuthMode(authMode === "login" ? "signup" : "login");
                setAuthError("");
                setPassword("");
                setConfirmPassword("");
              }}
            >
              {authMode === "login" ? "Request an invite? Sign up" : "Already registered? Log in"}
            </button>
          </article>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      {/* Launch Action Modal */}
      {launchModal.open && (
        <div className="modal-overlay">
          <div className="modal-content">
            {launchModal.status === 'launching' && (
              <>
                <div className="spinner-wrapper">
                  <div className="spinner"></div>
                  <div className="spinner-inner"></div>
                </div>
                <h3>Initializing Deployment</h3>
                <p>{launchModal.message}</p>
              </>
            )}

            {launchModal.status === 'success' && (
              <>
                <div className="spinner-wrapper" style={{ display: 'grid', placeItems: 'center' }}>
                  <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                  </svg>
                </div>
                <h3 style={{ color: '#10b981' }}>Deployed Successfully</h3>
                <p>{launchModal.message}</p>
              </>
            )}

            {launchModal.status === 'error' && (
              <>
                <div className="spinner-wrapper" style={{ display: 'grid', placeItems: 'center' }}>
                  <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="15" y1="9" x2="9" y2="15"></line>
                    <line x1="9" y1="9" x2="15" y2="15"></line>
                  </svg>
                </div>
                <h3 style={{ color: '#ef4444' }}>Deployment Failed</h3>
                <p>{launchModal.message}</p>
              </>
            )}
          </div>
        </div>
      )}

      <header className="topbar">
        <div>
          <p className="kicker">Command Center</p>
          <h1>Campaign Architecture</h1>
          <p className="subtext">{user?.email || "Authenticated user"}</p>
        </div>
        <button className="ghost" onClick={logout}>
          Disconnect
        </button>
      </header>

      <section className="grid">
        <article className="card planner-card">
          <h2>Configure Vector</h2>
          <form onSubmit={generatePlan} className="planner-form">
            <label>
              Primary Goal
              <select
                value={campaign.campaign_goal}
                onChange={(event) => setCampaign((prev) => ({ ...prev, campaign_goal: event.target.value }))}
              >
                {goalOptions.map((goal) => (
                  <option key={goal.value} value={goal.value}>
                    {goal.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Product/Service Handle
              <input
                value={campaign.product_name}
                placeholder="e.g. NextGen VR Headset"
                onChange={(event) => setCampaign((prev) => ({ ...prev, product_name: event.target.value }))}
                required
              />
            </label>
            <label>
              Market Category
              <select
                value={campaign.product_category}
                onChange={(event) => setCampaign((prev) => ({ ...prev, product_category: event.target.value }))}
              >
                <option value="">Auto-detected optimum</option>
                {productTypes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Audience Segment
              <select
                value={campaign.customer_segment}
                onChange={(event) => setCampaign((prev) => ({ ...prev, customer_segment: event.target.value }))}
              >
                <option value="">Machine learning selection</option>
                {segments.map((segment) => (
                  <option key={segment} value={segment}>
                    {segment}
                  </option>
                ))}
              </select>
            </label>
            <div className="inline-fields">
              <label>
                Min Budget ($)
                <input
                  type="number"
                  min="1"
                  value={campaign.budget_min}
                  onChange={(event) => setCampaign((prev) => ({ ...prev, budget_min: event.target.value }))}
                  required
                />
              </label>
              <label>
                Max Budget ($)
                <input
                  type="number"
                  min="1"
                  value={campaign.budget_max}
                  onChange={(event) => setCampaign((prev) => ({ ...prev, budget_max: event.target.value }))}
                  required
                />
              </label>
            </div>
            <button type="submit" disabled={loadingPlan} style={{ marginTop: '0.5rem' }}>
              {loadingPlan ? "Simulating Strategy..." : "Generate Matrix"}
            </button>
          </form>
          {planError && <p className="alert" style={{ marginTop: '1rem' }}>{planError}</p>}
        </article>

        <article className="card output-card">
          <h2>Network Predictions</h2>
          {result?.recommendations?.length ? (
            <>
              <div className="prediction-list">
                {result.recommendations.map((rec) => (
                  <div key={rec.platform} className="prediction-item">
                    <h3>
                      {rec.platform}
                      <span className="badge">Optimized</span>
                    </h3>
                    <p>
                      <span>Audience Vector</span>
                      <strong>{formatAudience(rec)}</strong>
                    </p>
                    <p>
                      <span>Expected ROI</span>
                      <strong style={{ color: '#10b981' }}>{rec.predicted_roi}x</strong>
                    </p>
                    <p>
                      <span>Allocated Allocation</span>
                      <strong>${rec.budget}</strong>
                    </p>
                    <p>
                      <span>Conv. Probability</span>
                      <strong>{rec.predicted_conversion_rate}%</strong>
                    </p>
                    {(() => {
                      const launchKey = `${result?.id}::${rec.platform}`;
                      const isLaunched = launchedKeys.has(launchKey);
                      return isLaunched ? (
                        <div className="launched-badge">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                          </svg>
                          Launched
                        </div>
                      ) : (
                        <button
                          className="btn-launch"
                          onClick={() => handleLaunch(rec)}
                        >
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                          </svg>
                          Launch Network
                        </button>
                      );
                    })()}
                  </div>
                ))}
              </div>
              {result.budget_suggestion && (
                <div className="llm-block">
                  <h3>Calculated Expenditure</h3>
                  <p>
                    Optimal range: <strong style={{ color: "#a5b4fc" }}>${result.budget_suggestion.recommended_min} - ${result.budget_suggestion.recommended_max}</strong>
                    <br />(Mean efficiency at ${result.budget_suggestion.recommended_average})
                  </p>
                </div>
              )}
            </>
          ) : (
            <p className="subtext" style={{ padding: "2rem 0", textAlign: "center" }}>
              Configure matrix and generate strategy to predict network outcomes.
            </p>
          )}
          {insights.length > 0 && (
            <div className="insights">
              <h3>System Observability</h3>
              <ul>
                {insights.slice(0, 3).map((insight) => (
                  <li key={insight}>{insight}</li>
                ))}
              </ul>
            </div>
          )}
        </article>
      </section>

      <section className="card history-card">
        <h2 style={{ marginBottom: "0.5rem" }}>Transmission History</h2>
        {history.length === 0 ? (
          <p className="subtext">No historical metrics collected.</p>
        ) : (
          <div className="history-list">
            {history.map((item) => (
              <article
                key={item.id}
                className="history-item"
                style={{ cursor: "pointer" }}
                onClick={() => loadHistoryItem(item)}
              >
                <div className="header">
                  <h3>{item.product_name}</h3>
                  <span className="date">{formatDate(item.created_at)}</span>
                </div>
                <div className="details">
                  <p style={{ color: "var(--brand)" }}>{item.campaign_goal}</p>
                  <p>{item.output?.recommendations ? item.output.recommendations.map(r => r.platform).join(', ') : (item.top_platform || "N/A")}</p>
                </div>
                <div className="details">
                  <p style={{ color: "#10b981", fontWeight: "600" }}>
                    {item.predicted_roi ? `${item.predicted_roi}x Return` : "Analytics Offline"}
                  </p>
                  <span style={{ fontSize: "0.8rem", color: "var(--brand-2)" }}>→ Reload Matrix</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
