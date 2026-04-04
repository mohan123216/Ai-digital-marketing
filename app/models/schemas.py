# app/models/schemas.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import date

class CampaignGoal(str, Enum):
    ROI = "roi"
    LEADS = "leads"
    TRAFFIC = "traffic"
    CONVERSIONS = "conversions"
    BRAND_AWARENESS = "brand_awareness"
    ENGAGEMENT = "engagement"

class PlatformType(str, Enum):
    GOOGLE_ADS = "Google Ads"
    META_ADS = "Meta Ads"
    LINKEDIN_ADS = "LinkedIn Ads"
    INSTAGRAM = "Instagram"
    FACEBOOK = "Facebook"
    YOUTUBE = "YouTube"
    EMAIL = "Email"
    ALL = "All"

class TargetAudience(BaseModel):
    age_range: Optional[str] = Field(None, description="e.g., '25-34', '35-44'")
    gender: Optional[str] = Field(None, description="Male, Female, All")
    interests: Optional[List[str]] = Field(default=[], description="User interests")
    location: Optional[str] = Field(None, description="City or country")
    language: Optional[str] = Field(None, description="Preferred language")
    customer_segment: Optional[str] = Field(None, description="e.g., Tech Enthusiasts, Health & Wellness")

class BudgetRange(BaseModel):
    min: float = Field(..., gt=0, description="Minimum budget in USD")
    max: float = Field(..., gt=0, description="Maximum budget in USD")

    @property
    def average(self) -> float:
        return (self.min + self.max) / 2

    @property
    def range_size(self) -> float:
        return self.max - self.min

class CampaignInput(BaseModel):
    campaign_goal: CampaignGoal
    product_name: str = Field(..., min_length=1, max_length=100)
    product_category: Optional[str] = Field(None, description="e.g., Tech, Fashion, Health")
    target_audience: TargetAudience
    budget_range: BudgetRange
    platform_preference: Optional[List[PlatformType]] = None
    duration_days: Optional[int] = Field(30, ge=1, le=365)
    start_date: Optional[date] = None
    additional_context: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("campaign_goal", mode="before")
    @classmethod
    def normalize_campaign_goal(cls, value):
        """Allow case-insensitive campaign_goal inputs such as ROI/Conversions."""
        if isinstance(value, str):
            return value.strip().lower().replace(" ", "_")
        return value

class CampaignRecommendation(BaseModel):
    platform: str
    target_location: str
    target_segment: str
    target_age_group: str
    target_gender: Optional[str] = None
    target_language: Optional[str] = None
    target_interests: Optional[List[str]] = []
    budget: str
    predicted_roi: float
    predicted_conversion_rate: float
    confidence: str
    rationale: str
    risk_level: str  # Low, Medium, High
    expected_impressions: Optional[int] = None
    expected_clicks: Optional[int] = None

class PerformanceExpectations(BaseModel):
    best_case_roi: float
    average_case_roi: float
    worst_case_roi: float
    best_case_conversion: float
    average_case_conversion: float
    worst_case_conversion: float
    confidence_interval: str
    expected_roi_range: str
    expected_conversion_range: str

class ABTestPlan(BaseModel):
    recommended: bool
    channels_to_test: List[str]
    budget_per_channel: str
    test_duration_days: int
    success_metric: str
    minimum_detectable_effect: float

class RecommendationResponse(BaseModel):
    campaign_id: str
    timestamp: str
    recommendations: List[CampaignRecommendation]
    top_recommendation: CampaignRecommendation
    performance_expectations: PerformanceExpectations
    ab_testing_plan: ABTestPlan
    insights: List[str]
    data_quality_score: float
    model_confidence: float

    model_config = ConfigDict(from_attributes=True)

class ModelMetrics(BaseModel):
    roi_model_r2: float
    roi_model_rmse: float
    conversion_model_r2: float
    conversion_model_rmse: float
    feature_importance: Dict[str, float]
    last_trained: str
    data_records: int


class UserProfile(BaseModel):
    id: str
    email: Optional[str] = None
    created_at: Optional[str] = None


class AuthCredentials(BaseModel):
    email: str = Field(..., min_length=5, max_length=320)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class CampaignHistoryItem(BaseModel):
    id: str
    created_at: str
    product_name: str
    campaign_goal: str
    budget_min: float
    budget_max: float
    top_platform: Optional[str] = None
    predicted_roi: Optional[float] = None
    output: Dict[str, Any]
    launched_platforms: List[str] = Field(default_factory=list)
    google_ads_type: Optional[str] = None
    meta_campaign_id: Optional[str] = None
    meta_adset_id: Optional[str] = None
    meta_platform: Optional[str] = None
    meta_assets: Optional[Dict[str, Any]] = None


class GoogleAdsLaunchRequest(BaseModel):
    campaign_id: str
    recommendation: Dict[str, Any]
    ad_type: str = Field(default="text", description="Type of ad: 'text', 'image', or 'video'")
    customer_id: Optional[str] = None
    budget_resource_name: Optional[str] = None
    login_customer_id: Optional[str] = None
    campaign_name: Optional[str] = None
    dry_run: bool = False


class GoogleAdsLaunchStatusRequest(BaseModel):
    campaign_id: str
    recommendation: Dict[str, Any]


class MetaAdsLaunchRequest(BaseModel):
    campaign_id: str
    recommendation: Dict[str, Any]
    ad_account_id: Optional[str] = None
    dry_run: bool = False


class MetaAdsLaunchStatusRequest(BaseModel):
    campaign_id: str
    recommendation: Dict[str, Any]


# ─── Ad Launch Schemas ──────────────────────────────────────────────────────

class LaunchAdRequest(BaseModel):
    """Payload for launching a new ad inside an already-launched campaign."""
    ad_name: Optional[str] = Field(None, description="Friendly name for this ad (optional)")
    ad_type: str = Field("text", description="Ad type: 'text', 'image', or 'video'")
    headline_1: Optional[str] = Field(None, max_length=30, description="Headline 1 (max 30 chars)")
    headline_2: Optional[str] = Field(None, max_length=30, description="Headline 2 (max 30 chars)")
    headline_3: Optional[str] = Field(None, max_length=30, description="Headline 3 (max 30 chars)")
    description_1: Optional[str] = Field(None, max_length=90, description="Description 1 (max 90 chars)")
    description_2: Optional[str] = Field(None, max_length=90, description="Description 2 (max 90 chars)")
    final_url: str = Field(..., description="Landing page URL")
    display_url_path_1: Optional[str] = Field(None, max_length=15, description="Display path 1 (max 15 chars)")
    display_url_path_2: Optional[str] = Field(None, max_length=15, description="Display path 2 (max 15 chars)")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords to add to the Ad Group")
    long_headline: Optional[str] = Field(None, max_length=90, description="Long headline for image/display ads")
    business_name: Optional[str] = Field(None, max_length=25, description="Business name shown on image ads")
    call_to_action: Optional[str] = Field(None, max_length=15, description="Call-to-action text for video ads (max 15 chars, e.g. 'Learn More')")
    dry_run: bool = Field(False, description="If true, simulate without calling Google Ads API")


class LaunchAdResponse(BaseModel):
    id: str
    campaign_run_id: str
    ad_name: Optional[str]
    ad_type: str = "text"
    headline_1: Optional[str]
    headline_2: Optional[str]
    headline_3: Optional[str]
    description_1: Optional[str]
    description_2: Optional[str]
    final_url: str
    display_url_path_1: Optional[str]
    display_url_path_2: Optional[str]
    keywords: List[str]
    long_headline: Optional[str]
    business_name: Optional[str]
    media_url: Optional[str]
    media_file_name: Optional[str]
    media_content_type: Optional[str]
    media_size_bytes: Optional[int]
    status: str
    platform: str
    google_ad_resource_name: Optional[str]
    google_adgroup_resource_name: Optional[str]
    dry_run: bool
    created_at: str


class CampaignAdItem(BaseModel):
    id: str
    campaign_run_id: str
    ad_name: Optional[str]
    ad_type: str = "text"
    headline_1: Optional[str]
    headline_2: Optional[str]
    headline_3: Optional[str]
    description_1: Optional[str]
    description_2: Optional[str]
    final_url: str
    display_url_path_1: Optional[str]
    display_url_path_2: Optional[str]
    keywords: List[str]
    long_headline: Optional[str]
    business_name: Optional[str]
    media_url: Optional[str]
    media_file_name: Optional[str]
    media_content_type: Optional[str]
    media_size_bytes: Optional[int]
    status: str
    platform: str
    google_ad_resource_name: Optional[str]
    google_adgroup_resource_name: Optional[str]
    dry_run: bool
    created_at: str


class OptimizeRequest(BaseModel):
    """Request body for the campaign optimization endpoint."""
    campaign_run_id: str = Field(..., description="Supabase campaign run UUID")
    platform: str = Field(default="Google Ads", description="Platform to optimize")
    dry_run: bool = Field(default=False, description="Simulate without applying changes to the ad platform")
    use_mock_data: bool = Field(default=False, description="Inject simulated metrics instead of fetching from Google Ads API")
    user_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user-edited values to apply instead of computed values. E.g. {'new_budget_usd': 25.0}"
    )


class MetaOptimizeRequest(BaseModel):
    """Request body for the Meta Ads campaign optimization endpoint."""
    campaign_run_id: str = Field(..., description="Supabase campaign run UUID")
    dry_run: bool = Field(default=False, description="Simulate without applying changes")
    use_mock_data: bool = Field(default=False, description="Use simulated metrics for testing")
    user_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user-edited values, e.g. {'new_budget_usd': 25.0}"
    )


class OptimizationUndoRequest(BaseModel):
    """Request body for undoing an optimization."""
    optimization_id: str = Field(..., description="ID of the optimization record to undo")
    platform: str = Field(default="Google Ads", description="Platform the optimization was applied to")
