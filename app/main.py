# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from config import settings
from app.models.schemas import (
    AuthCredentials,
    AuthResponse,
    CampaignInput,
    ModelMetrics,
    UserProfile,
    CampaignHistoryItem,
)
from app.services.data_analyzer import DataAnalyzer
from app.services.predictor import CampaignPredictor
from app.services.recommendation_engine import RecommendationEngine
from app.services.auth_service import create_access_token, hash_password, verify_password
from app.services.llm_summarizer import summarize_ml_result
from app.services.supabase_client import get_supabase_admin_client
from app.services.user_store import create_user, get_user_by_email
from app.dependencies.auth import get_current_user

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
    }
    client.table(settings.SUPABASE_CAMPAIGN_TABLE).insert(row).execute()


def _get_user_campaign_history(user_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_admin_client()
    response = (
        client.table(settings.SUPABASE_CAMPAIGN_TABLE)
        .select(
            "id,created_at,product_name,campaign_goal,budget_min,budget_max,top_platform,predicted_roi,output"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    return response.data or []

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
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
        llm_result = summarize_ml_result(
            recommendations,
            product_name=campaign_input.product_name,
            product_type=campaign_input.product_category or "",
        )
        recommendations["llm_summary"] = llm_result.get("llm_summary", "")
        recommendations["keyword_suggestions"] = llm_result.get("keyword_suggestions", [])
        recommendations["llm_model"] = settings.GROQ_MODEL if settings.GROQ_API_KEY else "fallback"
        
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
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch history")

    return [CampaignHistoryItem(**row) for row in rows]

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
