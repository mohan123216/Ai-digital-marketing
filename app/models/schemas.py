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
