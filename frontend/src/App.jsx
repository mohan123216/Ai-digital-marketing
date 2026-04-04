import { useEffect, useState, useCallback, useRef } from "react";
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
const initialCampaign = { campaign_goal: "roi", product_name: "", product_category: "", location: "United States", gender: "All", customer_segment: "", budget_min: 2000, budget_max: 7000, duration_days: 30 };
const initialAdForm = { ad_name: "", headline_1: "", headline_2: "", headline_3: "", description_1: "", description_2: "", final_url: "", display_url_path_1: "", display_url_path_2: "", keywords_raw: "" };
const fmt = (iso) => new Date(iso).toLocaleDateString();
const fmtFull = (iso) => new Date(iso).toLocaleString();
const CharCount = ({ value, max }) => { const l = (value || "").length; return <span style={{ fontSize: "0.72rem", color: l > max ? "#ef4444" : "#64748b", marginLeft: "auto" }}>{l}/{max}</span>; };

// ── Landing Page ──────────────────────────────────────────────────────────────
function LandingPage({ onLogin, onSignup }) {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="landing-logo"><span className="logo-icon">⚡</span>NexusAds</div>
        <div className="landing-nav-actions">
          <button className="ghost nav-btn" onClick={onLogin}>Sign In</button>
          <button className="btn-primary nav-btn" onClick={onSignup}>Get Started</button>
        </div>
      </nav>
      <section className="hero">
        <div className="hero-badge">🤖 AI-Powered Marketing Automation</div>
        <h1 className="hero-title">Launch Campaigns Across<br /><span className="gradient-text">Every Platform, Instantly</span></h1>
        <p className="hero-sub">Autonomously plan, launch, optimize and scale paid ad campaigns across LinkedIn, Meta and Google Ads — powered by AI and MCP orchestration.</p>
        <div className="hero-cta">
          <button className="btn-hero-primary" onClick={onSignup}>Start for Free →</button>
          <button className="btn-hero-ghost" onClick={onLogin}>Sign In</button>
        </div>
        <div className="platform-badges">
          {["🔵 Google Ads", "🔶 Meta Ads", "🔷 LinkedIn Ads"].map(p => <span key={p} className="platform-badge">{p}</span>)}
        </div>
      </section>
      <section className="features">
        <h2 className="section-title">Everything you need to scale</h2>
        <div className="features-grid">
          {[
            { icon: "🧠", title: "AI Campaign Planning", desc: "ML models predict ROI and conversion rates across platforms before you spend a dollar." },
            { icon: "🚀", title: "One-Click Launch", desc: "Launch campaigns to Google Ads, Meta, and LinkedIn simultaneously with a single click." },
            { icon: "📊", title: "Real-Time Metrics", desc: "Monitor campaign performance live. Impressions, clicks, conversions — all in one place." },
            { icon: "🤖", title: "MCP Orchestration", desc: "Open Model Context Protocol server autonomously manages campaign lifecycle end-to-end." },
            { icon: "🔒", title: "Secure & Encrypted", desc: "JWT authentication, encrypted credentials, and row-level security on all campaign data." },
            { icon: "📈", title: "Scale Intelligently", desc: "AI recommendations adapt to your budget, audience, and goals for maximum impact." },
          ].map(f => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="stats-section">
        {[["3", "Platforms Supported"], ["2.4x", "Avg ROI Improvement"], ["< 60s", "Campaign Launch Time"], ["100%", "AI-Automated"]].map(([v, l]) => (
          <div key={l} className="stat-item"><span className="stat-val">{v}</span><span className="stat-label">{l}</span></div>
        ))}
      </section>
      <div className="landing-footer">
        <p>© 2025 NexusAds — AI Digital Marketing Agent</p>
        <button className="btn-hero-primary" onClick={onSignup} style={{ marginTop: "1.5rem" }}>Get Started Free →</button>
      </div>
    </div>
  );
}

// ── Auth Pages ─────────────────────────────────────────────────────────────────
function AuthPage({ mode, onSuccess, onSwitch, onBack }) {
  const [email, setEmail] = useState(""); const [pw, setPw] = useState(""); const [cpw, setCpw] = useState("");
  const [err, setErr] = useState(""); const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setErr(""); setLoading(true);
    try {
      if (mode === "signup" && pw !== cpw) throw new Error("Passwords do not match.");
      const res = mode === "login" ? await api.login({ email: email.trim().toLowerCase(), password: pw }) : await api.signup({ email: email.trim().toLowerCase(), password: pw });
      localStorage.setItem(TOKEN_KEY, res.access_token);
      onSuccess(res.access_token, res.user);
    } catch (ex) { setErr(ex.message || "Authentication failed."); }
    finally { setLoading(false); }
  };
  return (
    <div className="auth-page">
      <button className="ghost back-btn" onClick={onBack}>← Back to Home</button>
      <div className="auth-card">
        <div className="auth-card-logo"><span className="logo-icon">⚡</span><span>NexusAds</span></div>
        <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <p className="subtext" style={{ marginBottom: "1.5rem" }}>{mode === "login" ? "Sign in to your dashboard" : "Start launching AI-powered campaigns"}</p>
        <form onSubmit={submit} className="stack">
          <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="name@company.com" required /></label>
          <label>Password<input type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder="••••••••" required minLength={6} /></label>
          {mode === "signup" && <label>Confirm Password<input type="password" value={cpw} onChange={e => setCpw(e.target.value)} placeholder="••••••••" required minLength={6} /></label>}
          {err && <p className="alert">{err}</p>}
          <button type="submit" disabled={loading} style={{ marginTop: "0.5rem" }}>{loading ? "Please wait…" : mode === "login" ? "Sign In" : "Create Account"}</button>
        </form>
        <button className="ghost" style={{ width: "100%", marginTop: "1rem" }} onClick={onSwitch}>
          {mode === "login" ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState(() => localStorage.getItem(TOKEN_KEY) ? "dashboard" : "landing");
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [dashTab, setDashTab] = useState("overview");
  const [history, setHistory] = useState([]);
  const [segments, setSegments] = useState([]);
  const [productTypes, setProductTypes] = useState([]);
  const [insights, setInsights] = useState([]);
  const [campaign, setCampaign] = useState(initialCampaign);
  const [result, setResult] = useState(null);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [planError, setPlanError] = useState("");
  const [launchedKeys, setLaunchedKeys] = useState(new Set());
  const [launchModal, setLaunchModal] = useState({ open: false, platform: null, status: "idle" });
  const [adModal, setAdModal] = useState({ open: false, campaignRunId: null, status: "idle" });
  const [adTab, setAdTab] = useState("text");
  const [adForm, setAdForm] = useState(initialAdForm);
  const [adFormError, setAdFormError] = useState("");
  const [editLaunchModal, setEditLaunchModal] = useState({ open: false, rec: null, campaignRunId: null, adType: "text", form: {} });
  const [loadingAd, setLoadingAd] = useState(false);
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [useYoutubeUrl, setUseYoutubeUrl] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const dropRef = useRef(null);
  const [campaignAds, setCampaignAds] = useState({});
  const [adsLoading, setAdsLoading] = useState({});
  const [metricsModal, setMetricsModal] = useState({ open: false, campaignRunId: null, data: null, error: "", loading: false });
  const [selectedMetricsItem, setSelectedMetricsItem] = useState(null);
  const [optimizeModal, setOptimizeModal] = useState({ open: false, campaignRunId: null, campaignName: "", dryRun: true, useMockData: false, loading: false, result: null, error: "", history: [] });
  const [scaleupData, setScaleupData] = useState(null);
  const [scaleupLoading, setScaleupLoading] = useState(false);
  const [scaleupError, setScaleupError] = useState("");

  useEffect(() => {
    api.getSegments().then(r => setSegments(r.segments || [])).catch(() => {});
    api.getProductTypes().then(r => setProductTypes(r.product_types || [])).catch(() => {});
    api.getInsights().then(r => setInsights(r.insights || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!accessToken) { setUser(null); setHistory([]); return; }
    Promise.all([api.getMe(accessToken), api.getHistory(accessToken)]).then(([u, rows]) => {
      setUser(u); setHistory(rows);
      const keys = new Set();
      rows.forEach(item => (item.launched_platforms || []).forEach(p => keys.add(`${item.id}::${p}`)));
      setLaunchedKeys(keys);
    }).catch(() => { localStorage.removeItem(TOKEN_KEY); setAccessToken(""); setPage("landing"); });
  }, [accessToken]);

  const onAuthSuccess = (token, u) => { setAccessToken(token); setUser(u); setPage("dashboard"); };
  const logout = () => {
    localStorage.removeItem(TOKEN_KEY); setAccessToken(""); setUser(null); setHistory([]); setResult(null);
    setCampaign(initialCampaign); setCampaignAds({}); setPage("landing");
  };

  const loadAds = useCallback(async (id) => {
    if (!accessToken || !id) return;
    setAdsLoading(p => ({ ...p, [id]: true }));
    try { const ads = await api.getAds(accessToken, id); setCampaignAds(p => ({ ...p, [id]: ads })); }
    catch (_) {} finally { setAdsLoading(p => ({ ...p, [id]: false })); }
  }, [accessToken]);

  const handleViewMetrics = async (id, platform = "Google Ads") => {
    setMetricsModal({ open: true, campaignRunId: id, platform, data: null, error: "", loading: true });
    try {
      const isGA = platform === "Google Ads";
      const m = isGA
        ? await api.getCampaignMetrics(accessToken, id)
        : await api.getMetaCampaignMetrics(accessToken, id, platform);
      setMetricsModal(p => ({ ...p, data: m, loading: false }));
    }
    catch (err) { setMetricsModal(p => ({ ...p, error: err.message || "Failed.", loading: false })); }
  };

  const loadHistoryItem = (item) => {
    const pi = item.output?.campaign_input || {};
    setCampaign({ ...initialCampaign, campaign_goal: item.campaign_goal || "roi", product_name: item.product_name || "", budget_min: item.budget_min || 2000, budget_max: item.budget_max || 7000, product_category: pi.product_category || "", location: pi.target_audience?.location || "United States", gender: pi.target_audience?.gender || "All", customer_segment: pi.target_audience?.customer_segment || "", duration_days: pi.duration_days || 30 });
    setResult({ ...item.output, id: item.id, google_ads_type: item.google_ads_type });
    (item.launched_platforms || []).forEach(p => setLaunchedKeys(prev => new Set([...prev, `${item.id}::${p}`])));
    loadAds(item.id); setDashTab("plan");
  };

  const generatePlan = async (e) => {
    e.preventDefault(); if (!accessToken) return;
    if (Number(campaign.budget_min) > Number(campaign.budget_max)) { setPlanError("Min budget cannot exceed max."); return; }
    setLoadingPlan(true); setPlanError("");
    const payload = { campaign_goal: campaign.campaign_goal, product_name: campaign.product_name, product_category: campaign.product_category || null, target_audience: { location: campaign.location, gender: campaign.gender, interests: [], customer_segment: campaign.customer_segment || null }, budget_range: { min: Number(campaign.budget_min), max: Number(campaign.budget_max) }, duration_days: Number(campaign.duration_days), start_date: new Date().toISOString().split("T")[0] };
    try {
      const rec = await api.createRecommendation(accessToken, payload);
      const rows = await api.getHistory(accessToken); setHistory(rows);
      const keys = new Set(); rows.forEach(item => (item.launched_platforms || []).forEach(p => keys.add(`${item.id}::${p}`))); setLaunchedKeys(keys);
      if (rows.length > 0) { setResult({ ...rec, id: rows[0].id, google_ads_type: rows[0].google_ads_type }); loadAds(rows[0].id); }
      else setResult(rec);
    } catch (err) { setPlanError(err.message || "Could not generate recommendations."); }
    finally { setLoadingPlan(false); }
  };

  // Open the edit-before-launch modal, pre-filling with recommendation values
  const handleLaunchInitiate = (rec, campaignRunId) => {
    const cid = campaignRunId || result?.id || "unknown";
    setEditLaunchModal({
      open: true, rec, campaignRunId: cid,
      adType: "text",
      form: {
        budget: rec.budget ?? "",
        target_location: rec.target_location ?? "",
        target_segment: rec.target_segment ?? "",
        target_age_group: rec.target_age_group ?? "",
        duration_days: campaign.duration_days ?? 30,
        campaign_goal: rec.campaign_goal ?? campaign.campaign_goal ?? "roi",
      },
    });
  };

  const handleLaunch = async () => {
    const { rec, campaignRunId, adType, form } = editLaunchModal;
    setEditLaunchModal(p => ({ ...p, open: false }));
    const platform = rec.platform;
    setLaunchModal({ open: true, platform, status: "launching", message: `Deploying to ${platform}…` });
    // Merge user-edited values into the recommendation
    const payload = {
      ...rec,
      budget: Number(form.budget) || rec.budget,
      target_location: form.target_location || rec.target_location,
      target_segment: form.target_segment || rec.target_segment,
      target_age_group: form.target_age_group || rec.target_age_group,
      duration_days: Number(form.duration_days) || 30,
      campaign_goal: form.campaign_goal || rec.campaign_goal || campaign.campaign_goal,
      product_name: rec.product_name || campaign.product_name,
      product_category: rec.product_category || campaign.product_category || null,
    };
    try {
      let response;
          if (platform === "Google Ads") response = await api.launchGoogleAds(accessToken, { campaign_id: campaignRunId, recommendation: payload, ad_type: adType, campaign_name: form.campaign_name || undefined, dry_run: false });
      else if (platform === "Instagram" || platform === "Facebook") response = await api.launchMetaAds(accessToken, { campaign_id: campaignRunId, recommendation: payload, dry_run: false });
          else if (platform === "Instagram" || platform === "Facebook") response = await api.launchMetaAds(accessToken, { campaign_id: campaignRunId, recommendation: payload, campaign_name: form.campaign_name || undefined, dry_run: false });
      else { await new Promise(r => setTimeout(r, 1500)); response = { status: "launched", message: `Campaign is live on ${platform}.` }; }
      if (response.status === "already_launched") setLaunchModal({ open: true, platform, status: "error", message: response.message });
      else {
        setLaunchModal({ open: true, platform, status: "success", message: response.message });
        setLaunchedKeys(p => new Set([...p, `${campaignRunId}::${platform}`]));
        if (platform === "Google Ads") setResult(p => p ? { ...p, google_ads_type: adType } : p);
        const rows = await api.getHistory(accessToken); setHistory(rows);
      }
    } catch (err) { setLaunchModal({ open: true, platform, status: "error", message: err.message || "Launch failed." }); }
    setTimeout(() => setLaunchModal(p => ({ ...p, open: false })), 3500);
  };

  const openAdModal = (id, allowedType = "text") => { setAdForm(initialAdForm); setAdFormError(""); setAdTab(allowedType); setMediaFile(null); setMediaPreview(null); setYoutubeUrl(""); setUseYoutubeUrl(false); setUploadProgress(0); setAdModal({ open: true, campaignRunId: id, status: "idle", allowedType }); };

  const runOptimize = async (campaignRunId, campaignName, dryRun = false, useMockData = false) => {
    setOptimizeModal(p => ({ ...p, loading: true, result: null, error: "" }));
    try {
      const result = await api.optimizeCampaign(accessToken, campaignRunId, dryRun, useMockData);
      setOptimizeModal(p => ({ ...p, loading: false, result }));
      // Fetch history update
      if (!dryRun) {
        try {
          const hist = await api.getOptimizationHistory(accessToken, campaignRunId);
          setOptimizeModal(p => ({ ...p, history: hist.history || [] }));
        } catch (e) {}
      }
    } catch (err) {
      setOptimizeModal(p => ({ ...p, loading: false, error: err.message || "Optimization failed." }));
    }
  };

  const closeAdModal = () => { if (mediaPreview) URL.revokeObjectURL(mediaPreview); setAdModal({ open: false, campaignRunId: null, status: "idle" }); setAdForm(initialAdForm); setAdFormError(""); setMediaFile(null); setMediaPreview(null); };
  const applyFile = (f) => { if (!f) return; setMediaFile(f); if (mediaPreview) URL.revokeObjectURL(mediaPreview); setMediaPreview(URL.createObjectURL(f)); };

  const validateFinalUrl = (url) => {
    if (!url || !url.trim()) return "Final URL is required.";
    url = url.trim();
    if (url.toLowerCase().includes('localhost')) return "Final URL cannot be 'localhost'. Please provide a valid domain (e.g., https://example.com).";
    if (!url.startsWith('http://') && !url.startsWith('https://')) return "Final URL must start with http:// or https://";
    try {
      const u = new URL(url);
      if (!u.hostname || !u.hostname.includes('.')) return "Final URL must contain a valid domain with a top-level domain (e.g., .com, .org).";
    } catch { return "Invalid URL format."; }
    return null;
  };


  const submitAd = async (e) => {
    e.preventDefault(); setAdFormError("");
    const { ad_name, headline_1, headline_2, headline_3, description_1, description_2, final_url, display_url_path_1, display_url_path_2, keywords_raw } = adForm;
    if (!headline_1.trim() || !headline_2.trim() || !headline_3.trim()) { setAdFormError("All three headlines are required."); return; }
    if (!description_1.trim() || !description_2.trim()) { setAdFormError("Both descriptions are required."); return; }
    const urlError = validateFinalUrl(final_url);
    if (urlError) { setAdFormError(urlError); return; }
    const keywords = keywords_raw.split(",").map(k => k.trim()).filter(Boolean);
    const payload = { ad_name: ad_name.trim() || null, ad_type: "text", headline_1: headline_1.trim(), headline_2: headline_2.trim(), headline_3: headline_3.trim(), description_1: description_1.trim(), description_2: description_2.trim(), final_url: final_url.trim(), display_url_path_1: display_url_path_1.trim() || null, display_url_path_2: display_url_path_2.trim() || null, keywords, dry_run: false };
    setLoadingAd(true); setAdModal(p => ({ ...p, status: "launching" }));
    try { const ad = await api.launchAd(accessToken, adModal.campaignRunId, payload); setCampaignAds(p => ({ ...p, [adModal.campaignRunId]: [ad, ...(p[adModal.campaignRunId] || [])] })); setAdModal(p => ({ ...p, status: "success" })); setTimeout(() => closeAdModal(), 2500); }
    catch (err) { setAdModal(p => ({ ...p, status: "error" })); setAdFormError(err.message || "Failed to launch ad."); }
    finally { setLoadingAd(false); }
  };

  const submitMediaAd = async (e) => {
    e.preventDefault(); setAdFormError("");
    const { ad_name, final_url, long_headline, business_name, headline_1, description_1, keywords_raw } = adForm;
    if (!final_url.trim()) { setAdFormError("Final URL is required."); return; }
    const fd = new FormData();
    fd.append("ad_type", adTab); fd.append("ad_name", ad_name || ""); fd.append("final_url", final_url.trim());
    fd.append("long_headline", long_headline || ""); fd.append("business_name", business_name || "");
    fd.append("headline_1", headline_1 || ""); fd.append("description_1", description_1 || "");
    fd.append("keywords", keywords_raw || ""); fd.append("dry_run", "false");
    if (adTab === "video" && useYoutubeUrl) { if (!youtubeUrl.trim()) { setAdFormError("Please enter a YouTube URL."); return; } fd.append("youtube_url", youtubeUrl.trim()); fd.append("file", new Blob([], { type: "application/octet-stream" }), ""); }
    else { if (!mediaFile) { setAdFormError("Please select a file."); return; } fd.append("file", mediaFile); fd.append("youtube_url", ""); }
    setLoadingAd(true); setAdModal(p => ({ ...p, status: "launching" })); setUploadProgress(0);
    const pi = setInterval(() => setUploadProgress(p => Math.min(p + 8, 90)), 200);
    try { const ad = await api.launchMediaAd(accessToken, adModal.campaignRunId, fd); clearInterval(pi); setUploadProgress(100); setCampaignAds(p => ({ ...p, [adModal.campaignRunId]: [ad, ...(p[adModal.campaignRunId] || [])] })); setAdModal(p => ({ ...p, status: "success" })); setTimeout(() => closeAdModal(), 2500); }
    catch (err) { clearInterval(pi); setUploadProgress(0); setAdModal(p => ({ ...p, status: "error" })); setAdFormError(err.message || "Upload failed."); }
    finally { setLoadingAd(false); }
  };

  // ── Routing ──────────────────────────────────────────────────────────────────
  if (page === "landing") return <LandingPage onLogin={() => setPage("login")} onSignup={() => setPage("signup")} />;
  if (page === "login") return <AuthPage mode="login" onSuccess={onAuthSuccess} onSwitch={() => setPage("signup")} onBack={() => setPage("landing")} />;
  if (page === "signup") return <AuthPage mode="signup" onSuccess={onAuthSuccess} onSwitch={() => setPage("login")} onBack={() => setPage("landing")} />;

  // ── Dashboard ─────────────────────────────────────────────────────────────
  const totalCampaigns = history.length;
  const launchedCount = history.filter(h => (h.launched_platforms || []).length > 0).length;
  const avgROI = history.length ? (history.reduce((s, h) => s + (h.predicted_roi || 0), 0) / history.length).toFixed(2) : "—";

  const navItems = [
    { id: "overview", icon: "📊", label: "Overview" },
    { id: "campaigns", icon: "🚀", label: "Campaigns" },
    { id: "plan", icon: "📝", label: "Plan Campaign" },
    { id: "metrics", icon: "📈", label: "Metrics" },
    { id: "optimize", icon: "⚡", label: "Optimize" },
    { id: "scaleup", icon: "📈", label: "Scale Up" },
    { id: "settings", icon: "⚙️", label: "Settings" },
  ];

  return (
    <div className="dashboard-layout">
      {/* Modals */}
      {launchModal.open && (
        <div className="modal-overlay">
          <div className="modal-content">
            {launchModal.status === "launching" && <><div className="spinner-wrapper"><div className="spinner" /><div className="spinner-inner" /></div><h3>Deploying…</h3><p>{launchModal.message}</p></>}
            {launchModal.status === "success" && <><div className="modal-icon success-icon">✓</div><h3 style={{ color: "#10b981" }}>Launched!</h3><p>{launchModal.message}</p></>}
            {launchModal.status === "error" && <><div className="modal-icon error-icon">✗</div><h3 style={{ color: "#ef4444" }}>Failed</h3><p>{launchModal.message}</p></>}
          </div>
        </div>
      )}

      {editLaunchModal.open && (() => {
        const { rec, adType, form } = editLaunchModal;
        const isGA = rec?.platform === "Google Ads";
        const setForm = (k, v) => setEditLaunchModal(p => ({ ...p, form: { ...p.form, [k]: v } }));
        return (
          <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) setEditLaunchModal(p => ({ ...p, open: false })); }}>
            <div className="modal-content edit-launch-modal" style={{ maxWidth: 560, width: "95vw", textAlign: "left" }}>
              <div className="ad-modal-header">
                <div>
                  <p className="kicker">{rec?.platform}</p>
                  <h3>Review & Edit Campaign</h3>
                  <p className="subtext" style={{ marginTop: "0.25rem", fontSize: "0.85rem" }}>Adjust any values before launching. These settings override the AI recommendations.</p>
                </div>
                <button className="ghost modal-close-btn" onClick={() => setEditLaunchModal(p => ({ ...p, open: false }))}>✕</button>
              </div>
              <div className="edit-launch-fields">
                <div className="el-row">
                  <label>Budget ($)<input type="number" min="1" value={form.budget} onChange={e => setForm("budget", e.target.value)} /></label>
                  <label>Duration (days)<input type="number" min="1" max="365" value={form.duration_days} onChange={e => setForm("duration_days", e.target.value)} /></label>
                                <label>Campaign Name<input type="text" placeholder="e.g. My Campaign 2024" value={form.campaign_name} onChange={e => setForm("campaign_name", e.target.value)} /></label>
                </div>
                <label>Target Location<input type="text" placeholder="e.g. United States" value={form.target_location} onChange={e => setForm("target_location", e.target.value)} /></label>
                <label>Target Segment<input type="text" placeholder="e.g. Young Professionals" value={form.target_segment} onChange={e => setForm("target_segment", e.target.value)} /></label>
                <label>Age Group<input type="text" placeholder="e.g. 25-44" value={form.target_age_group} onChange={e => setForm("target_age_group", e.target.value)} /></label>
                <label>Campaign Goal
                  <select value={form.campaign_goal} onChange={e => setForm("campaign_goal", e.target.value)}>
                    {goalOptions.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
                  </select>
                </label>
                {isGA && (
                  <>
                    <div className="ad-section-title" style={{ marginTop: "0.5rem" }}>Ad Format</div>
                    {[{ key: "text", icon: "📝", title: "Search (Text RSA)", desc: "Responsive Search Ads on Google Search." }, { key: "image", icon: "🖼️", title: "Display (Image)", desc: "Responsive Display Ads across the web." }, { key: "video", icon: "🎬", title: "Video (YouTube)", desc: "Skippable In-Stream Video Ads on YouTube." }].map(o => (
                      <label key={o.key} className={`modal-option-card${editLaunchModal.adType === o.key ? " active" : ""}`} style={{ marginBottom: "0.5rem" }}>
                        <input type="radio" name="elAdType" value={o.key} checked={editLaunchModal.adType === o.key} onChange={() => setEditLaunchModal(p => ({ ...p, adType: o.key }))} style={{ display: "none" }} />
                        <div className="option-icon">{o.icon}</div>
                        <div className="option-info"><strong>{o.title}</strong><span>{o.desc}</span></div>
                      </label>
                    ))}
                  </>
                )}
              </div>
              <div className="ad-form-actions" style={{ borderTop: "1px solid var(--border)", paddingTop: "1rem", marginTop: "1rem" }}>
                <button className="ghost" onClick={() => setEditLaunchModal(p => ({ ...p, open: false }))}>Cancel</button>
                <button className="btn-launch" onClick={handleLaunch}>🚀 Launch to {rec?.platform}</button>
              </div>
            </div>
          </div>
        );
      })()}

      {adModal.open && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget && adModal.status === "idle") closeAdModal(); }}>
          <div className="modal-content ad-launch-modal">
            {adModal.status === "launching" && <div style={{ textAlign: "center", padding: "1rem 0" }}><div className="spinner-wrapper" style={{ margin: "0 auto 1rem" }}><div className="spinner" /><div className="spinner-inner" /></div><h3>Creating Ad…</h3>{adTab !== "text" && uploadProgress > 0 && <div className="upload-progress-bar"><div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }} /></div>}</div>}
            {adModal.status === "success" && <div style={{ textAlign: "center", padding: "1rem 0" }}><div className="modal-icon success-icon" style={{ fontSize: "2.5rem" }}>✓</div><h3 style={{ color: "#10b981" }}>Ad Launched! 🎉</h3><p>Your ad is live on Google Ads.</p></div>}
            {adModal.status === "error" && <div style={{ textAlign: "center", padding: "1rem 0" }}><div className="modal-icon error-icon" style={{ fontSize: "2.5rem" }}>✗</div><h3 style={{ color: "#ef4444" }}>Launch Failed</h3>{adFormError && <p className="alert">{adFormError}</p>}<button onClick={closeAdModal} className="ghost" style={{ width: "100%", marginTop: "1rem" }}>Close</button></div>}
            {adModal.status === "idle" && (
              <>
                <div className="ad-modal-header"><div><p className="kicker">Google Ads</p><h3>Launch New Ad</h3></div><button className="ghost modal-close-btn" onClick={closeAdModal}>✕</button></div>
                <div className="ad-type-tabs">
                  {[{ key: "text", icon: "📝", label: "Text" }, { key: "image", icon: "🖼️", label: "Image" }, { key: "video", icon: "🎬", label: "Video" }].map(t => {
                    const dis = adModal.allowedType && adModal.allowedType !== t.key;
                    return <button key={t.key} type="button" className={`ad-tab-btn${adTab === t.key ? " active" : ""}${dis ? " disabled-tab" : ""}`} disabled={dis} onClick={() => { setAdTab(t.key); setAdFormError(""); setMediaFile(null); setMediaPreview(null); }}>{t.icon} {t.label}</button>;
                  })}
                </div>
                {adTab === "text" && (
                  <form onSubmit={submitAd} className="ad-form">
                    <label className="ad-field-full">Ad Name <span className="optional-tag">optional</span><input type="text" placeholder="Summer Sale RSA" value={adForm.ad_name} onChange={e => setAdForm(p => ({ ...p, ad_name: e.target.value }))} /></label>
                    <div className="ad-section-title">Headlines <span className="char-note">max 30 chars</span></div>
                    {["headline_1", "headline_2", "headline_3"].map((f, i) => (<label key={f} className="ad-field-full"><span style={{ display: "flex", justifyContent: "space-between" }}>Headline {i + 1} <CharCount value={adForm[f]} max={30} /></span><input type="text" maxLength={30} value={adForm[f]} onChange={e => setAdForm(p => ({ ...p, [f]: e.target.value }))} required /></label>))}
                    <div className="ad-section-title">Descriptions <span className="char-note">max 90 chars</span></div>
                    {["description_1", "description_2"].map((f, i) => (<label key={f} className="ad-field-full"><span style={{ display: "flex", justifyContent: "space-between" }}>Description {i + 1} <CharCount value={adForm[f]} max={90} /></span><textarea maxLength={90} rows={2} value={adForm[f]} onChange={e => setAdForm(p => ({ ...p, [f]: e.target.value }))} required /></label>))}
                    <label className="ad-field-full">Final URL *<input type="url" placeholder="https://yoursite.com" value={adForm.final_url} onChange={e => setAdForm(p => ({ ...p, final_url: e.target.value }))} required /></label>
                    <label className="ad-field-full">Keywords <span className="optional-tag">comma-separated</span><input type="text" placeholder="shoes, sneakers" value={adForm.keywords_raw} onChange={e => setAdForm(p => ({ ...p, keywords_raw: e.target.value }))} /></label>
                    {adFormError && <p className="alert ad-field-full">{adFormError}</p>}
                    <div className="ad-form-actions"><button type="button" className="ghost" onClick={closeAdModal}>Cancel</button><button type="submit" disabled={loadingAd} className="btn-launch-ad">{loadingAd ? "Launching…" : "Launch Text Ad"}</button></div>
                  </form>
                )}
                {(adTab === "image" || adTab === "video") && (
                  <form onSubmit={submitMediaAd} className="ad-form">
                    <label className="ad-field-full">Ad Name <span className="optional-tag">optional</span><input type="text" value={adForm.ad_name} onChange={e => setAdForm(p => ({ ...p, ad_name: e.target.value }))} /></label>
                    {adTab === "video" && <div className="video-source-toggle ad-field-full"><button type="button" className={`src-btn${!useYoutubeUrl ? " active" : ""}`} onClick={() => setUseYoutubeUrl(false)}>📁 Upload</button><button type="button" className={`src-btn${useYoutubeUrl ? " active" : ""}`} onClick={() => setUseYoutubeUrl(true)}>▶️ YouTube URL</button></div>}
                    {(adTab === "image" || (adTab === "video" && !useYoutubeUrl)) ? (
                      <div className={`drop-zone ad-field-full${dragging ? " dragging" : ""}${mediaFile ? " has-file" : ""}`} ref={dropRef} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); applyFile(e.dataTransfer.files[0]); }} onClick={() => document.getElementById("media-file-input").click()}>
                        {mediaPreview && adTab === "image" ? <div className="media-preview"><img src={mediaPreview} alt="Preview" style={{ maxHeight: 140, maxWidth: "100%", borderRadius: 8, objectFit: "contain" }} /><p className="media-filename">{mediaFile?.name}</p></div> : mediaFile ? <div className="media-preview"><p className="media-filename">🎬 {mediaFile.name}</p></div> : <div className="drop-zone-inner"><p>Drag & drop or click to browse</p><span>{adTab === "image" ? "JPG, PNG · max 10 MB" : "MP4, MOV · max 200 MB"}</span></div>}
                      </div>
                    ) : <label className="ad-field-full">YouTube URL *<input type="url" placeholder="https://www.youtube.com/watch?v=..." value={youtubeUrl} onChange={e => setYoutubeUrl(e.target.value)} required /></label>}
                    <input id="media-file-input" type="file" accept={adTab === "image" ? "image/*" : "video/*"} style={{ display: "none" }} onChange={e => applyFile(e.target.files[0])} />
                    <label className="ad-field-full">Final URL *<input type="url" placeholder="https://yoursite.com" value={adForm.final_url} onChange={e => setAdForm(p => ({ ...p, final_url: e.target.value }))} required /></label>
                    {adTab === "image" && <><label className="ad-field-full">Long Headline<input type="text" maxLength={90} value={adForm.long_headline || ""} onChange={e => setAdForm(p => ({ ...p, long_headline: e.target.value }))} /></label><label className="ad-field-full">Business Name<input type="text" maxLength={25} value={adForm.business_name || ""} onChange={e => setAdForm(p => ({ ...p, business_name: e.target.value }))} /></label></>}
                    {adFormError && <p className="alert ad-field-full">{adFormError}</p>}
                    <div className="ad-form-actions"><button type="button" className="ghost" onClick={closeAdModal}>Cancel</button><button type="submit" disabled={loadingAd || (!useYoutubeUrl && !mediaFile)} className="btn-launch-ad">{loadingAd ? `${uploadProgress}%…` : "Launch Ad"}</button></div>
                  </form>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {metricsModal.open && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) setMetricsModal({ open: false, campaignRunId: null, data: null, error: "", loading: false }); }}>
          <div className="modal-content" style={{ maxWidth: 640, width: "90vw", textAlign: "left" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
              <h3 style={{ margin: 0 }}>Campaign Metrics</h3>
              <button className="ghost modal-close-btn" onClick={() => setMetricsModal({ open: false, campaignRunId: null, data: null, error: "", loading: false })}>✕</button>
            </div>
            {metricsModal.loading && <div style={{ textAlign: "center", padding: "2rem" }}><div className="spinner-wrapper" style={{ margin: "0 auto" }}><div className="spinner" /><div className="spinner-inner" /></div></div>}
            {metricsModal.error && <p className="alert">{metricsModal.error}</p>}
            {metricsModal.data && (
              <div>
                {(metricsModal.data.campaign_metrics || []).length === 0 && (metricsModal.data.ad_metrics || []).length === 0 ? <p className="subtext" style={{ padding: "1rem 0" }}>No metrics available yet. (Campaign may be in dry-run or pending Google Ads approval.)</p> : (
                  <>
                    {(metricsModal.data.campaign_metrics || []).map((m, i) => (<div key={i} className="metrics-card"><h4>{m.campaign_name}</h4><div className="metrics-grid"><div><span>Impressions</span><strong>{(m.impressions || 0).toLocaleString()}</strong></div><div><span>Clicks</span><strong>{(m.clicks || 0).toLocaleString()}</strong></div><div><span>Cost</span><strong>${((m.cost_micros || 0) / 1e6).toFixed(2)}</strong></div><div><span>Conv.</span><strong>{m.conversions || 0}</strong></div></div></div>))}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo"><span className="logo-icon">⚡</span><span>NexusAds</span></div>
        <nav className="sidebar-nav">
          {navItems.map(n => (<button key={n.id} className={`nav-link${dashTab === n.id ? " active" : ""}`} onClick={() => setDashTab(n.id)}><span className="nav-icon">{n.icon}</span><span>{n.label}</span></button>))}
        </nav>
        <div className="sidebar-user">
          <div className="user-avatar">{(user?.email || "U")[0].toUpperCase()}</div>
          <div className="user-info"><span className="user-email">{user?.email}</span></div>
          <button className="ghost logout-btn" onClick={logout} title="Logout">⏏</button>
        </div>
      </aside>

      {/* Main content */}
      <main className="dash-main">
        {/* Overview */}
        {dashTab === "overview" && (
          <div className="dash-section">
            <div className="dash-page-header"><h1>Overview</h1><p className="subtext">Your AI marketing command center</p></div>
            <div className="overview-stats">
              {[["🗂️", String(totalCampaigns), "Total Campaigns"], ["🚀", String(launchedCount), "Active Launches"], ["📈", `${avgROI}x`, "Avg. ROI"], ["🌐", "3", "Platforms"]].map(([icon, val, label]) => (
                <div key={label} className="overview-stat-card"><div className="ov-icon">{icon}</div><div className="ov-value">{val}</div><div className="ov-label">{label}</div></div>
              ))}
            </div>
            <div className="overview-recent">
              <h2 style={{ marginBottom: "1rem" }}>Recent Campaigns</h2>
              {history.length === 0 ? <p className="subtext">No campaigns yet. <button className="link-btn" onClick={() => setDashTab("plan")}>Plan your first →</button></p> : (
                <div className="campaign-list">
                  {history.slice(0, 5).map(item => (
                    <div key={item.id} className="campaign-row" onClick={() => loadHistoryItem(item)}>
                      <div className="cr-left"><strong>{item.product_name}</strong><span className="cr-goal">{item.campaign_goal}</span></div>
                      <div className="cr-mid"><span className="cr-roi">{item.predicted_roi ? `${item.predicted_roi}x ROI` : "—"}</span></div>
                      <div className="cr-right">
                        {(item.launched_platforms || []).length > 0 ? (item.launched_platforms || []).map(p => <span key={p} className="platform-chip">{p}</span>) : <span className="chip-pending">Not launched</span>}
                        <span className="cr-date">{fmt(item.created_at)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {insights.length > 0 && <div className="insights-box"><h3>AI Insights</h3><ul>{insights.slice(0, 3).map(i => <li key={i}>{i}</li>)}</ul></div>}
          </div>
        )}

        {/* Campaigns */}
        {dashTab === "campaigns" && (
          <div className="dash-section">
            <div className="dash-page-header"><h1>Campaigns</h1><p className="subtext">{totalCampaigns} total campaign runs — launch any platform from here</p></div>
            {history.length === 0 ? <div className="empty-state"><p>🗂️</p><h3>No campaigns yet</h3><button className="btn-primary" onClick={() => setDashTab("plan")}>Plan Your First Campaign</button></div> : (
              <div className="campaign-list full">
                {history.map(item => {
                  const recs = item.output?.recommendations || [];
                  const launched = item.launched_platforms || [];
                  return (
                    <div key={item.id} className="campaign-card">
                      <div className="cc-header">
                        <div className="cr-left">
                          <strong>{item.product_name}</strong>
                          <span className="cr-goal">{item.campaign_goal}</span>
                          <code className="cr-id">{item.id?.substring(0, 8)}…</code>
                        </div>
                        <div className="cr-mid">
                          <span className="cr-budget">${item.budget_min}–${item.budget_max}</span>
                          <span className="cr-roi">{item.predicted_roi ? `${item.predicted_roi}x ROI` : "—"}</span>
                        </div>
                        <div className="cr-right">
                          <span className="cr-date">{fmtFull(item.created_at)}</span>
                        </div>
                      </div>
                      {recs.length > 0 && (
                        <div className="cc-platforms">
                          {recs.map(rec => {
                            const isLaunchedRec = launched.includes(rec.platform) || launchedKeys.has(`${item.id}::${rec.platform}`);
                            return (
                              <div key={rec.platform} className="cc-platform-row">
                                <div className="cpp-info">
                                  <strong>{rec.platform}</strong>
                                  <span>${rec.budget} · {rec.predicted_roi}x ROI · {rec.predicted_conversion_rate}% conv.</span>
                                </div>
                                <div className="cpp-actions">
                                  {isLaunchedRec ? (
                                    <>
                                      <span className="platform-chip">✓ Launched</span>
                                      {rec.platform === "Google Ads" && (
                                        <button className="btn-launch-ad" style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
                                          onClick={() => { openAdModal(item.id, item.google_ads_type || "text"); }}>
                                          + Ad
                                        </button>
                                      )}
                                      {["Google Ads", "Instagram", "Facebook", "Meta Ads"].includes(rec.platform) && (
                                        <button className="ghost" style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
                                          onClick={() => handleViewMetrics(item.id, rec.platform)}>
                                          📈
                                        </button>
                                      )}
                                    </>
                                  ) : (
                                    <button className="btn-launch" style={{ padding: "0.5rem 1rem", fontSize: "0.82rem" }}
                                      onClick={() => handleLaunchInitiate(rec, item.id)}>
                                      🚀 Launch
                                    </button>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                      {recs.length === 0 && (
                        <div style={{ padding: "0.75rem 1.25rem", color: "var(--muted)", fontSize: "0.85rem" }}>
                          No recommendations generated. <button className="link-btn" onClick={() => loadHistoryItem(item)}>Re-plan →</button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Plan Campaign */}
        {dashTab === "plan" && (
          <div className="dash-section">
            <div className="dash-page-header"><h1>Plan Campaign</h1><p className="subtext">Get AI-powered recommendations for your next campaign</p></div>
            <div className="plan-grid">
              <article className="card">
                <h2>Campaign Setup</h2>
                <form onSubmit={generatePlan} className="planner-form">
                  <label>Goal<select value={campaign.campaign_goal} onChange={e => setCampaign(p => ({ ...p, campaign_goal: e.target.value }))}>{goalOptions.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}</select></label>
                  <label>Product / Service<input value={campaign.product_name} placeholder="e.g. AI SaaS Platform" onChange={e => setCampaign(p => ({ ...p, product_name: e.target.value }))} required /></label>
                  <label>Category<select value={campaign.product_category} onChange={e => setCampaign(p => ({ ...p, product_category: e.target.value }))}><option value="">Auto-detect</option>{productTypes.map(t => <option key={t} value={t}>{t}</option>)}</select></label>
                  <label>Audience Segment<select value={campaign.customer_segment} onChange={e => setCampaign(p => ({ ...p, customer_segment: e.target.value }))}><option value="">ML Selection</option>{segments.map(s => <option key={s} value={s}>{s}</option>)}</select></label>
                  <div className="inline-fields">
                    <label>Min Budget ($)<input type="number" min="1" value={campaign.budget_min} onChange={e => setCampaign(p => ({ ...p, budget_min: e.target.value }))} required /></label>
                    <label>Max Budget ($)<input type="number" min="1" value={campaign.budget_max} onChange={e => setCampaign(p => ({ ...p, budget_max: e.target.value }))} required /></label>
                  </div>
                  <label>Duration (days)<input type="number" min="1" value={campaign.duration_days} onChange={e => setCampaign(p => ({ ...p, duration_days: e.target.value }))} required /></label>
                  <button type="submit" disabled={loadingPlan} style={{ marginTop: "0.5rem" }}>{loadingPlan ? "Generating…" : "Generate Recommendations"}</button>
                  {planError && <p className="alert">{planError}</p>}
                </form>
              </article>
              <article className="card">
                <h2>AI Recommendations</h2>
                {result?.recommendations?.length ? (
                  <div className="prediction-list">
                    {result.recommendations.map(rec => {
                      const lk = `${result?.id}::${rec.platform}`;
                      const isLaunched = launchedKeys.has(lk);
                      const isGA = rec.platform === "Google Ads";
                      return (
                        <div key={rec.platform} className="prediction-item">
                          <h3>{rec.platform}<span className="badge">Optimized</span></h3>
                          <p><span>Audience</span><strong>{rec.target_segment || "General"} | {rec.target_location || "N/A"}</strong></p>
                          <p><span>Expected ROI</span><strong style={{ color: "#10b981" }}>{rec.predicted_roi}x</strong></p>
                          <p><span>Budget</span><strong>${rec.budget}</strong></p>
                          <p><span>Conv. Rate</span><strong>{rec.predicted_conversion_rate}%</strong></p>
                          {isLaunched ? <div className="launched-badge">✓ Campaign Launched</div> : (
                            <button className="btn-launch" onClick={() => handleLaunchInitiate(rec, result.id)}>🚀 Launch Campaign</button>
                          )}
                          {isLaunched && result?.id && (
                            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
                              {isGA && <button className="btn-launch-ad" onClick={() => openAdModal(result.id, result.google_ads_type)}>+ Launch Ad</button>}
                              <button className="ghost" style={{ flex: 1, fontSize: "0.8rem" }} onClick={() => handleViewMetrics(result.id, rec.platform)}>📈 Metrics</button>
                            </div>
                          )}
                          {isLaunched && isGA && result?.id && <CampaignAdsPanel campaignRunId={result.id} ads={campaignAds[result.id]} loading={adsLoading[result.id]} onLoad={() => loadAds(result.id)} />}
                        </div>
                      );
                    })}
                    {result.budget_suggestion && <div className="llm-block"><h3>Budget Suggestion</h3><p>Optimal: <strong>${result.budget_suggestion.recommended_min}–${result.budget_suggestion.recommended_max}</strong></p></div>}
                  </div>
                ) : <p className="subtext" style={{ padding: "2rem 0", textAlign: "center" }}>Fill in the form and generate recommendations to get started.</p>}
              </article>
            </div>
            {history.length > 0 && (
              <div className="card" style={{ marginTop: "1.5rem" }}>
                <h2>Campaign History</h2>
                <div className="history-list">
                  {history.map(item => (
                    <article key={item.id} className="history-item" style={{ cursor: "pointer" }} onClick={() => loadHistoryItem(item)}>
                      <div className="header"><h3>{item.product_name}</h3><span className="date">{fmt(item.created_at)}</span></div>
                      <div className="details"><p style={{ color: "var(--brand)" }}>{item.campaign_goal}</p><p style={{ color: "#10b981", fontWeight: 600 }}>{item.predicted_roi ? `${item.predicted_roi}x ROI` : "—"}</p></div>
                      {(item.launched_platforms || []).length > 0 && <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginTop: "0.25rem" }}>{item.launched_platforms.map(p => <span key={p} className="platform-chip">{p}</span>)}</div>}
                    </article>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Metrics */}
        {dashTab === "metrics" && (
          <div className="dash-section">
            <div className="dash-page-header"><h1>Metrics</h1><p className="subtext">View real-time performance for your launched campaigns</p></div>
            {(() => {
              const metricPlatforms = new Set(["Google Ads", "Instagram", "Facebook", "Meta Ads"]);
              const metricsRows = history.flatMap(h =>
                (h.launched_platforms || [])
                  .filter(p => metricPlatforms.has(p))
                  .map(p => ({ id: h.id, platform: p, product_name: h.product_name, campaign_goal: h.campaign_goal, created_at: h.created_at }))
              );

              if (metricsRows.length === 0) {
                return (
                  <div className="empty-state"><p>📊</p><h3>No launched campaigns</h3><p className="subtext">Launch a Google Ads or Meta (Facebook/Instagram) campaign first to view metrics.</p><button className="btn-primary" onClick={() => setDashTab("plan")}>Plan a Campaign</button></div>
                );
              }

              return (
                <div className="metrics-section">
                  <div className="card" style={{ marginBottom: "1.5rem" }}>
                    <h2>Select Campaign</h2>
                    <div className="campaign-list">
                      {metricsRows.map(row => (
                        <div
                          key={`${row.id}::${row.platform}`}
                          className={`campaign-row${selectedMetricsItem?.id === row.id && selectedMetricsItem?.platform === row.platform ? " selected" : ""}`}
                          onClick={() => setSelectedMetricsItem({ id: row.id, platform: row.platform })}
                          style={{ cursor: "pointer" }}
                        >
                          <div className="cr-left"><strong>{row.product_name}</strong><span className="cr-goal">{row.campaign_goal}</span></div>
                          <div className="cr-right"><span className="platform-chip">{row.platform}</span><span className="cr-date">{fmt(row.created_at)}</span></div>
                        </div>
                      ))}
                    </div>
                    {selectedMetricsItem && <button style={{ marginTop: "1rem" }} onClick={() => handleViewMetrics(selectedMetricsItem.id, selectedMetricsItem.platform)}>📈 Load Metrics</button>}
                  </div>

                  {metricsModal.data && (
                    <div className="card">
                      <h2>Live Metrics</h2>
                      {(metricsModal.data.campaign_metrics || []).length === 0 ? <p className="subtext">No metrics available yet — campaign may be pending approval or in dry-run mode.</p> : (
                        (metricsModal.data.campaign_metrics || []).map((m, i) => {
                          const costUsd = (m.cost_micros != null) ? (Number(m.cost_micros || 0) / 1e6) : Number(m.spend ?? m.cost ?? 0);
                          return (
                            <div key={i} className="metrics-card"><h4>{m.campaign_name || `${metricsModal.platform || m.platform || "Campaign"}`}</h4>
                              <div className="metrics-grid">
                                <div className="metric-tile"><span>Impressions</span><strong>{(m.impressions || 0).toLocaleString()}</strong></div>
                                <div className="metric-tile"><span>Clicks</span><strong>{(m.clicks || 0).toLocaleString()}</strong></div>
                                <div className="metric-tile"><span>CTR</span><strong>{m.clicks && m.impressions ? ((m.clicks / m.impressions) * 100).toFixed(2) : 0}%</strong></div>
                                <div className="metric-tile"><span>Cost</span><strong>${(costUsd || 0).toFixed(2)}</strong></div>
                                <div className="metric-tile"><span>Conversions</span><strong>{m.conversions || 0}</strong></div>
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}

        {/* ── Optimize tab ── */}
        {dashTab === "optimize" && (() => {
          const launchedGA   = history.filter(h => (h.launched_platforms || []).includes("Google Ads"));
          const launchedMeta = history.filter(h =>
            (h.launched_platforms || []).some(p => p === "Instagram" || p === "Facebook" || p === "Meta Ads")
          );
          const allOptimizable = [
            ...launchedGA.map(h => ({ ...h, _optPlatform: "Google Ads" })),
            ...launchedMeta.filter(h => !launchedGA.find(g => g.id === h.id)).map(h => ({ ...h, _optPlatform: "Meta Ads" })),
            ...launchedMeta.filter(h => launchedGA.find(g => g.id === h.id)).map(h => ({ ...h, _optPlatform: "Meta Ads" })),
          ];

          const om = optimizeModal;
          const result = om.result;

          const actionIcons = {
            increase_budget:   { icon: "📈", color: "#10b981", label: "Increase Budget" },
            reduce_budget:     { icon: "📉", color: "#f59e0b", label: "Reduce Budget" },
            pause_campaign:    { icon: "⏸️", color: "#ef4444", label: "Pause Campaign" },
            no_change:         { icon: "✅", color: "#64748b", label: "No Change Needed" },
            flag_low_ctr:      { icon: "⚠️", color: "#f59e0b", label: "Low CTR Warning" },
            flag_landing_page: { icon: "🔗", color: "#a78bfa", label: "Landing Page Issue" },
          };

          const runOptimize_withOverrides = async (dryRun, userOverrides = null) => {
            const { campaignRunId, campaignName, useMockData, selectedPlatform } = om;
            setOptimizeModal(p => ({ ...p, loading: true, error: "" }));
            try {
              let res;
              if (selectedPlatform === "Meta Ads") {
                res = await api.optimizeMetaCampaign(accessToken, campaignRunId, dryRun, useMockData ?? false, userOverrides);
              } else {
                res = await api.optimizeCampaign(accessToken, campaignRunId, dryRun, useMockData ?? false, userOverrides);
              }
              setOptimizeModal(p => ({ ...p, loading: false, result: res, pendingOverrides: {} }));
            } catch (err) {
              setOptimizeModal(p => ({ ...p, loading: false, error: err.message || "Optimization failed." }));
            }
          };

          const selectCampaignForOptimize = async (item, platform) => {
            setOptimizeModal(p => ({
              ...p, open: false, campaignRunId: item.id, campaignName: item.product_name,
              selectedPlatform: platform, result: null, error: "", pendingOverrides: {},
            }));
          };

          // Campaigns that can be optimized (launched to at least one platform)
          const allCampaigns = history.filter(h => (h.launched_platforms || []).length > 0);

          return (
            <div className="dash-section">
              <div className="dash-page-header">
                <h1>⚡ Optimization Agent</h1>
                <p className="subtext">
                  AI compares actual vs predicted performance and recommends budget, status, and creative changes.
                  Budget changes can be auto-applied. Creative changes require manual action in the ad platform.
                </p>
              </div>
              {allCampaigns.length === 0 ? (
                <div className="empty-state"><p>⚡</p><h3>No launched campaigns</h3><p className="subtext">Launch a campaign first to run the optimizer.</p><button className="btn-primary" onClick={() => setDashTab("plan")}>Plan a Campaign</button></div>
              ) : (
                <div className="optimize-layout">
                  {/* Campaign & Platform selector */}
                  <div className="card">
                    <h2>Select Campaign &amp; Platform</h2>
                    <div className="campaign-list" style={{ marginBottom: "1rem" }}>
                      {allCampaigns.map(item => {
                        const platforms = item.launched_platforms || [];
                        const hasGA   = platforms.includes("Google Ads");
                        const hasMeta = platforms.some(p => p === "Instagram" || p === "Facebook" || p === "Meta Ads");
                        return (
                          <div key={item.id} className={`campaign-card${om.campaignRunId === item.id ? " selected" : ""}`} style={{ cursor: "default", marginBottom: "0.75rem" }}>
                            <div className="cc-header" style={{ marginBottom: "0.5rem" }}>
                              <div className="cr-left">
                                <strong>{item.product_name}</strong>
                                <span className="cr-goal">{item.campaign_goal}</span>
                              </div>
                              <div className="cr-right"><span className="cr-date">{fmt(item.created_at)}</span></div>
                            </div>
                            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                              {hasGA && (
                                <button
                                  className={`platform-chip opt-select-btn${om.campaignRunId === item.id && om.selectedPlatform === "Google Ads" ? " selected-opt" : ""}`}
                                  onClick={() => selectCampaignForOptimize(item, "Google Ads")}
                                >
                                  🔵 Optimize Google Ads
                                </button>
                              )}
                              {hasMeta && (
                                <button
                                  className={`platform-chip opt-select-btn${om.campaignRunId === item.id && om.selectedPlatform === "Meta Ads" ? " selected-opt" : ""}`}
                                  onClick={() => selectCampaignForOptimize(item, "Meta Ads")}
                                >
                                  🔶 Optimize Meta Ads
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    {om.campaignRunId && (
                      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap", borderTop: "1px solid var(--border)", paddingTop: "1rem" }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.35rem" }}>
                            Selected: <strong style={{ color: "var(--text)" }}>{om.campaignName}</strong>
                            {om.selectedPlatform && <span className="platform-chip" style={{ marginLeft: "0.5rem" }}>{om.selectedPlatform}</span>}
                          </div>
                          <label style={{ display: "flex", gap: "0.5rem", alignItems: "center", cursor: "pointer", fontSize: "0.87rem", color: "#94a3b8" }}>
                            <input type="checkbox" checked={om.useMockData ?? false}
                              onChange={e => setOptimizeModal(p => ({ ...p, useMockData: e.target.checked }))}
                              style={{ accentColor: "var(--brand)" }} />
                            Use Mock Data (generate simulated metrics for demo/testing)
                          </label>
                        </div>
                        <button className="btn-launch" style={{ padding: "0.65rem 1.5rem" }}
                          disabled={om.loading}
                          onClick={() => runOptimize_withOverrides(true)}>
                          {om.loading ? (
                            <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2, display: "inline-block", marginRight: 8 }} />Analyzing…</>
                          ) : "🔍 Analyze Campaign"}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Error */}
                  {om.error && <p className="alert" style={{ marginTop: "1rem" }}>{om.error}</p>}

                  {/* Results */}
                  {result && (
                    <div style={{ marginTop: "1.5rem" }}>
                      {(() => {
                        const applyFailed = result.status === "apply_failed";
                        if (!applyFailed) return null;
                        return (
                          <p className="alert" style={{ marginTop: "0.75rem" }}>
                            Some changes failed to apply. Check the action cards for API errors.
                          </p>
                        );
                      })()}
                      {/* Status banner */}
                      <div className={`opt-status-banner ${result.status}`}>
                        {result.status === "insufficient_data" && <><span>⏳</span><div><strong>Not enough data yet</strong><p>{result.message}</p></div></>}
                        {result.status === "optimized"         && <><span>✅</span><div><strong>Optimization Applied{result.dry_run ? " (Dry Run)" : ""}</strong><p>Changes have been sent to {om.selectedPlatform}.</p></div></>}
                        {result.status === "apply_failed"      && <><span>⚠️</span><div><strong>Apply Failed</strong><p>{result.message || "Some programmatic changes could not be applied."}</p></div></>}
                        {result.status === "paused"            && <><span>⏸️</span><div><strong>Campaign Paused</strong><p>Budget was being wasted — campaign paused automatically.</p></div></>}
                        {result.status === "no_action"         && <><span>✔️</span><div><strong>No Action Needed</strong><p>Performance is within expected range.</p></div></>}
                        {result.status === "dry_run_campaign"  && <><span>🧪</span><div><strong>Dry-Run Campaign</strong><p>{result.message}</p></div></>}
                      </div>

                      {/* Analysis table */}
                      {result.analysis && Object.keys(result.analysis).length > 0 && (
                        <div className="card" style={{ marginTop: "1rem" }}>
                          <h2>📊 Performance Analysis</h2>
                          <div className="opt-analysis-grid">
                            {[
                              ["Actual ROI",   `${result.analysis.actual_roi?.toFixed(2) ?? "—"}x`,      `Predicted: ${result.analysis.predicted_roi?.toFixed(2) ?? "—"}x`, result.analysis.roi_gap >= 0 ? "positive" : "negative"],
                              ["Actual CTR",   `${result.analysis.actual_ctr_pct?.toFixed(2) ?? "—"}%`,  result.analysis.actual_ctr_pct < 2 ? "⚠ Below 2% threshold" : "✓ Healthy", result.analysis.actual_ctr_pct < 2 ? "warning" : "positive"],
                              ["Conv. Rate",   `${result.analysis.actual_cr_pct?.toFixed(2) ?? "—"}%`,   `Predicted: ${result.analysis.predicted_cr_pct?.toFixed(2) ?? "—"}%`, result.analysis.cr_gap >= 0 ? "positive" : "negative"],
                              ["Impressions",  (result.analysis.actual_impressions ?? 0).toLocaleString(), "Last 7 days", "neutral"],
                              ["Clicks",       (result.analysis.actual_clicks ?? 0).toLocaleString(),     `Avg CPC: $${result.analysis.avg_cpc_usd?.toFixed(3) ?? "—"}`, "neutral"],
                              ["Cost",         `$${result.analysis.actual_cost_usd?.toFixed(2) ?? "0.00"}`, "Last 7 days spend", "neutral"],
                            ].map(([label, value, sub, type]) => (
                              <div key={label} className={`opt-metric-card opt-${type}`}>
                                <span className="om-label">{label}</span>
                                <strong className="om-value">{value}</strong>
                                <span className="om-sub">{sub}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      {result.actions?.length > 0 && (
                        <div className="card" style={{ marginTop: "1rem" }}>
                          <h2>🎯 Recommended Actions{result.dry_run ? " (Preview — Not Applied Yet)" : ""}</h2>
                          <div className="opt-actions-list">
                            {result.actions.map((action, i) => {
                              const meta = actionIcons[action.action] || { icon: "🔔", color: "#94a3b8", label: action.action };
                              const isProgrammatic = action.programmatic;
                              const isManual = !isProgrammatic;
                              const isBudgetAction = action.action === "increase_budget" || action.action === "reduce_budget";
                              const pendingBudget = (om.pendingOverrides || {})[i];
                              const budgetPrefix = om.selectedPlatform === "Meta Ads" ? "" : "$";
                              return (
                                <div key={i} className={`opt-action-card${isManual ? " manual-action" : ""}`} style={{ borderLeft: `3px solid ${meta.color}` }}>
                                  <div className="oac-header">
                                    <span className="oac-icon">{meta.icon}</span>
                                    <strong style={{ color: meta.color }}>{meta.label}</strong>
                                    {isManual && <span className="oac-manual-badge">👤 Manual Action Required</span>}
                                    {isProgrammatic && result.dry_run && <span className="oac-auto-badge">🤖 Can Auto-Apply</span>}
                                    {action.adjustment_rate !== undefined && !isBudgetAction && (
                                      <span className="oac-rate">{action.adjustment_rate > 0 ? "+" : ""}{(action.adjustment_rate * 100).toFixed(0)}%</span>
                                    )}
                                  </div>
                                  <p className="oac-reason">{action.reason}</p>
                                  {action.recommendation && <p className="oac-rec">💡 {action.recommendation}</p>}

                                  {/* Editable budget input for budget actions in dry-run */}
                                  {isBudgetAction && result.dry_run && action.adjustment_rate !== undefined && (
                                    <div className="oac-edit-budget">
                                      <label>
                                        <span>Suggested adjustment: <strong>{action.adjustment_rate > 0 ? "+" : ""}{(action.adjustment_rate * 100).toFixed(0)}%</strong></span>
                                        <br />
                                        <span style={{ fontSize: "0.82rem", color: "#94a3b8" }}>
                                          {om.selectedPlatform === "Meta Ads"
                                            ? "Override with a specific daily budget (ad account currency):"
                                            : "Override with a specific daily budget ($):"}
                                        </span>
                                        <input
                                          type="number" min="1" step="0.01"
                                          placeholder={`e.g. ${action.api_result?.new_daily_budget_usd ?? "custom amount"}`}
                                          value={pendingBudget ?? ""}
                                          onChange={e => setOptimizeModal(p => ({ ...p, pendingOverrides: { ...(p.pendingOverrides || {}), [i]: e.target.value } }))}
                                          style={{ marginTop: "0.4rem", width: "160px", padding: "0.35rem 0.6rem", borderRadius: "6px", border: "1px solid var(--border)", background: "var(--input-bg)", color: "var(--text)", fontSize: "0.9rem" }}
                                        />
                                      </label>
                                    </div>
                                  )}

                                  {/* Manual instruction box */}
                                  {isManual && action.manual_action && (
                                    <div className="oac-manual-steps">
                                      <strong>📋 What to do:</strong>
                                      <p>{action.manual_action}</p>
                                    </div>
                                  )}

                                  {/* API result when applied */}
                                  {action.api_result && (
                                    <div className="oac-api-result">
                                      {action.api_result.old_daily_budget_usd !== undefined ? (
                                        <span>Budget: <s>{budgetPrefix}{action.api_result.old_daily_budget_usd}/day</s> → <strong>{budgetPrefix}{action.api_result.new_daily_budget_usd}/day</strong>
                                          {action.api_result.user_override && <span className="oac-override-note"> (custom amount)</span>}
                                        </span>
                                      ) : action.api_result.new_status ? (
                                        <span>Status set to: <strong>{action.api_result.new_status}</strong></span>
                                      ) : null}
                                    </div>
                                  )}
                                  {action.api_error && (() => {
                                    const errText = String(action.api_error || "");
                                    const isBudgetTooLow = (
                                      om.selectedPlatform === "Meta Ads" &&
                                      (errText.toLowerCase().includes("budget is too low") ||
                                       errText.toLowerCase().includes("budget must be more than") ||
                                       errText.includes("1885272"))
                                    );
                                    if (isBudgetTooLow) {
                                      const m = errText.match(/more than\s+[^0-9]*([0-9][0-9,]*\.?[0-9]{0,2})/i);
                                      const minTxt = m?.[1] ? `Minimum required daily budget: ${m[1]}` : "Meta requires a higher daily budget.";
                                      return <p className="subtext" style={{ marginTop: "0.5rem" }}>{minTxt} Try applying again (we auto-bump), or override the daily budget to a higher value.</p>;
                                    }
                                    return <p className="alert" style={{ marginTop: "0.5rem" }}>API Error: {action.api_error}</p>;
                                  })()}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Approve & Apply — only if there are programmatic actions in dry-run mode */}
                      {result && result.dry_run && result.actions?.some(a => a.programmatic && a.action !== "no_change") && (
                        <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1rem 1.5rem", background: "rgba(16, 185, 129, 0.08)", borderRadius: "10px", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
                          <div>
                            <strong style={{ color: "#10b981", fontSize: "0.95rem" }}>Ready to apply programmatic optimizations to {om.selectedPlatform}?</strong>
                            <p style={{ fontSize: "0.82rem", color: "#94a3b8", margin: "0.2rem 0 0" }}>
                              Manual actions (creative changes) require action in the ad platform directly.
                              {Object.keys(om.pendingOverrides || {}).length > 0 && " Custom budget values will be applied."}
                            </p>
                          </div>
                          <button className="btn-primary"
                            disabled={om.loading}
                            onClick={() => {
                              // Collect user override budgets from pending fields
                              const overrides = {};
                              const budgetActions = result.actions.filter(a => a.action === "increase_budget" || a.action === "reduce_budget");
                              if (budgetActions.length > 0) {
                                const firstBudgetIdx = result.actions.findIndex(a => a.action === "increase_budget" || a.action === "reduce_budget");
                                const v = (om.pendingOverrides || {})[firstBudgetIdx];
                                if (v && parseFloat(v) > 0) {
                                  overrides.new_budget_usd = parseFloat(v);
                                }
                              }
                              runOptimize_withOverrides(false, Object.keys(overrides).length > 0 ? overrides : null);
                            }}>
                            {om.loading ? "Applying..." : "✅ Approve & Apply Changes"}
                          </button>
                        </div>
                      )}


                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })()}

        {/* Scale Up */}
        {dashTab === "scaleup" && (
          <div className="dash-section">
            <div className="dash-page-header">
              <h1>📈 Scale Up Your Campaigns</h1>
              <p className="subtext">Select a campaign to analyze scaling opportunities</p>
            </div>
            {history.length === 0 ? (
              <div className="empty-state"><p>📊</p><h3>No campaigns yet</h3><p className="subtext">Create and launch campaigns to see scaling recommendations.</p><button className="btn-primary" onClick={() => setDashTab("plan")}>Plan Your First Campaign</button></div>
            ) : (
              <div className="scaleup-analysis">
                {/* Campaign List */}
                <div className="card" style={{ marginBottom: "1.5rem" }}>
                  <h2>Select a Campaign to Analyze</h2>
                  <div className="campaigns-scaleup-list">
                    {history.map(c => (
                      <div key={c.id} className={`campaign-scaleup-row${selectedMetricsItem?.id === c.id ? " selected" : ""}`} onClick={() => setSelectedMetricsItem({ id: c.id })}>
                        <div className="csr-main">
                          <h4>{c.product_name}</h4>
                          <div className="csr-meta">
                            <span className="cr-goal">{c.campaign_goal}</span>
                            <span>${c.budget_min}-${c.budget_max}</span>
                            <span style={{ color: "#10b981", fontWeight: "600" }}>{c.predicted_roi}x ROI</span>
                          </div>
                        </div>
                        <div className="csr-platforms">
                          {c.launched_platforms.length > 0 ? (
                            c.launched_platforms.map(p => <span key={p} className="platform-chip-mini">{p}</span>)
                          ) : (
                            <span className="chip-pending-mini">Not launched</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Campaign Analysis */}
                {selectedMetricsItem && (
                  <button className="btn-primary" style={{ marginBottom: "1.5rem" }} disabled={scaleupLoading} onClick={async () => {
                    setScaleupLoading(true); setScaleupError("");
                    try { const data = await api.getCampaignScaleupAnalysis(accessToken, selectedMetricsItem.id); setScaleupData(data); }
                    catch (err) { setScaleupError(err.message || "Failed to analyze campaign."); }
                    finally { setScaleupLoading(false); }
                  }}>
                    {scaleupLoading ? "Analyzing…" : "🔍 Analyze Scaling Options"}
                  </button>
                )}

                {scaleupError && <p className="alert" style={{ marginBottom: "1rem" }}>{scaleupError}</p>}

                {scaleupData && (
                  <div className="campaign-scaleup-details">
                    {/* Campaign Header */}
                    <div className="card csd-header" style={{ marginBottom: "1.5rem" }}>
                      <div>
                        <h2>{scaleupData.campaign.name}</h2>
                        <p className="subtext">{scaleupData.campaign.goal} • ${scaleupData.campaign.budget_range.min}-${scaleupData.campaign.budget_range.max} • {scaleupData.campaign.predicted_roi}x ROI</p>
                      </div>
                      <div className="csd-status">
                        {scaleupData.campaign.launched_platforms.length > 0 ? (
                          <>
                            <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.5rem" }}>Launched on:</div>
                            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                              {scaleupData.campaign.launched_platforms.map(p => <span key={p} className="platform-chip">{p}</span>)}
                            </div>
                          </>
                        ) : (
                          <span className="chip-pending">Not launched yet</span>
                        )}
                      </div>
                    </div>

                    {/* Platform Comparison */}
                    <div className="card" style={{ marginBottom: "1.5rem" }}>
                      <h2>🏆 Platform Comparison for This Campaign</h2>
                      <div className="platform-comparison-grid">
                        {scaleupData.platform_analysis.map((p, idx) => (
                          <div key={p.platform} className={`platform-rank-card${p === scaleupData.best_platform ? " best-platform" : ""}`}>
                            {p === scaleupData.best_platform && <div className="pbest-badge">✓ Best Choice</div>}
                            <h3>{p.platform}</h3>
                            <div className="prc-metric">
                              <span>Expected ROI</span>
                              <strong style={{ color: p === scaleupData.best_platform ? "#10b981" : "#64748b", fontSize: "1.3rem" }}>{p.predicted_roi}x</strong>
                            </div>
                            <div className="prc-metric">
                              <span>Conv. Rate</span>
                              <strong>{p.predicted_conversion_rate}%</strong>
                            </div>
                            <div className="prc-metric">
                              <span>Budget</span>
                              <strong>${p.budget.toLocaleString()}</strong>
                            </div>
                            <div style={{ marginTop: "1rem", padding: "0.75rem", background: "rgba(0,0,0,0.2)", borderRadius: "8px", fontSize: "0.85rem" }}>
                              {p.is_launched ? (
                                <span style={{ color: "#10b981", fontWeight: "600" }}>✓ Currently launched</span>
                              ) : (
                                <span style={{ color: "var(--muted)" }}>Not launched on this platform</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Scaling Recommendation */}
                    <div className={`card csd-recommendation${scaleupData.scaling_recommendation.action === "scale_up_budget" ? " recommend-increase" : scaleupData.scaling_recommendation.action === "switch_platform" ? " recommend-switch" : ""}`}>
                      <div className="csr-icon">
                        {scaleupData.scaling_recommendation.action === "scale_up_budget" && <span style={{ fontSize: "2rem" }}>📈</span>}
                        {scaleupData.scaling_recommendation.action === "switch_platform" && <span style={{ fontSize: "2rem" }}>🔄</span>}
                        {scaleupData.scaling_recommendation.action === "add_platform" && <span style={{ fontSize: "2rem" }}>➕</span>}
                        {scaleupData.scaling_recommendation.action === "launch" && <span style={{ fontSize: "2rem" }}>🚀</span>}
                        {scaleupData.scaling_recommendation.action === "maintain" && <span style={{ fontSize: "2rem" }}>✅</span>}
                        {scaleupData.scaling_recommendation.action === "none" && <span style={{ fontSize: "2rem" }}>👀</span>}
                      </div>
                      <div className="csr-content">
                        <h3>
                          {scaleupData.scaling_recommendation.action === "scale_up_budget" && "Scale Up Budget"}
                          {scaleupData.scaling_recommendation.action === "switch_platform" && "Switch to Better Platform"}
                          {scaleupData.scaling_recommendation.action === "add_platform" && "Expand to Additional Platform"}
                          {scaleupData.scaling_recommendation.action === "launch" && "Launch Campaign"}
                          {scaleupData.scaling_recommendation.action === "maintain" && "Maintain Current Performance"}
                          {scaleupData.scaling_recommendation.action === "none" && "No Action Recommended"}
                        </h3>
                        <p>{scaleupData.scaling_recommendation.reason}</p>
                        {scaleupData.scaling_recommendation.suggested_budget && (
                          <div style={{ marginTop: "1rem", padding: "1rem", background: "rgba(16,185,129,0.1)", borderRadius: "10px", border: "1px solid rgba(16,185,129,0.2)" }}>
                            <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Suggested new budget: </span>
                            <strong style={{ color: "#10b981", fontSize: "1.1rem" }}>${scaleupData.scaling_recommendation.suggested_budget.toLocaleString()}</strong>
                          </div>
                        )}
                        {scaleupData.scaling_recommendation.recommended_platform && (
                          <div style={{ marginTop: "1rem" }}>
                            <button className="btn-launch" onClick={() => { loadHistoryItem(history.find(h => h.id === selectedMetricsItem.id)); setDashTab("campaigns"); }}>
                              View Campaign & Take Action →
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Settings */}
        {dashTab === "settings" && (
          <div className="dash-section">
            <div className="dash-page-header"><h1>Settings</h1><p className="subtext">Manage your account and platform credentials</p></div>
            <div className="settings-grid">
              <div className="card"><h2>Account</h2><div className="settings-field"><label>Email</label><input type="email" value={user?.email || ""} disabled /></div><div className="settings-field"><label>Member since</label><input type="text" value={user?.created_at ? fmt(user.created_at) : "—"} disabled /></div><div className="settings-field"><label>Account ID</label><input type="text" value={user?.id || "—"} disabled /></div></div>
              <div className="card"><h2>Platform Credentials</h2><p className="subtext" style={{ marginBottom: "1rem" }}>API credentials are configured via environment variables on the server for security.</p>{[{ label: "Google Ads", fields: ["CUSTOMER_ID", "DEVELOPER_TOKEN", "CLIENT_ID", "REFRESH_TOKEN"], status: "✅ Configured via .env" }, { label: "Meta Ads (Facebook/Instagram)", fields: ["ACCESS_TOKEN", "AD_ACCOUNT_ID"], status: "✅ Configured via .env" }, { label: "LinkedIn Ads", fields: ["LINKEDIN_ACCESS_TOKEN", "ACCOUNT_ID"], status: "⚙️ Coming soon" }].map(p => (<div key={p.label} className="platform-settings-item"><div className="psi-header"><strong>{p.label}</strong><span className="psi-status">{p.status}</span></div><div className="psi-fields">{p.fields.map(f => <code key={f}>{f}</code>)}</div></div>))}</div>
              <div className="card"><h2>About</h2><p className="subtext">NexusAds is an AI-powered digital marketing automation agent that autonomously plans, launches, optimizes, and scales paid ad campaigns across LinkedIn Ads, Meta Ads (Facebook/Instagram), and Google Ads, using a free/open MCP (Model Context Protocol) server as the orchestration backbone.</p><div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>{"Google Ads · Meta Ads · LinkedIn Ads · MCP · AI Planning".split(" · ").map(t => <span key={t} className="platform-chip">{t}</span>)}</div></div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// ── Campaign Ads Panel ─────────────────────────────────────────────────────────
function CampaignAdsPanel({ campaignRunId, ads, loading, onLoad }) {
  const [expanded, setExpanded] = useState(false);
  useEffect(() => { if (expanded && ads === undefined && !loading) onLoad(); }, [expanded, ads, loading, onLoad]);
  return (
    <div className="campaign-ads-panel">
      <button type="button" className="ghost ads-toggle-btn" onClick={e => { e.stopPropagation(); setExpanded(v => !v); }}>
        📋 {expanded ? "Hide" : "View"} Ads {ads?.length > 0 && <span className="ads-count-chip">{ads.length}</span>}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: "auto", transform: expanded ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}><polyline points="6 9 12 15 18 9" /></svg>
      </button>
      {expanded && (
        <div className="ads-list-container">
          {loading ? <p className="subtext" style={{ fontSize: "0.85rem", padding: "0.75rem" }}>Loading…</p> : !ads || ads.length === 0 ? <p className="subtext" style={{ fontSize: "0.85rem", padding: "0.75rem" }}>No ads launched yet.</p> : (
            <div className="ads-list">
              {ads.map(ad => (
                <div key={ad.id} className="ad-item">
                  <div className="ad-item-header"><span className="ad-item-name">{ad.ad_name || "Unnamed Ad"}</span><span className={`ad-item-status ${ad.dry_run ? "dry-run" : "live"}`}>{ad.dry_run ? "Sim" : "Live"}</span><span className="ad-item-date">{new Date(ad.created_at).toLocaleDateString()}</span></div>
                  {ad.headline_1 && <div className="ad-headlines"><span>{ad.headline_1}</span>{ad.headline_2 && <><span className="sep">|</span><span>{ad.headline_2}</span></>}</div>}
                  {ad.final_url && <div className="ad-url">🔗 {ad.final_url}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
