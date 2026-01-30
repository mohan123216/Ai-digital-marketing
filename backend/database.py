# database.py - Updated with campaign planning functions
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_benchmark(entry):
    """Insert benchmark data"""
    data = {
        "platform": entry.get("platform"),
        "industry": entry.get("industry"),
        "metric": entry.get("metric"),
        "value": entry.get("value"),
        "creative_insight": entry.get("creative_insight"),
        "source": "WordStream"
    }
    response = supabase.table("ad_benchmarks").insert(data).execute()
    return response

# ==================== CAMPAIGN PLANNING FUNCTIONS ====================

def create_campaign(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new campaign and store all related data
    """
    try:
        # 1. Insert main campaign
        campaign_response = supabase.table("campaigns").insert({
            "name": campaign_data.get("name", f"Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
            "goal": campaign_data["goal"],
            "budget": float(campaign_data["budget"]),
            "industry": campaign_data.get("industry", "ecommerce"),
            "duration_days": int(campaign_data.get("duration", 30)),
            "status": "planning"
        }).execute()
        
        campaign = campaign_response.data[0]
        campaign_id = campaign["id"]
        
        # 2. Insert audience data
        audience = campaign_data.get("audience", {})
        if audience:
            supabase.table("campaign_audience").insert({
                "campaign_id": campaign_id,
                "age_min": audience.get("age", {}).get("min", 18),
                "age_max": audience.get("age", {}).get("max", 65),
                "genders": audience.get("gender", ["all"]),
                "interests": audience.get("interests", []),
                "location": audience.get("location", "Global"),
                "income_level": audience.get("income", "all")
            }).execute()
        
        # 3. Insert platforms
        platforms = campaign_data.get("platforms", [])
        for platform in platforms:
            supabase.table("campaign_platforms").insert({
                "campaign_id": campaign_id,
                "platform": platform,
                "allocated_budget": float(campaign_data["budget"]) / len(platforms) if platforms else 0,
                "status": "planned"
            }).execute()
        
        print(f"✅ Campaign created successfully: {campaign_id}")
        return {
            "success": True,
            "campaign_id": campaign_id,
            "campaign": campaign
        }
        
    except Exception as e:
        print(f"❌ Error creating campaign: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def save_ai_recommendations(campaign_id: str, recommendations: List[Dict[str, Any]]) -> bool:
    """
    Save AI recommendations for a campaign
    """
    try:
        for rec in recommendations:
            supabase.table("ai_recommendations").insert({
                "campaign_id": campaign_id,
                "title": rec.get("title", ""),
                "description": rec.get("description", ""),
                "category": rec.get("action", "").split("_")[0] if "_" in rec.get("action", "") else "general",
                "confidence_score": rec.get("confidence", 50),
                "impact_level": rec.get("impact", "medium").lower(),
                "action_type": rec.get("action", ""),
                "applied": False
            }).execute()
        
        print(f"✅ Saved {len(recommendations)} AI recommendations for campaign: {campaign_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving AI recommendations: {e}")
        return False

def save_campaign_predictions(campaign_id: str, predictions: Dict[str, Any]) -> bool:
    """
    Save campaign performance predictions
    """
    try:
        # Parse string values to float where needed
        def parse_value(value):
            if isinstance(value, str):
                # Remove $, %, x symbols and convert to float
                value = value.replace('$', '').replace('%', '').replace('x', '')
                try:
                    return float(value)
                except:
                    return 0.0
            return value
        
        supabase.table("campaign_predictions").insert({
            "campaign_id": campaign_id,
            "estimated_reach": int(predictions.get("estimated_reach", 0)),
            "estimated_clicks": int(predictions.get("estimated_clicks", 0)),
            "estimated_conversions": int(predictions.get("estimated_conversions", 0)),
            "estimated_ctr": parse_value(predictions.get("estimated_ctr", "0%")),
            "estimated_cpc": parse_value(predictions.get("estimated_cpc", "$0")),
            "estimated_cpa": parse_value(predictions.get("estimated_cpa", "$0")),
            "estimated_roas": parse_value(predictions.get("estimated_roas", "0x")),
            "audience_score": int(predictions.get("audience_score", 50))
        }).execute()
        
        print(f"✅ Saved predictions for campaign: {campaign_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving predictions: {e}")
        return False

def save_benchmark_comparison(campaign_id: str, benchmark_data: List[Dict[str, Any]]) -> bool:
    """
    Save benchmark comparisons for campaign
    """
    try:
        for bench in benchmark_data:
            supabase.table("campaign_benchmark_comparison").insert({
                "campaign_id": campaign_id,
                "platform": bench.get("platform"),
                "metric": bench.get("metric"),
                "campaign_value": bench.get("campaign_value"),
                "benchmark_value": bench.get("benchmark_value"),
                "difference_percentage": bench.get("difference_percentage", 0)
            }).execute()
        
        print(f"✅ Saved benchmark comparisons for campaign: {campaign_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving benchmark comparisons: {e}")
        return False

def get_campaign_by_id(campaign_id: str) -> Optional[Dict[str, Any]]:
    """
    Get campaign details with all related data
    """
    try:
        # Get campaign
        campaign_response = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
        if not campaign_response.data:
            return None
        
        campaign = campaign_response.data[0]
        
        # Get audience
        audience_response = supabase.table("campaign_audience").select("*").eq("campaign_id", campaign_id).execute()
        
        # Get platforms
        platforms_response = supabase.table("campaign_platforms").select("*").eq("campaign_id", campaign_id).execute()
        
        # Get AI recommendations
        recommendations_response = supabase.table("ai_recommendations").select("*").eq("campaign_id", campaign_id).execute()
        
        # Get predictions
        predictions_response = supabase.table("campaign_predictions").select("*").eq("campaign_id", campaign_id).execute()
        
        return {
            "campaign": campaign,
            "audience": audience_response.data[0] if audience_response.data else {},
            "platforms": platforms_response.data,
            "recommendations": recommendations_response.data,
            "predictions": predictions_response.data[0] if predictions_response.data else {}
        }
        
    except Exception as e:
        print(f"❌ Error getting campaign: {e}")
        return None

def update_campaign_status(campaign_id: str, status: str) -> bool:
    """
    Update campaign status
    """
    try:
        supabase.table("campaigns").update({
            "status": status,
            "updated_at": datetime.now().isoformat()
        }).eq("id", campaign_id).execute()
        
        if status == "active":
            supabase.table("campaigns").update({
                "launched_at": datetime.now().isoformat()
            }).eq("id", campaign_id).execute()
        
        print(f"✅ Updated campaign {campaign_id} status to: {status}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating campaign status: {e}")
        return False

def get_industry_benchmarks(industry: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get benchmarks for specific industry and platform
    """
    try:
        query = supabase.table("ad_benchmarks").select("*").eq("industry", industry.lower())
        
        if platform:
            query = query.eq("platform", platform)
        
        response = query.execute()
        return response.data if response.data else []
        
    except Exception as e:
        print(f"❌ Error getting benchmarks: {e}")
        return []

def get_campaign_performance(campaign_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get performance data for a campaign
    """
    try:
        query = supabase.table("campaign_performance").select("*").eq("campaign_id", campaign_id)
        
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
        
        response = query.execute()
        return response.data
        
    except Exception as e:
        print(f"❌ Error getting campaign performance: {e}")
        return []

def record_campaign_performance(campaign_id: str, performance_data: Dict[str, Any]) -> bool:
    """
    Record actual performance data for a campaign
    """
    try:
        data = {
            "campaign_id": campaign_id,
            "platform": performance_data.get("platform"),
            "date": performance_data.get("date", datetime.now().date().isoformat()),
            "impressions": int(performance_data.get("impressions", 0)),
            "clicks": int(performance_data.get("clicks", 0)),
            "conversions": int(performance_data.get("conversions", 0)),
            "spend": float(performance_data.get("spend", 0)),
            "revenue": float(performance_data.get("revenue", 0)),
            "ctr": calculate_ctr(performance_data.get("clicks", 0), performance_data.get("impressions", 1)),
            "cpc": calculate_cpc(performance_data.get("spend", 0), performance_data.get("clicks", 1)),
            "cpa": calculate_cpa(performance_data.get("spend", 0), performance_data.get("conversions", 1)),
            "roas": calculate_roas(performance_data.get("revenue", 0), performance_data.get("spend", 1))
        }
        
        supabase.table("campaign_performance").insert(data).execute()
        
        print(f"✅ Recorded performance data for campaign: {campaign_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error recording performance: {e}")
        return False

# Helper functions for calculations
def calculate_ctr(clicks: int, impressions: int) -> float:
    return (clicks / impressions * 100) if impressions > 0 else 0.0

def calculate_cpc(spend: float, clicks: int) -> float:
    return spend / clicks if clicks > 0 else 0.0

def calculate_cpa(spend: float, conversions: int) -> float:
    return spend / conversions if conversions > 0 else 0.0

def calculate_roas(revenue: float, spend: float) -> float:
    return revenue / spend if spend > 0 else 0.0

# ==================== ANALYTICS FUNCTIONS ====================

def get_campaign_analytics(campaign_id: str) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a campaign
    """
    try:
        # Get basic campaign info
        campaign_info = get_campaign_by_id(campaign_id)
        if not campaign_info:
            return {}
        
        # Get performance data
        performance_data = get_campaign_performance(campaign_id)
        
        # Calculate totals
        totals = {
            "total_impressions": sum(p.get("impressions", 0) for p in performance_data),
            "total_clicks": sum(p.get("clicks", 0) for p in performance_data),
            "total_conversions": sum(p.get("conversions", 0) for p in performance_data),
            "total_spend": sum(p.get("spend", 0) for p in performance_data),
            "total_revenue": sum(p.get("revenue", 0) for p in performance_data)
        }
        
        # Calculate averages
        totals["avg_ctr"] = calculate_ctr(totals["total_clicks"], totals["total_impressions"])
        totals["avg_cpc"] = calculate_cpc(totals["total_spend"], totals["total_clicks"])
        totals["avg_cpa"] = calculate_cpa(totals["total_spend"], totals["total_conversions"])
        totals["avg_roas"] = calculate_roas(totals["total_revenue"], totals["total_spend"])
        
        # Get platform breakdown
        platform_breakdown = {}
        for p in performance_data:
            platform = p.get("platform", "unknown")
            if platform not in platform_breakdown:
                platform_breakdown[platform] = {
                    "impressions": 0,
                    "clicks": 0,
                    "conversions": 0,
                    "spend": 0,
                    "revenue": 0
                }
            platform_breakdown[platform]["impressions"] += p.get("impressions", 0)
            platform_breakdown[platform]["clicks"] += p.get("clicks", 0)
            platform_breakdown[platform]["conversions"] += p.get("conversions", 0)
            platform_breakdown[platform]["spend"] += p.get("spend", 0)
            platform_breakdown[platform]["revenue"] += p.get("revenue", 0)
        
        # Calculate metrics for each platform
        for platform, data in platform_breakdown.items():
            data["ctr"] = calculate_ctr(data["clicks"], data["impressions"])
            data["cpc"] = calculate_cpc(data["spend"], data["clicks"])
            data["cpa"] = calculate_cpa(data["spend"], data["conversions"])
            data["roas"] = calculate_roas(data["revenue"], data["spend"])
        
        return {
            "campaign_info": campaign_info,
            "performance_totals": totals,
            "platform_breakdown": platform_breakdown,
            "performance_history": performance_data,
            "recommendations_applied": len([r for r in campaign_info.get("recommendations", []) if r.get("applied")]),
            "total_recommendations": len(campaign_info.get("recommendations", []))
        }
        
    except Exception as e:
        print(f"❌ Error getting campaign analytics: {e}")
        return {}