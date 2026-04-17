# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from config import settings
from app.models.schemas import (
    AuthCredentials,
    AuthResponse,
    CampaignInput,
    GoogleAdsLaunchRequest,
    GoogleAdsLaunchStatusRequest,
    MetaAdsLaunchRequest,
    MetaAdsLaunchStatusRequest,
    ModelMetrics,
    UserProfile,
    CampaignHistoryItem,
    LaunchAdRequest,
    LaunchAdResponse,
    CampaignAdItem,
    OptimizeRequest,
    MetaOptimizeRequest,
    OptimizationUndoRequest,
    GenerateAdContentRequest,
    GeneratedAdContent,
)
from app.services.data_analyzer import DataAnalyzer
from app.services.predictor import CampaignPredictor
from app.services.recommendation_engine import RecommendationEngine
from app.services.auth_service import create_access_token, hash_password, verify_password
from app.services.supabase_client import get_supabase_admin_client
from app.services.user_store import create_user, get_user_by_email
from app.services.ad_generator import generate_ad_content
from app.dependencies.auth import get_current_user
from google_ads_mcp.launch import (
    get_recommendation_launch_status,
    get_campaign_resource_name_for_run,
    launch_selected_recommendation,
    launch_ad_to_campaign,
    launch_image_ad_to_campaign,
    launch_video_ad_to_campaign,
)
from meta_mcp.launch import (
    get_recommendation_launch_status as get_meta_recommendation_launch_status,
    launch_selected_recommendation as launch_selected_meta_recommendation,
)
from app.services.media_upload import upload_ad_media, validate_media

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
data_analyzer = None
predictor = None
recommendation_engine = None


def _save_campaign_history(
    user_id: str,
    campaign_input: CampaignInput,
    recommendations: Dict[str, Any],
) -> None:
    client = get_supabase_admin_client()
    top_recommendation = recommendations.get("top_recommendation", {})
    row = {
        "user_id": user_id,
        "product_name": campaign_input.product_name,
        "campaign_goal": campaign_input.campaign_goal.value,
        "budget_min": campaign_input.budget_range.min,
        "budget_max": campaign_input.budget_range.max,
        "top_platform": top_recommendation.get("platform"),
        "predicted_roi": top_recommendation.get("predicted_roi"),
        "input": campaign_input.model_dump(mode="json"),
        "output": recommendations,
        "launched_platforms": [],
    }
    client.table(settings.SUPABASE_CAMPAIGN_TABLE).insert(row).execute()


def _get_user_campaign_history(user_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_admin_client()
    response = (
        client.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select(
            "id,created_at,product_name,campaign_goal,budget_min,budget_max,top_platform,predicted_roi,output,launched_platforms,meta_campaign_id,meta_adset_id,meta_platform,meta_assets"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    rows = response.data or []
    # Ensure launched_platforms is always a list even for older rows without the column
    for row in rows:
        if row.get("launched_platforms") is None:
            row["launched_platforms"] = []
    return rows


def _persist_launched_platform(campaign_id: str, platform: str) -> None:
    db = get_supabase_admin_client()
    row_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("launched_platforms")
        .eq("id", campaign_id)
        .single()
        .execute()
    )
    current_platforms = row_resp.data.get("launched_platforms") or []
    if platform not in current_platforms:
        current_platforms.append(platform)
    db.table(settings.SUPABASE_CAMPAIGN_TABLE).update(
        {"launched_platforms": current_platforms}
    ).eq("id", campaign_id).execute()


def _persist_meta_launch_assets(
    campaign_id: str,
    platform: str,
    meta_campaign_id: str | None,
    meta_adset_id: str | None,
    launched_at: str | None = None,
) -> None:
    """Persist Meta (FB/IG) campaign/adset IDs onto campaign_runs for easy lookup."""
    if not meta_campaign_id:
        return

    db = get_supabase_admin_client()
    row_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("meta_assets")
        .eq("id", campaign_id)
        .single()
        .execute()
    )
    current_assets = (row_resp.data or {}).get("meta_assets") or {}
    if not isinstance(current_assets, dict):
        current_assets = {}

    current_assets[str(platform or "Meta Ads")] = {
        "meta_campaign_id": meta_campaign_id,
        "meta_adset_id": meta_adset_id,
        "launched_at": launched_at,
    }

    db.table(settings.SUPABASE_CAMPAIGN_TABLE).update(
        {
            "meta_campaign_id": meta_campaign_id,
            "meta_adset_id": meta_adset_id,
            "meta_platform": platform or "Meta Ads",
            "meta_assets": current_assets,
        }
    ).eq("id", campaign_id).execute()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    global data_analyzer, predictor, recommendation_engine

    logger.info("="*60)
    logger.info(f"🚀 STARTING {settings.PROJECT_NAME}")
    logger.info("="*60)

    try:
        # 1. Load and analyze data
        logger.info("\n📊 Step 1: Loading data...")
        data_analyzer = DataAnalyzer(settings.DATA_PATH)

        # 2. Train prediction models
        logger.info("\n🤖 Step 2: Training ML models...")
        predictor = CampaignPredictor()
        metrics = predictor.train(data_analyzer.df)

        # 3. Initialize recommendation engine
        logger.info("\n🎯 Step 3: Initializing recommendation engine...")
        recommendation_engine = RecommendationEngine(data_analyzer, predictor)

        # 4. Log success
        logger.info("\n" + "="*60)
        logger.info("✅ PLANNING AGENT READY!")
        logger.info("="*60)
        logger.info(f"📈 ROI Model R²: {metrics['roi']['r2']:.4f}")
        logger.info(f"📊 Conversion Model R²: {metrics['conversion']['r2']:.4f}")
        logger.info(f"📁 Data Records: {len(data_analyzer.df):,}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        logger.exception("Detailed error:")
        raise

    yield

    logger.info("🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered marketing campaign planning and optimization agent",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Normalize configured frontend origin to avoid mismatch on trailing slash.
frontend_origin = settings.FRONTEND_URL.rstrip("/")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    if not all([data_analyzer, predictor, recommendation_engine]):
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "message": "Services not fully initialized"}
        )
    
    return {
        "status": "healthy",
        "services": {
            "data_analyzer": "ready",
            "predictor": "ready",
            "recommendation_engine": "ready"
        },
        "stats": {
            "data_records": len(data_analyzer.df),
            "roi_model_r2": predictor.metrics['roi']['r2'],
            "conversion_model_r2": predictor.metrics['conversion']['r2']
        }
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post(
    f"{settings.API_V1_PREFIX}/auth/signup",
    response_model=AuthResponse,
    tags=["Auth"],
)
async def signup(payload: AuthCredentials):
    """Create a new user account and return an access token."""
    try:
        existing = get_user_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email is already registered")

        user = create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        token = create_access_token(user["id"], user["email"])
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Signup runtime error for {payload.email}: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception(f"Signup failed for {payload.email}: {e}")
        detail = f"Unable to create account: {str(e)}" if settings.DEBUG else "Unable to create account"
        raise HTTPException(status_code=500, detail=detail)

    return AuthResponse(
        access_token=token,
        user=UserProfile(
            id=user["id"],
            email=user.get("email"),
            created_at=user.get("created_at"),
        ),
    )


@app.post(
    f"{settings.API_V1_PREFIX}/auth/login",
    response_model=AuthResponse,
    tags=["Auth"],
)
async def login(payload: AuthCredentials):
    """Authenticate with email and password and return an access token."""
    try:
        user = get_user_by_email(payload.email)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to process login")

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"], user["email"])
    return AuthResponse(
        access_token=token,
        user=UserProfile(
            id=user["id"],
            email=user.get("email"),
            created_at=user.get("created_at"),
        ),
    )

@app.post(f"{settings.API_V1_PREFIX}/recommendations", 
          response_model=Dict[str, Any],
          tags=["Recommendations"])
async def generate_recommendations(
    campaign_input: CampaignInput,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Generate campaign recommendations based on user input
    
    This endpoint analyzes your campaign requirements and returns:
    - Top 5 campaign recommendations with predicted performance
    - Performance expectations and confidence scores
    - A/B testing recommendations
    - Actionable insights
    """
    logger.info(f"📨 Received request for: {campaign_input.product_name}")
    
    # Validate services
    if not all([data_analyzer, predictor, recommendation_engine]):
        raise HTTPException(
            status_code=503,
            detail="Services not fully initialized. Please try again in a moment."
        )
    
    # Validate budget
    if campaign_input.budget_range.min > campaign_input.budget_range.max:
        raise HTTPException(
            status_code=400,
            detail="Minimum budget cannot exceed maximum budget"
        )
    
    try:
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(campaign_input)
        
        logger.info(f"✅ Generated {len(recommendations['recommendations'])} recommendations")
        _save_campaign_history(current_user["id"], campaign_input, recommendations)
        return recommendations
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error generating recommendations: {e}")
        logger.exception("Detailed error:")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@app.get(
    f"{settings.API_V1_PREFIX}/me",
    response_model=UserProfile,
    tags=["Auth"],
)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get currently authenticated user profile."""
    return UserProfile(
        id=current_user["id"],
        email=current_user.get("email"),
        created_at=current_user.get("created_at"),
    )


@app.get(
    f"{settings.API_V1_PREFIX}/history",
    response_model=List[CampaignHistoryItem],
    tags=["Recommendations"],
)
async def get_history(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get the latest recommendation runs for the authenticated user."""
    try:
        rows = _get_user_campaign_history(current_user["id"])
        
        # Hydrate with Google Ads specific ad_type
        try:
            from google_ads_mcp.launch import _load_state
            state = _load_state()
            launched_dict = state.get("launched", {})
            for row in rows:
                row["google_ads_type"] = None
                if "Google Ads" in row.get("launched_platforms", []):
                    for k, v in launched_dict.items():
                        if v.get("campaign_id") == row["id"] and v.get("platform") == "Google Ads":
                            row["google_ads_type"] = v.get("ad_type")
                            break
        except Exception as e:
            logger.warning(f"Could not load Google Ads state for history: {e}")
            pass

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch history")

    return [CampaignHistoryItem(**row) for row in rows]


@app.post(f"{settings.API_V1_PREFIX}/google-ads/launch", tags=["Google Ads"])
async def launch_google_ads_campaign(
    payload: GoogleAdsLaunchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Launch selected recommendation in Google Ads and block relaunches."""
    try:
        result = launch_selected_recommendation(
            campaign_id=payload.campaign_id,
            recommendation=payload.recommendation,
            ad_type=payload.ad_type,
            dry_run=payload.dry_run,
            customer_id_override=payload.customer_id,
            budget_resource_override=payload.budget_resource_name,
            login_customer_id_override=payload.login_customer_id,
                    campaign_name_override=payload.campaign_name,
        )
        logger.info(
            "Google Ads launch request processed for user=%s campaign_id=%s status=%s",
            current_user.get("id"),
            payload.campaign_id,
            result.get("status"),
        )

        # Handle auth errors gracefully
        if result.get("status") == "auth_error":
            raise HTTPException(
                status_code=401,
                detail=result.get("message", "Google Ads authentication failed")
            )

        # If successfully launched (not a duplicate), persist the platform into the DB row
        if result.get("status") == "launched" or result.get("status") == "launched_dry_run":
            platform = payload.recommendation.get("platform", "Google Ads")
            try:
                _persist_launched_platform(payload.campaign_id, platform)
                logger.info("Persisted launched platform '%s' for campaign_id=%s", platform, payload.campaign_id)
            except Exception as db_err:
                logger.warning("Could not persist launched platform to DB: %s", db_err)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ModuleNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Ads SDK is not installed in this environment: {e}",
        )
    except Exception as e:
        logger.exception(f"Google Ads launch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Launch failed: {str(e)}")


@app.post(f"{settings.API_V1_PREFIX}/google-ads/launch-status", tags=["Google Ads"])
async def get_google_ads_launch_status(
    payload: GoogleAdsLaunchStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get launch status for a recommendation (to disable launch button in UI)."""
    try:
        status = get_recommendation_launch_status(
            campaign_id=payload.campaign_id,
            recommendation=payload.recommendation,
        )
        logger.info(
            "Google Ads launch status checked for user=%s campaign_id=%s launchable=%s",
            current_user.get("id"),
            payload.campaign_id,
            status.get("launchable"),
        )
        return status
    except Exception as e:
        logger.exception(f"Google Ads launch status lookup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status lookup failed: {str(e)}")


@app.post(f"{settings.API_V1_PREFIX}/meta-ads/launch", tags=["Meta Ads"])
async def launch_meta_ads_campaign(
    payload: MetaAdsLaunchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Launch selected recommendation in Meta Ads (Instagram/Facebook)."""
    try:
        result = launch_selected_meta_recommendation(
            campaign_id=payload.campaign_id,
            recommendation=payload.recommendation,
            dry_run=payload.dry_run,
            ad_account_id_override=payload.ad_account_id,
        )
        logger.info(
            "Meta launch request processed for user=%s campaign_id=%s status=%s platform=%s",
            current_user.get("id"),
            payload.campaign_id,
            result.get("status"),
            payload.recommendation.get("platform"),
        )

        if result.get("status") == "launched" or result.get("status") == "launched_dry_run":
            platform = payload.recommendation.get("platform", "Meta Ads")
            try:
                _persist_launched_platform(payload.campaign_id, platform)
                logger.info("Persisted launched platform '%s' for campaign_id=%s", platform, payload.campaign_id)
            except Exception as db_err:
                logger.warning("Could not persist launched platform to DB: %s", db_err)

            try:
                _persist_meta_launch_assets(
                    campaign_id=payload.campaign_id,
                    platform=platform,
                    meta_campaign_id=result.get("meta_campaign_id"),
                    meta_adset_id=result.get("meta_adset_id"),
                )
            except Exception as db_err:
                logger.warning("Could not persist Meta IDs to campaign_runs: %s", db_err)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ModuleNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Meta SDK is not installed in this environment: {e}",
        )
    except Exception as e:
        logger.exception(f"Meta launch failed: {e}")
        msg = str(e).lower()
        if (
            "error validating access token" in msg
            or '"code": 190' in msg
            or '"error_subcode": 463' in msg
            or "session has expired" in msg
            or "meta access token is expired" in msg
        ):
            raise HTTPException(
                status_code=401,
                detail="Meta access token expired. Reconnect Meta (or update META_ACCESS_TOKEN) and try again.",
            )
        raise HTTPException(status_code=500, detail=f"Launch failed: {str(e)}")


@app.post(f"{settings.API_V1_PREFIX}/meta-ads/launch-status", tags=["Meta Ads"])
async def get_meta_ads_launch_status(
    payload: MetaAdsLaunchStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get launchability status for a Meta recommendation."""
    try:
        status = get_meta_recommendation_launch_status(
            campaign_id=payload.campaign_id,
            recommendation=payload.recommendation,
        )
        logger.info(
            "Meta launch status checked for user=%s campaign_id=%s launchable=%s",
            current_user.get("id"),
            payload.campaign_id,
            status.get("launchable"),
        )
        return status
    except Exception as e:
        logger.exception(f"Meta launch status lookup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status lookup failed: {str(e)}")


# ============================================================================
# PAUSE/RESUME CAMPAIGN ENDPOINTS
# ============================================================================

@app.post(f"{settings.API_V1_PREFIX}/google-ads/{{campaign_resource_name}}/pause", tags=["Google Ads"])
async def pause_google_ads_campaign(
    campaign_resource_name: str,
    dry_run: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Pause a Google Ads campaign."""
    try:
        from google_ads_mcp.pause import pause_campaign as pause_google_campaign
        
        result = pause_google_campaign(
            resource_name=campaign_resource_name,
            dry_run=dry_run,
        )
        logger.info(
            "Google Ads pause request processed for user=%s campaign=%s status=%s",
            current_user.get("id"),
            campaign_resource_name,
            result.get("status"),
        )
        return result
    except Exception as e:
        logger.exception(f"Google Ads pause failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pause failed: {str(e)}")


@app.post(f"{settings.API_V1_PREFIX}/google-ads/{{campaign_resource_name}}/resume", tags=["Google Ads"])
async def resume_google_ads_campaign(
    campaign_resource_name: str,
    dry_run: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Resume a paused Google Ads campaign."""
    try:
        from google_ads_mcp.pause import resume_campaign as resume_google_campaign
        
        result = resume_google_campaign(
            resource_name=campaign_resource_name,
            dry_run=dry_run,
        )
        logger.info(
            "Google Ads resume request processed for user=%s campaign=%s status=%s",
            current_user.get("id"),
            campaign_resource_name,
            result.get("status"),
        )
        return result
    except Exception as e:
        logger.exception(f"Google Ads resume failed: {e}")
        raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)}")


@app.get(f"{settings.API_V1_PREFIX}/google-ads/{{campaign_resource_name}}/status", tags=["Google Ads"])
async def get_google_ads_campaign_status(
    campaign_resource_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get status of a Google Ads campaign."""
    try:
        from google_ads_mcp.pause import get_campaign_status as get_google_status
        
        result = get_google_status(resource_name=campaign_resource_name)
        logger.info(
            "Google Ads status check for user=%s campaign=%s",
            current_user.get("id"),
            campaign_resource_name,
        )
        return result
    except Exception as e:
        logger.exception(f"Google Ads status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.post(f"{settings.API_V1_PREFIX}/meta-ads/{{meta_campaign_id}}/pause", tags=["Meta Ads"])
async def pause_meta_ads_campaign(
    meta_campaign_id: str,
    dry_run: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Pause a Meta (Facebook/Instagram) campaign."""
    try:
        from meta_mcp.pause import pause_campaign as pause_meta_campaign
        
        result = pause_meta_campaign(
            meta_campaign_id=meta_campaign_id,
            dry_run=dry_run,
        )
        logger.info(
            "Meta pause request processed for user=%s campaign=%s status=%s",
            current_user.get("id"),
            meta_campaign_id,
            result.get("status"),
        )
        return result
    except Exception as e:
        logger.exception(f"Meta pause failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pause failed: {str(e)}")


@app.post(f"{settings.API_V1_PREFIX}/meta-ads/{{meta_campaign_id}}/resume", tags=["Meta Ads"])
async def resume_meta_ads_campaign(
    meta_campaign_id: str,
    dry_run: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Resume a paused Meta campaign."""
    try:
        from meta_mcp.pause import resume_campaign as resume_meta_campaign
        
        result = resume_meta_campaign(
            meta_campaign_id=meta_campaign_id,
            dry_run=dry_run,
        )
        logger.info(
            "Meta resume request processed for user=%s campaign=%s status=%s",
            current_user.get("id"),
            meta_campaign_id,
            result.get("status"),
        )
        return result
    except Exception as e:
        logger.exception(f"Meta resume failed: {e}")
        raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)}")


@app.get(f"{settings.API_V1_PREFIX}/meta-ads/{{meta_campaign_id}}/status", tags=["Meta Ads"])
async def get_meta_ads_campaign_status(
    meta_campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get status of a Meta campaign."""
    try:
        from meta_mcp.pause import get_campaign_status as get_meta_status
        
        result = get_meta_status(meta_campaign_id=meta_campaign_id)
        logger.info(
            "Meta status check for user=%s campaign=%s",
            current_user.get("id"),
            meta_campaign_id,
        )
        return result
    except Exception as e:
        logger.exception(f"Meta status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


# ============================================================================
# AD CONTENT GENERATION ENDPOINTS
# ============================================================================

@app.post(
    f"{settings.API_V1_PREFIX}/ads/generate-content",
    response_model=GeneratedAdContent,
    tags=["Ads"],
)
async def generate_ad_content_endpoint(
    payload: GenerateAdContentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Generate ad headlines, keywords, and descriptions using AI.
    
    Provide product name, campaign title, target audience, and marketing text.
    The AI will generate high-performing headlines, keywords, and product descriptions.
    """
    try:
        result = generate_ad_content(
            product_name=payload.product_name,
            title=payload.campaign_title,
            target_audience=payload.target_audience,
            ad_text=payload.ad_text,
            campaign_goal=payload.campaign_goal,
        )
        logger.info(
            "Generated ad content for user=%s product=%s",
            current_user.get("id"),
            payload.product_name,
        )
        return GeneratedAdContent(**result)
    except Exception as e:
        logger.exception(f"Ad content generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate ad content: {str(e)}")


# ============================================================================
# ADS ENDPOINTS (launch ads inside campaigns)
# ============================================================================

CAMPAIGN_ADS_TABLE = "campaign_ads"


def _save_campaign_ad(
    campaign_run_id: str,
    user_id: str,
    payload: LaunchAdRequest,
    launch_result: Dict[str, Any],
    media_url: str | None = None,
    media_file_name: str | None = None,
    media_content_type: str | None = None,
    media_size_bytes: int | None = None,
) -> Dict[str, Any]:
    """Persist a launched ad record in Supabase and return the full row."""
    db = get_supabase_admin_client()
    status = launch_result.get("status", "launched")
    row = {
        "campaign_run_id": campaign_run_id,
        "user_id": user_id,
        "ad_name": payload.ad_name or launch_result.get("ad_name"),
        "ad_type": getattr(payload, "ad_type", "text") or "text",
        "headline_1": payload.headline_1,
        "headline_2": payload.headline_2,
        "headline_3": payload.headline_3,
        "description_1": payload.description_1,
        "description_2": payload.description_2,
        "final_url": payload.final_url,
        "display_url_path_1": payload.display_url_path_1,
        "display_url_path_2": payload.display_url_path_2,
        "keywords": payload.keywords or [],
        "long_headline": getattr(payload, "long_headline", None),
        "business_name": getattr(payload, "business_name", None),
        "status": status,
        "platform": "Google Ads",
        "google_ad_resource_name": launch_result.get("ad_resource_name"),
        "google_adgroup_resource_name": launch_result.get("adgroup_resource_name"),
        "dry_run": payload.dry_run,
        "media_url": media_url,
        "media_file_name": media_file_name,
        "media_content_type": media_content_type,
        "media_size_bytes": media_size_bytes,
    }
    response = db.table(CAMPAIGN_ADS_TABLE).insert(row).execute()
    return response.data[0]


def _list_campaign_ads(campaign_run_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Fetch all ads belonging to a specific campaign run for the given user."""
    db = get_supabase_admin_client()
    response = (
        db.table(CAMPAIGN_ADS_TABLE)
        .select("*")
        .eq("campaign_run_id", campaign_run_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


@app.post(
    f"{settings.API_V1_PREFIX}/google-ads/campaigns/{{campaign_run_id}}/ads",
    response_model=LaunchAdResponse,
    tags=["Ads"],
)
async def launch_ad(
    campaign_run_id: str,
    payload: LaunchAdRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Launch a new Responsive Search Ad inside an existing Google Ads campaign.

    The campaign_run_id is the UUID from campaign_runs in Supabase.
    Users may call this endpoint as many times as they want to create multiple ads.
    
    If generate_with_llm is true, provide product_name and target_audience.
    The AI will auto-generate headlines, keywords, and descriptions.
    """
    user_id = current_user["id"]

    # Verify the campaign_run_id belongs to this user
    db = get_supabase_admin_client()
    run_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("id,user_id,launched_platforms")
        .eq("id", campaign_run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_resp.data:
        raise HTTPException(status_code=404, detail="Campaign run not found or access denied.")

    try:
        # Generate ad content using LLM if requested
        if payload.generate_with_llm:
            if not payload.product_name:
                raise ValueError("product_name is required when generate_with_llm is true")
            
            generated = generate_ad_content(
                product_name=payload.product_name,
                title=payload.campaign_title,
                target_audience=payload.target_audience,
                ad_text=payload.ad_text,
                campaign_goal=payload.campaign_goal,
            )
            logger.info(
                "Generated ad content using LLM for user=%s campaign_run_id=%s",
                user_id, campaign_run_id,
            )
            
            # Populate payload with generated content
            # Headlines
            headlines = generated.get("headlines", [])
            if len(headlines) > 0:
                payload.headline_1 = headlines[0][:30]
            if len(headlines) > 1:
                payload.headline_2 = headlines[1][:30]
            if len(headlines) > 2:
                payload.headline_3 = headlines[2][:30]
            
            # Descriptions
            descriptions = generated.get("descriptions", [])
            if len(descriptions) > 0:
                payload.description_1 = descriptions[0][:90]
            if len(descriptions) > 1:
                payload.description_2 = descriptions[1][:90]
            
            # Keywords (merge with any manually provided keywords)
            keywords = generated.get("keywords", [])
            if payload.keywords:
                keywords = list(set(keywords + payload.keywords))
            payload.keywords = keywords

        result = launch_ad_to_campaign(
            campaign_run_id=campaign_run_id,
            ad_payload=payload.model_dump(),
            dry_run=payload.dry_run,
        )
        logger.info(
            "Ad launch for user=%s campaign_run_id=%s status=%s dry_run=%s",
            user_id, campaign_run_id, result.get("status"), payload.dry_run,
        )
        row = _save_campaign_ad(campaign_run_id, user_id, payload, result)
        return LaunchAdResponse(**row)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ModuleNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Google Ads SDK not installed: {e}")
    except Exception as e:
        logger.exception(f"Ad launch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ad launch failed: {str(e)}")


@app.get(
    f"{settings.API_V1_PREFIX}/google-ads/campaigns/{{campaign_run_id}}/ads",
    response_model=List[CampaignAdItem],
    tags=["Ads"],
)
async def list_ads(
    campaign_run_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all ads launched for a particular campaign run."""
    user_id = current_user["id"]
    try:
        rows = _list_campaign_ads(campaign_run_id, user_id)
        return [CampaignAdItem(**r) for r in rows]
    except Exception as e:
        logger.exception(f"List ads failed: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch ads: {str(e)}")


@app.get(
    f"{settings.API_V1_PREFIX}/google-ads/campaigns/{{campaign_run_id}}/metrics",
    tags=["Google Ads", "Metrics"],
)
async def get_campaign_metrics(
    campaign_run_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Fetch real-time metrics from Google Ads for the launched campaign."""
    user_id = current_user["id"]
    db = get_supabase_admin_client()
    run_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("id,user_id")
        .eq("id", campaign_run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_resp.data:
        raise HTTPException(status_code=404, detail="Campaign run not found or access denied.")

    campaign_resource = get_campaign_resource_name_for_run(campaign_run_id)
    if not campaign_resource:
        raise HTTPException(status_code=404, detail="Google Ads campaign not found for this run.")

    if campaign_resource.startswith("dryrun/"):
        return {"campaign_metrics": [], "ad_metrics": []}

    try:
        # Extract numeric campaign ID from resource name (e.g., customers/123/campaigns/456)
        parts = campaign_resource.split("/")
        if len(parts) >= 4 and parts[-2] == "campaigns":
            numeric_id = parts[-1]
            from google_ads_mcp.get_metrics import get_metrics as get_gads_metrics
            metrics = get_gads_metrics([numeric_id])
            return metrics
        else:
            return {"campaign_metrics": [], "ad_metrics": []}
    except Exception as e:
        logger.exception(f"Failed to fetch Google Ads metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics.")


@app.get(
    f"{settings.API_V1_PREFIX}/meta-ads/campaigns/{{campaign_run_id}}/metrics",
    tags=["Meta Ads", "Metrics"],
)
async def get_meta_campaign_metrics(
    campaign_run_id: str,
    platform: str | None = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Fetch real-time metrics from Meta Ads (Facebook/Instagram) for the launched campaign."""
    user_id = current_user["id"]
    db = get_supabase_admin_client()
    run_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("id,user_id,meta_campaign_id,meta_adset_id,meta_assets")
        .eq("id", campaign_run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_resp.data:
        raise HTTPException(status_code=404, detail="Campaign run not found or access denied.")

    run = run_resp.data or {}
    meta_campaign_id = run.get("meta_campaign_id")
    meta_adset_id = run.get("meta_adset_id")

    meta_assets = run.get("meta_assets") or {}
    if platform and isinstance(meta_assets, dict):
        entry = meta_assets.get(platform) or meta_assets.get("Meta Ads")
        if isinstance(entry, dict):
            meta_campaign_id = entry.get("meta_campaign_id") or meta_campaign_id
            meta_adset_id = entry.get("meta_adset_id") or meta_adset_id

    # Fallback: look up IDs from MCP state (JSON/Supabase) if not present on campaign_runs
    if not meta_campaign_id:
        try:
            from meta_mcp.launch import _load_state as _load_meta_state

            meta_state = _load_meta_state()
            candidates = []
            for entry in (meta_state.get("launched") or {}).values():
                if entry.get("campaign_id") != campaign_run_id:
                    continue
                if platform and entry.get("platform") != platform:
                    continue
                candidates.append(entry)

            if candidates:
                picked = candidates[0]
                meta_campaign_id = picked.get("meta_campaign_id") or picked.get("resource_name")
                meta_adset_id = picked.get("meta_adset_id")
        except Exception:
            pass

    if not meta_campaign_id:
        raise HTTPException(status_code=404, detail="Meta Ads campaign not found for this run.")

    if str(meta_campaign_id).startswith("dryrun"):
        return {"campaign_metrics": [], "ad_metrics": []}

    try:
        from meta_mcp.get_metrics import get_metrics as get_meta_metrics

        return get_meta_metrics([str(meta_campaign_id)])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ModuleNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Meta SDK is not installed in this environment: {e}")
    except Exception as e:
        logger.exception(f"Failed to fetch Meta Ads metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics.")


@app.post(
    f"{settings.API_V1_PREFIX}/google-ads/campaigns/{{campaign_run_id}}/optimize",
    tags=["Google Ads", "Optimize"],
)
async def optimize_google_ads_campaign(
    campaign_run_id: str,
    body: OptimizeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Run the Optimization Agent for a launched Google Ads campaign.
    Compares actual vs predicted metrics, then applies budget/status changes.
    Pass dry_run=True for analysis-only. Pass user_overrides={new_budget_usd: X} to apply a custom budget.
    """
    user_id = current_user["id"]
    db = get_supabase_admin_client()

    # 1. Verify campaign ownership
    run_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("id,user_id,output,launched_platforms")
        .eq("id", campaign_run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_resp.data:
        raise HTTPException(status_code=404, detail="Campaign run not found or access denied.")

    run = run_resp.data
    output = run.get("output") or {}
    recommendations = output.get("recommendations", [])

    # 2. Find predicted values for Google Ads platform
    predicted_roi = 1.0
    predicted_cr_pct = 2.0
    for rec in recommendations:
        if rec.get("platform") == "Google Ads":
            predicted_roi    = float(rec.get("predicted_roi", 1.0))
            predicted_cr_pct = float(rec.get("predicted_conversion_rate", 2.0))
            break

    # 3. Get the Google Ads resource name
    campaign_resource = get_campaign_resource_name_for_run(campaign_run_id)
    if not campaign_resource:
        raise HTTPException(
            status_code=404,
            detail="No Google Ads campaign found for this run. Launch it first.",
        )
    if campaign_resource.startswith("dryrun/") and not body.use_mock_data:
        return {
            "status": "dry_run_campaign",
            "message": "This campaign was launched in dry-run mode. No real metrics exist. Use 'Mock Data' to simulate optimization.",
            "analysis": {}, "actions": [],
        }

    # 4. Fetch actual metrics from Google Ads OR generate mock data
    actual_metrics: list = []
    mock_seed = None
    mock_scenario = None

    if body.use_mock_data:
        import random, time
        mock_seed = time.time_ns()
        random.seed(mock_seed)
        budget_val = str(recommendations[0].get("budget", 50)) if recommendations else "50"
        budget = float(budget_val.replace(",", "").replace("$", ""))
        cost_usd = budget * 7 * random.uniform(0.1, 1.0)
        scenario = random.choices(
            ["good", "bad_roi", "bad_ctr", "bad_cr", "average"],
            weights=[0.25, 0.25, 0.15, 0.15, 0.20]
        )[0]
        mock_scenario = scenario
        if scenario == "good":
            roi_mul = random.uniform(1.1, 1.5); cr_mul = random.uniform(1.1, 1.3); ctr_pct = random.uniform(5.0, 8.0)
        elif scenario == "bad_roi":
            roi_mul = random.uniform(0.3, 0.6); cr_mul = random.uniform(0.7, 1.0); ctr_pct = random.uniform(3.0, 6.0)
        elif scenario == "bad_ctr":
            roi_mul = random.uniform(0.8, 1.2); cr_mul = random.uniform(0.8, 1.2); ctr_pct = random.uniform(0.5, 1.8)
        elif scenario == "bad_cr":
            roi_mul = random.uniform(0.5, 0.9); cr_mul = random.uniform(0.2, 0.4); ctr_pct = random.uniform(5.0, 9.0)
        else:
            roi_mul = random.uniform(0.9, 1.1); cr_mul = random.uniform(0.9, 1.1); ctr_pct = random.uniform(3.0, 5.0)
        mock_roi = predicted_roi * roi_mul
        mock_cr  = (predicted_cr_pct / 100.0) * cr_mul
        conversions = max(1, int((cost_usd / 10.0) * mock_roi))
        clicks = max(1, int(conversions / mock_cr)) if mock_cr > 0 else 100
        impressions = max(1, int(clicks / (ctr_pct / 100.0)))
        actual_metrics = [{"impressions": impressions, "clicks": clicks, "conversions": conversions, "cost_usd": cost_usd}]
    else:
        numeric_id = campaign_resource.split("/")[-1]
        try:
            from google_ads_mcp.get_metrics import get_metrics as _get_gads_metrics
            data = _get_gads_metrics([numeric_id])
            actual_metrics = data.get("campaign_metrics", [])
        except Exception as exc:
            logger.warning(f"Could not fetch metrics for optimisation: {exc}")

    # 5. Run optimisation agent
    try:
        from google_ads_mcp.optimize import optimize_campaign as _optimize
        result = _optimize(
            campaign_resource_name=campaign_resource,
            actual_campaign_metrics=actual_metrics,
            predicted_roi=predicted_roi,
            predicted_conversion_rate_pct=predicted_cr_pct,
            dry_run=body.dry_run,
            user_overrides=body.user_overrides,
        )
        if mock_seed is not None:
            result["mock_seed"] = mock_seed
            result["mock_scenario"] = mock_scenario
    except Exception as exc:
        logger.exception(f"Optimization agent error: {exc}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {exc}")

    # 6. Persist optimization log to Supabase (include old_values for undo)
    opt_record_id = None
    if not body.dry_run:
        try:
            # Collect old values for undo from api_result
            old_values: Dict[str, Any] = {}
            for action in result.get("actions", []):
                if action.get("api_result"):
                    ar = action["api_result"]
                    if "old_daily_budget_usd" in ar:
                        old_values["old_daily_budget_usd"] = ar["old_daily_budget_usd"]
                        old_values["budget_resource"] = ar.get("budget_resource")
                        old_values["campaign_resource"] = campaign_resource
                    if "new_status" in ar:
                        old_values["old_status"] = "ENABLED"  # assume was enabled before pausing
                        old_values["campaign_resource"] = campaign_resource

            ins_resp = db.table("campaign_optimizations").insert({
                "campaign_run_id": campaign_run_id,
                "user_id": user_id,
                "platform": "Google Ads",
                "dry_run": body.dry_run,
                "analysis": result.get("analysis"),
                "actions": result.get("actions"),
                "status": result.get("status"),
                "old_values": old_values,
            }).execute()
            if ins_resp.data:
                opt_record_id = ins_resp.data[0].get("id")
        except Exception as exc:
            logger.warning(f"Failed to persist optimization log: {exc}")

    result["optimization_id"] = opt_record_id
    return result


@app.get(
    f"{settings.API_V1_PREFIX}/google-ads/campaigns/{{campaign_run_id}}/optimizations",
    tags=["Optimization"],
)
async def get_google_ads_optimization_history(
    campaign_run_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get optimization history for a Google Ads campaign run."""
    db = get_supabase_admin_client()
    try:
        resp = (
            db.table("campaign_optimizations")
            .select("*")
            .eq("campaign_run_id", campaign_run_id)
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .execute()
        )
        return {"history": resp.data or []}
    except Exception as exc:
        logger.error(f"Failed to fetch optimizations: {exc}")
        return {"history": []}


@app.post(
    f"{settings.API_V1_PREFIX}/google-ads/campaigns/{{campaign_run_id}}/optimize/undo",
    tags=["Optimization"],
)
async def undo_google_ads_optimization(
    campaign_run_id: str,
    body: OptimizationUndoRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Undo the last applied Google Ads optimization by reverting budget/status to previous values."""
    user_id = current_user["id"]
    db = get_supabase_admin_client()

    # Fetch the optimization record
    opt_resp = (
        db.table("campaign_optimizations")
        .select("*")
        .eq("id", body.optimization_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not opt_resp.data:
        raise HTTPException(status_code=404, detail="Optimization record not found.")

    opt = opt_resp.data
    if opt.get("dry_run"):
        raise HTTPException(status_code=400, detail="Cannot undo a dry-run optimization.")
    if opt.get("undone"):
        raise HTTPException(status_code=400, detail="This optimization has already been undone.")

    old_values = opt.get("old_values") or {}
    if not old_values:
        raise HTTPException(status_code=400, detail="No old values stored for this optimization. Cannot undo.")

    undo_results = []

    # Restore previous budget if stored
    if "old_daily_budget_usd" in old_values and old_values.get("budget_resource"):
        try:
            from google_ads_mcp.optimize import _get_client, _get_customer_id
            client = _get_client()
            old_micros = int(round(old_values["old_daily_budget_usd"] * 1_000_000))
            old_micros = round(old_micros / 10000) * 10000

            budget_service = client.get_service("CampaignBudgetService")
            budget_op = client.get_type("CampaignBudgetOperation")
            budget = budget_op.update
            budget.resource_name = old_values["budget_resource"]
            budget.amount_micros = old_micros

            from google.api_core import protobuf_helpers
            client.copy_from(budget_op.update_mask, protobuf_helpers.field_mask(None, budget._pb))
            budget_service.mutate_campaign_budgets(customer_id=_get_customer_id(), operations=[budget_op])
            undo_results.append(f"Budget restored to ${old_values['old_daily_budget_usd']}/day")
        except Exception as exc:
            logger.error(f"Budget undo failed: {exc}")
            raise HTTPException(status_code=500, detail=f"Budget undo failed: {exc}")

    # Restore previous campaign status if needed
    if "old_status" in old_values and old_values.get("campaign_resource"):
        try:
            from google_ads_mcp.optimize import _get_client, _get_customer_id
            client = _get_client()
            campaign_service = client.get_service("CampaignService")
            campaign_op = client.get_type("CampaignOperation")
            campaign = campaign_op.update
            campaign.resource_name = old_values["campaign_resource"]
            status_enum = client.enums.CampaignStatusEnum.CampaignStatus.Value(old_values["old_status"])
            campaign.status = status_enum

            from google.api_core import protobuf_helpers
            client.copy_from(campaign_op.update_mask, protobuf_helpers.field_mask(None, campaign._pb))
            campaign_service.mutate_campaigns(customer_id=_get_customer_id(), operations=[campaign_op])
            undo_results.append(f"Campaign status restored to {old_values['old_status']}")
        except Exception as exc:
            logger.error(f"Status undo failed: {exc}")
            raise HTTPException(status_code=500, detail=f"Status undo failed: {exc}")

    # Mark record as undone
    try:
        db.table("campaign_optimizations").update({"undone": True}).eq("id", body.optimization_id).execute()
    except Exception as exc:
        logger.warning(f"Failed to mark optimization as undone: {exc}")

    return {"status": "undone", "reverted": undo_results, "optimization_id": body.optimization_id}


# ── Meta Ads Optimization Endpoints ──────────────────────────────────────────

@app.post(
    f"{settings.API_V1_PREFIX}/meta-ads/campaigns/{{campaign_run_id}}/optimize",
    tags=["Meta Ads", "Optimize"],
)
async def optimize_meta_ads_campaign(
    campaign_run_id: str,
    body: MetaOptimizeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Run the Optimization Agent for a launched Meta Ads campaign.
    Compares actual vs predicted metrics, applies budget/status changes.
    Pass dry_run=True for analysis only. Pass user_overrides={new_budget_usd: X} for custom budget.
    """
    user_id = current_user["id"]
    db = get_supabase_admin_client()

    # 1. Verify campaign ownership
    run_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("id,user_id,output,launched_platforms,meta_campaign_id,meta_adset_id,meta_assets")
        .eq("id", campaign_run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_resp.data:
        raise HTTPException(status_code=404, detail="Campaign run not found or access denied.")

    run = run_resp.data
    output = run.get("output") or {}
    recommendations = output.get("recommendations", [])

    # 2. Find predicted values for Meta (Instagram/Facebook)
    predicted_roi = 1.0
    predicted_cr_pct = 2.0
    for rec in recommendations:
        if rec.get("platform") in ("Instagram", "Facebook", "Meta Ads"):
            predicted_roi    = float(rec.get("predicted_roi", 1.0))
            predicted_cr_pct = float(rec.get("predicted_conversion_rate", 2.0))
            break

    # 3. Resolve Meta campaign/adset IDs (prefer campaign_runs columns, fallback to MCP state)
    meta_campaign_id = run.get("meta_campaign_id")
    meta_adset_id = run.get("meta_adset_id")

    if not meta_campaign_id or not meta_adset_id:
        from meta_mcp.launch import _load_state
        meta_state = _load_state()

        for entry in meta_state.get("launched", {}).values():
            if entry.get("campaign_id") == campaign_run_id:
                meta_campaign_id = meta_campaign_id or entry.get("meta_campaign_id") or entry.get("resource_name")
                meta_adset_id = meta_adset_id or entry.get("meta_adset_id")
                if meta_campaign_id and meta_adset_id:
                    break

    if not meta_campaign_id and not body.use_mock_data:
        raise HTTPException(
            status_code=404,
            detail="No Meta Ads campaign found for this run. Launch it first."
        )

    # If the user is applying changes, we must have real IDs (mock-only runs can't apply to Meta).
    if not body.dry_run:
        if not meta_campaign_id or not meta_adset_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot apply Meta optimizations without a real Meta campaign/adset ID. Launch the campaign first.",
            )
        if str(meta_campaign_id).startswith("dryrun_") or str(meta_adset_id).startswith("dryrun_"):
            raise HTTPException(
                status_code=400,
                detail="This Meta campaign was launched in dry-run mode. Launch it for real before applying optimizations.",
            )

    # 4. Fetch actual metrics or generate mock
    actual_metrics: list = []
    current_daily_budget_cents = 0
    mock_seed = None
    mock_scenario = None

    if body.use_mock_data or not meta_campaign_id or meta_campaign_id.startswith("dryrun_"):
        import random, time
        mock_seed = time.time_ns()
        random.seed(mock_seed)

        budget_val = str(recommendations[0].get("budget", 50)) if recommendations else "50"
        budget = float(budget_val.replace(",", "").replace("$", ""))
        cost_usd = budget * 7 * random.uniform(0.1, 1.0)

        scenario = random.choices(
            ["good", "bad_roi", "bad_ctr", "bad_cr", "average"],
            weights=[0.25, 0.25, 0.15, 0.15, 0.20]
        )[0]
        mock_scenario = scenario
        if scenario == "good":
            roi_mul = random.uniform(1.1, 1.5); cr_mul = random.uniform(1.1, 1.3); ctr_pct = random.uniform(5.0, 8.0)
        elif scenario == "bad_roi":
            roi_mul = random.uniform(0.3, 0.6); cr_mul = random.uniform(0.7, 1.0); ctr_pct = random.uniform(3.0, 6.0)
        elif scenario == "bad_ctr":
            roi_mul = random.uniform(0.8, 1.2); cr_mul = random.uniform(0.8, 1.2); ctr_pct = random.uniform(0.5, 1.8)
        elif scenario == "bad_cr":
            roi_mul = random.uniform(0.5, 0.9); cr_mul = random.uniform(0.2, 0.4); ctr_pct = random.uniform(5.0, 9.0)
        else:
            roi_mul = random.uniform(0.9, 1.1); cr_mul = random.uniform(0.9, 1.1); ctr_pct = random.uniform(3.0, 5.0)

        mock_roi = predicted_roi * roi_mul
        mock_cr  = (predicted_cr_pct / 100.0) * cr_mul
        conversions = max(1, int((cost_usd / 10.0) * mock_roi))
        clicks = max(1, int(conversions / mock_cr)) if mock_cr > 0 else 100
        impressions = max(1, int(clicks / (ctr_pct / 100.0)))
        actual_metrics = [{"impressions": impressions, "clicks": clicks, "conversions": conversions, "cost_usd": cost_usd}]
        # Set a simulated daily budget for mock (based on plan budget)
        current_daily_budget_cents = int(budget * 100 / 30)  # daily from 30-day plan
    else:
        try:
            from meta_mcp.optimize import get_meta_campaign_insights, get_meta_adset_current_budget_cents
            actual_metrics = get_meta_campaign_insights(meta_campaign_id)
            current_daily_budget_cents = get_meta_adset_current_budget_cents(meta_adset_id)
        except Exception as exc:
            logger.warning(f"Could not fetch Meta metrics: {exc}")

    # 5. Run Meta optimization agent
    try:
        from meta_mcp.optimize import optimize_meta_campaign as _meta_optimize
        result = _meta_optimize(
            meta_campaign_id=meta_campaign_id or f"mock_{campaign_run_id}",
            meta_adset_id=meta_adset_id or f"mock_adset_{campaign_run_id}",
            actual_campaign_metrics=actual_metrics,
            predicted_roi=predicted_roi,
            predicted_conversion_rate_pct=predicted_cr_pct,
            current_daily_budget_cents=current_daily_budget_cents,
            dry_run=body.dry_run,
            user_overrides=body.user_overrides,
        )
        if mock_seed is not None:
            result["mock_seed"] = mock_seed
            result["mock_scenario"] = mock_scenario
    except Exception as exc:
        logger.exception(f"Meta optimization agent error: {exc}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {exc}")

    # If we tried to apply programmatic changes and any API call failed, surface an explicit status
    if not body.dry_run:
        actions = result.get("actions") or []
        if any(a.get("api_error") for a in actions):
            result["status"] = "apply_failed"
            result["message"] = "Some programmatic changes failed to apply. See action-level API errors."

    # 6. Persist log
    opt_record_id = None
    if not body.dry_run:
        try:
            old_values: Dict[str, Any] = {}
            for action in result.get("actions", []):
                if action.get("api_result"):
                    ar = action["api_result"]
                    if "old_daily_budget_usd" in ar:
                        old_values["old_daily_budget_usd"] = ar["old_daily_budget_usd"]
                        old_values["meta_adset_id"] = meta_adset_id
                        old_values["meta_campaign_id"] = meta_campaign_id
                    if "new_status" in ar:
                        old_values["old_status"] = "ACTIVE"
                        old_values["meta_campaign_id"] = meta_campaign_id

            ins_resp = db.table("campaign_optimizations").insert({
                "campaign_run_id": campaign_run_id,
                "user_id": user_id,
                "platform": "Meta Ads",
                "dry_run": body.dry_run,
                "analysis": result.get("analysis"),
                "actions": result.get("actions"),
                "status": result.get("status"),
                "old_values": old_values,
            }).execute()
            if ins_resp.data:
                opt_record_id = ins_resp.data[0].get("id")
        except Exception as exc:
            logger.warning(f"Failed to persist Meta optimization log: {exc}")

    result["optimization_id"] = opt_record_id
    return result


@app.post(

    f"{settings.API_V1_PREFIX}/google-ads/campaigns/{{campaign_run_id}}/ads/media",
    response_model=LaunchAdResponse,
    tags=["Ads"],
)
async def launch_media_ad(
    campaign_run_id: str,
    file: UploadFile | None = File(None),
    ad_type: str = Form("image"),
    ad_name: str = Form(""),
    final_url: str = Form(...),
    long_headline: str = Form(""),
    business_name: str = Form(""),
    headline_1: str = Form(""),
    description_1: str = Form(""),
    keywords: str = Form(""),
    youtube_url: str = Form(""),
    call_to_action: str = Form(""),
    dry_run: bool = Form(False),
    customer_id: str = Form(""),
    login_customer_id: str = Form(""),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Upload an image or video file and create a real Google Ads asset + ad.

    Accepts multipart/form-data. The file is stored in Supabase Storage and
    the public URL is saved with the campaign_ads row.
    The ad is also created in Google Ads:
      - image  → ImageAsset + Responsive Display Ad
      - video  → YouTubeVideoAsset (from URL) or VideoAsset (from file) + Video Responsive Ad
    """
    user_id = current_user["id"]

    # Verify campaign ownership
    db = get_supabase_admin_client()
    run_resp = (
        db.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select("id,user_id")
        .eq("id", campaign_run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_resp.data:
        raise HTTPException(status_code=404, detail="Campaign run not found or access denied.")

    customer_id_override = customer_id.strip() or None
    login_customer_id_override = login_customer_id.strip() or None
    if not dry_run:
        if not (customer_id_override or os.getenv("CUSTOMER_ID")):
            raise HTTPException(
                status_code=400,
                detail="Missing CUSTOMER_ID. Provide customer_id or set CUSTOMER_ID in environment.",
            )
        if not get_campaign_resource_name_for_run(campaign_run_id):
            raise HTTPException(
                status_code=400,
                detail="Campaign not launched to Google Ads. Launch the campaign before creating ads.",
            )

    # Detect if this is a YouTube-URL-only video (no file upload needed)
    is_youtube_only = (ad_type == "video" and youtube_url and (file is None or not file.filename))

    # Read file bytes (if a real file was sent)
    file_bytes: bytes = b""
    content_type = ""
    filename = ""
    size_bytes = 0
    normalised_ct = ""

    if not is_youtube_only:
        if file is None:
            raise HTTPException(status_code=400, detail="File is required for image ads or non-YouTube video ads.")
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"
        filename = file.filename or "upload"
        size_bytes = len(file_bytes)

        try:
            normalised_ct = validate_media(filename, content_type, size_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Upload to Supabase Storage (only if a real file was provided)
    media_public_url = None
    if file_bytes:
        try:
            media_public_url, _ = upload_ad_media(
                file_bytes=file_bytes,
                original_filename=filename,
                content_type=normalised_ct,
                user_id=user_id,
                campaign_run_id=campaign_run_id,
            )
        except Exception as e:
            logger.exception(f"Supabase Storage upload failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}. Make sure the 'campaign-ads-media' bucket exists in Supabase Storage.",
            )
    elif youtube_url:
        # Store the YouTube URL as the media_url directly
        media_public_url = youtube_url

    # Keyword list from comma-separated string
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]

    ad_payload_dict = {
        "ad_type": ad_type,
        "ad_name": ad_name or None,
        "final_url": final_url,
        "long_headline": long_headline or None,
        "business_name": business_name or None,
        "headline_1": headline_1 or None,
        "description_1": description_1 or None,
        "call_to_action": call_to_action or None,
        "keywords": kw_list,
    }

    # ── Call the correct Google Ads creation function ──────────────────────────
    try:
        if ad_type == "image":
            launch_result = launch_image_ad_to_campaign(
                campaign_run_id=campaign_run_id,
                ad_payload=ad_payload_dict,
                image_bytes=file_bytes,
                image_filename=filename,
                dry_run=dry_run,
                customer_id_override=customer_id_override,
                login_customer_id_override=login_customer_id_override,
            )
        elif ad_type == "video":
            if not dry_run and not youtube_url and file_bytes:
                raise ValueError(
                    "Google Ads requires a YouTube URL for video ads. Upload the video to YouTube and provide youtube_url."
                )
            launch_result = launch_video_ad_to_campaign(
                campaign_run_id=campaign_run_id,
                ad_payload=ad_payload_dict,
                youtube_url=youtube_url or None,
                video_bytes=file_bytes if file_bytes else None,
                video_filename=filename or None,
                dry_run=dry_run,
                customer_id_override=customer_id_override,
                login_customer_id_override=login_customer_id_override,
            )
        else:
            launch_result = {"status": "launched", "ad_resource_name": None, "adgroup_resource_name": None, "ad_name": ad_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Google Ads {ad_type} ad launch failed: {e}")
        raise HTTPException(status_code=502, detail=f"{ad_type.capitalize()} ad launch failed: {str(e)}")

    pseudo_payload = LaunchAdRequest(
        ad_type=ad_type,
        ad_name=ad_name or None,
        final_url=final_url,
        long_headline=long_headline or None,
        business_name=business_name or None,
        headline_1=headline_1 or None,
        description_1=description_1 or None,
        keywords=kw_list,
        dry_run=dry_run or (launch_result.get("status") == "launched_dry_run"),
    )

    try:
        row = _save_campaign_ad(
            campaign_run_id,
            user_id,
            pseudo_payload,
            launch_result,
            media_url=media_public_url,
            media_file_name=filename or None,
            media_content_type=normalised_ct or None,
            media_size_bytes=size_bytes or None,
        )
    except Exception as e:
        logger.exception(f"Failed to save media ad to DB: {e}")
        raise HTTPException(status_code=500, detail=f"DB save failed: {str(e)}")

    logger.info(
        "Media ad launched for user=%s campaign_run_id=%s ad_type=%s gads_status=%s",
        user_id, campaign_run_id, ad_type, launch_result.get("status"),
    )
    return LaunchAdResponse(**row)


@app.get(f"{settings.API_V1_PREFIX}/insights", tags=["Insights"])
async def get_insights():
    """Get insights from historical campaign data"""
    if not data_analyzer:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    return {
        "insights": data_analyzer.get_insights(),
        "summary_stats": data_analyzer.summary_stats
    }

@app.get(f"{settings.API_V1_PREFIX}/model/metrics", 
         response_model=ModelMetrics,
         tags=["Model"])
async def get_model_metrics():
    """Get model performance metrics"""
    if not predictor or not predictor.is_trained:
        raise HTTPException(status_code=503, detail="Models not trained")
    
    return predictor.get_model_metrics()

@app.get(f"{settings.API_V1_PREFIX}/channels", tags=["Data"])
async def get_channels():
    """Get all available channels"""
    if not data_analyzer:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    return {
        "channels": data_analyzer.summary_stats.get('channels', [])
    }

@app.get(f"{settings.API_V1_PREFIX}/campaign-types", tags=["Data"])
async def get_campaign_types():
    """Get all available campaign types"""
    if not data_analyzer:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    return {
        "campaign_types": data_analyzer.summary_stats.get('campaign_types', [])
    }

@app.get(f"{settings.API_V1_PREFIX}/product-types", tags=["Data"])
async def get_product_types():
    """Get all available product types"""
    if not data_analyzer:
        raise HTTPException(status_code=503, detail="Data not loaded")

    return {
        "product_types": data_analyzer.summary_stats.get("product_types", [])
    }

@app.get(f"{settings.API_V1_PREFIX}/segments", tags=["Data"])
async def get_customer_segments():
    """Get all available customer segments"""
    if not data_analyzer:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    return {
        "segments": data_analyzer.summary_stats.get('customer_segments', [])
    }


# ============================================================================
# PORTFOLIO & MULTI-CAMPAIGN ANALYSIS ENDPOINT
# ============================================================================

@app.get(f"{settings.API_V1_PREFIX}/scaleup/portfolio-analysis", tags=["ScaleUp"])
async def get_portfolio_analysis(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Comprehensive portfolio analysis for all user campaigns:
    - Multi-campaign comparison and optimization
    - Budget allocation recommendations
    - Competitive benchmarking
    - Seasonal trends analysis
    - Risk/reward analysis
    - Scaling timeline projections
    """
    try:
        user_id = current_user["id"]
        db = get_supabase_admin_client()
        
        # Get all campaigns for this user
        campaigns_resp = (
            db.table(settings.SUPABASE_CAMPAIGN_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        
        campaigns = campaigns_resp.data or []
        
        if not campaigns:
            return {
                "status": "success",
                "portfolio": {
                    "total_campaigns": 0,
                    "total_budget": 0,
                    "avg_roi": 0,
                    "portfolio_health": "new"
                },
                "message": "No campaigns yet to analyze"
            }
        
        # Portfolio metrics
        total_budget = sum(c.get("budget_max", 0) for c in campaigns)
        roi_values = [c.get("predicted_roi", 1.0) for c in campaigns if c.get("predicted_roi")]
        avg_roi = sum(roi_values) / len(roi_values) if roi_values else 1.0
        
        # Platform performance aggregation
        platform_performance = {}
        for campaign in campaigns:
            output = campaign.get("output") or {}
            recommendations = output.get("recommendations", [])
            launched = campaign.get("launched_platforms", [])
            
            for rec in recommendations:
                platform = rec.get("platform", "Unknown")
                if platform not in platform_performance:
                    platform_performance[platform] = {
                        "total_roi": 0,
                        "count": 0,
                        "total_budget": 0,
                        "campaigns": [],
                        "is_launched": False
                    }
                
                platform_performance[platform]["total_roi"] += rec.get("predicted_roi", 1.0)
                platform_performance[platform]["count"] += 1
                platform_performance[platform]["total_budget"] += rec.get("budget", 0)
                platform_performance[platform]["campaigns"].append(campaign.get("product_name"))
                
                if platform in launched:
                    platform_performance[platform]["is_launched"] = True
        
        # Calculate average ROI per platform
        platform_insights = []
        for platform, data in platform_performance.items():
            avg_platform_roi = data["total_roi"] / data["count"] if data["count"] > 0 else 1.0
            platform_insights.append({
                "platform": platform,
                "avg_roi": round(avg_platform_roi, 2),
                "campaigns_count": data["count"],
                "total_budget": data["total_budget"],
                "is_launched": data["is_launched"],
                "performance_trend": "↑ Strong" if avg_platform_roi >= 2.5 else "→ Stable" if avg_platform_roi >= 1.5 else "↓ Weak"
            })
        
        # Sort by ROI
        platform_insights.sort(key=lambda x: x["avg_roi"], reverse=True)
        
        # Budget allocation recommendation
        if platform_insights:
            total_platform_roi = sum(p["avg_roi"] for p in platform_insights)
            budget_allocation = []
            for platform in platform_insights:
                allocation_pct = (platform["avg_roi"] / total_platform_roi) * 100 if total_platform_roi > 0 else 0
                budget_allocation.append({
                    "platform": platform["platform"],
                    "recommended_allocation": round(allocation_pct, 1),
                    "expected_roi": round(platform["avg_roi"], 2),
                    "rationale": f"Based on {platform['campaigns_count']} campaigns with avg {platform['avg_roi']:.1f}x ROI"
                })
        else:
            budget_allocation = []
        
        # Industry benchmarks (simulated based on goal types)
        industry_benchmarks = {
            "roi": {"average": 1.8, "top_performer": 3.2, "your_performance": round(avg_roi, 2)},
            "conversion_rate": {"average": 2.5, "top_performer": 4.2, "your_performance": round(avg_roi * 1.2, 1)},
            "cpc": {"average": 1.5, "top_performer": 0.8, "your_performance": round(2.0 - (avg_roi * 0.3), 2)},
        }
        
        # Performance rank
        if avg_roi >= 3.0:
            rank = "Top 10% - Excellent"
            rank_percentile = 95
        elif avg_roi >= 2.3:
            rank = "Top 25% - Very Good"
            rank_percentile = 85
        elif avg_roi >= 1.8:
            rank = "Top 50% - Good"
            rank_percentile = 65
        elif avg_roi >= 1.2:
            rank = "Average"
            rank_percentile = 45
        else:
            rank = "Below Average"
            rank_percentile = 20
        
        # Seasonal trends (simulated with campaign creation patterns)
        from datetime import datetime, timedelta
        seasonal_analysis = []
        today = datetime.now()
        
        for month_back in range(0, 6):
            target_date = today - timedelta(days=30*month_back)
            month_name = target_date.strftime("%B")
            
            # Count campaigns in this month
            campaigns_this_month = [
                c for c in campaigns 
                if c.get("created_at") and 
                   target_date.replace(day=1) <= datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")) < target_date.replace(day=1) + timedelta(days=32)
            ]
            
            if campaigns_this_month:
                month_avg_roi = sum(c.get("predicted_roi", 1.0) for c in campaigns_this_month) / len(campaigns_this_month)
                seasonal_analysis.append({
                    "month": month_name,
                    "campaigns": len(campaigns_this_month),
                    "avg_roi": round(month_avg_roi, 2),
                    "opportunity": "↑ High" if month_avg_roi >= avg_roi * 1.2 else "→ Normal" if month_avg_roi >= avg_roi * 0.8 else "↓ Low"
                })
        
        # Scaling timeline recommendations
        scaling_timelines = []
        goals = [10000, 25000, 50000]
        current_monthly_roi = total_budget * avg_roi
        
        for goal in goals:
            if current_monthly_roi > 0:
                months_to_goal = goal / current_monthly_roi
                recommended_budget = total_budget * (goal / current_monthly_roi)
                scaling_timelines.append({
                    "goal": f"${goal:,}",
                    "current_monthly_roi": round(current_monthly_roi, 0),
                    "months_to_reach": round(months_to_goal, 1),
                    "recommended_budget": round(recommended_budget, 0),
                    "timeline_description": f"Increase budget to ${recommended_budget:,.0f} to reach ${goal:,} ROI in ~{months_to_goal:.0f} month(s)"
                })
        
        # Risk/reward analysis
        risk_reward = []
        budget_increases = [20, 50, 100]
        
        for increase in budget_increases:
            new_budget = total_budget * (1 + increase/100)
            projected_roi = new_budget * avg_roi
            risk_level = "Low" if increase <= 20 else "Medium" if increase <= 50 else "High"
            reward_potential = round(projected_roi - (total_budget * avg_roi), 0)
            
            risk_reward.append({
                "budget_increase": f"+{increase}%",
                "new_budget": round(new_budget, 0),
                "projected_roi": round(projected_roi, 0),
                "additional_revenue": round(reward_potential, 0),
                "risk_level": risk_level,
                "confidence": "High" if increase <= 30 else "Medium"
            })
        
        # Market timing insights
        market_insights = {
            "best_time_to_scale": "Next 2 weeks",
            "market_trend": "↑ Upward - Good time to increase spend",
            "competitor_activity": "Moderate - Lower competition expected",
            "seasonal_opportunity": "Peak season starting in 3 weeks",
            "recommended_action": "Start scaling now to capitalize on seasonal opportunity"
        }
        
        return {
            "status": "success",
            "portfolio": {
                "total_campaigns": len(campaigns),
                "total_budget": round(total_budget, 0),
                "avg_roi": round(avg_roi, 2),
                "portfolio_health": "Excellent" if avg_roi >= 2.5 else "Good" if avg_roi >= 1.8 else "Fair" if avg_roi >= 1.2 else "Needs Attention"
            },
            "platform_performance": platform_insights,
            "budget_allocation": budget_allocation,
            "industry_benchmarks": industry_benchmarks,
            "performance_rank": {
                "rank": rank,
                "percentile": rank_percentile,
                "insight": f"Your portfolio outperforms {100 - rank_percentile}% of similar campaigns"
            },
            "seasonal_trends": seasonal_analysis,
            "scaling_timelines": scaling_timelines,
            "risk_reward_analysis": risk_reward,
            "market_timing": market_insights,
            "competitive_insights": {
                "strongest_platform": platform_insights[0]["platform"] if platform_insights else "Unknown",
                "platform_dominance": round((platform_insights[0]["avg_roi"] / avg_roi) * 100, 0) if platform_insights and avg_roi > 0 else 100,
                "opportunities": "Expand Google Ads presence for better ROI" if platform_insights and "Google Ads" not in [p["platform"] for p in platform_insights[:2]] else "Current platform mix is optimal"
            }
        }
    
    except Exception as e:
        logger.exception(f"Portfolio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================================================
# SCALEUP ANALYSIS ENDPOINT
# ============================================================================

@app.get(f"{settings.API_V1_PREFIX}/scaleup/campaign/{{campaign_id}}/analysis", tags=["ScaleUp"])
async def get_campaign_scaleup_analysis(campaign_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Analyze a specific campaign and provide scaling recommendations.
    
    Returns:
    - Campaign performance metrics
    - ROI by platform
    - Scaling recommendations (increase budget vs switch platform)
    - Comparison with other platforms
    """
    try:
        user_id = current_user["id"]
        db = get_supabase_admin_client()
        
        # Get the specific campaign
        campaign_resp = (
            db.table(settings.SUPABASE_CAMPAIGN_TABLE)
            .select("*")
            .eq("id", campaign_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        
        if not campaign_resp.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = campaign_resp.data
        output = campaign.get("output") or {}
        recommendations = output.get("recommendations", [])
        launched_platforms = campaign.get("launched_platforms", [])
        
        # Build platform comparison for this specific campaign
        platform_options = []
        best_platform = None
        best_roi = 0
        
        for rec in recommendations:
            platform = rec.get("platform", "Unknown")
            predicted_roi = rec.get("predicted_roi", 1.0)
            predicted_cr = rec.get("predicted_conversion_rate", 2.0)
            budget = rec.get("budget", "0")
            
            try:
                budget_val = float(str(budget).replace("$", "").replace(",", ""))
            except (ValueError, TypeError):
                budget_val = 0
            
            is_launched = platform in launched_platforms
            
            platform_option = {
                "platform": platform,
                "predicted_roi": predicted_roi,
                "predicted_conversion_rate": predicted_cr,
                "budget": budget_val,
                "is_launched": is_launched,
                "confidence": rec.get("confidence", "Medium"),
                "rationale": rec.get("rationale", "")
            }
            platform_options.append(platform_option)
            
            # Track best platform
            if predicted_roi > best_roi:
                best_roi = predicted_roi
                best_platform = platform_option
        
        # Determine scaling recommendation
        scaling_action = "none"
        scaling_reason = ""
        suggested_increase = None
        recommended_platform = None
        
        if best_platform:
            if best_platform["is_launched"]:
                # Campaign is already on best platform - recommend scaling up budget
                if best_platform["predicted_roi"] >= 2.0:
                    scaling_action = "scale_up_budget"
                    suggested_increase = best_platform["budget"] * 1.5  # 50% increase
                    scaling_reason = f"This campaign shows strong ROI of {best_platform['predicted_roi']:.2f}x on {best_platform['platform']}. Scale up the budget by 50% to increase returns."
                else:
                    scaling_action = "maintain"
                    scaling_reason = f"ROI is stable at {best_platform['predicted_roi']:.2f}x. Monitor performance before scaling."
            else:
                # Campaign not on best platform yet - recommend launch or switch
                launched_platform = launched_platforms[0] if launched_platforms else None
                if launched_platform:
                    current_rec = next((r for r in recommendations if r.get("platform") == launched_platform), None)
                    current_roi = current_rec.get("predicted_roi", 1.0) if current_rec else 1.0
                    
                    if best_platform["predicted_roi"] > current_roi * 1.5:
                        scaling_action = "switch_platform"
                        recommended_platform = best_platform["platform"]
                        scaling_reason = f"{best_platform['platform']} shows {(best_platform['predicted_roi'] / current_roi):.1f}x better ROI ({best_platform['predicted_roi']:.2f}x vs {current_roi:.2f}x). Consider moving budget here."
                    else:
                        scaling_action = "add_platform"
                        recommended_platform = best_platform["platform"]
                        scaling_reason = f"Expand to {best_platform['platform']} to diversify. Expected ROI: {best_platform['predicted_roi']:.2f}x"
                else:
                    scaling_action = "launch"
                    recommended_platform = best_platform["platform"]
                    scaling_reason = f"Launch on {best_platform['platform']} for best expected ROI: {best_platform['predicted_roi']:.2f}x"
        
        # Sort platforms by ROI for comparison
        sorted_platforms = sorted(platform_options, key=lambda x: x["predicted_roi"], reverse=True)
        
        return {
            "status": "success",
            "campaign": {
                "id": campaign_id,
                "name": campaign.get("product_name"),
                "goal": campaign.get("campaign_goal"),
                "budget_range": {
                    "min": campaign.get("budget_min", 0),
                    "max": campaign.get("budget_max", 0)
                },
                "predicted_roi": campaign.get("predicted_roi", 1.0),
                "launched_platforms": launched_platforms
            },
            "platform_analysis": sorted_platforms,
            "best_platform": best_platform,
            "scaling_recommendation": {
                "action": scaling_action,
                "reason": scaling_reason,
                "suggested_budget": suggested_increase,
                "recommended_platform": recommended_platform
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Campaign scaleup analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
