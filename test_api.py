# test_api.py
import requests
import json
from datetime import datetime
import os

BASE_URL = "http://localhost:8000"
SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN", "")

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.json()}")
    return response.status_code == 200

def test_recommendations():
    """Test recommendations endpoint"""
    if not SUPABASE_ACCESS_TOKEN:
        print("\n⚠️ Set SUPABASE_ACCESS_TOKEN environment variable to test authenticated recommendations.")
        return None
    
    # Test case: no age_range input; system selects top age group internally
    test_input = {
        "campaign_goal": "ROI",
        "product_name": "Shoes",
        "product_category": "Footwear",
        "target_audience": {
            "gender": "Men",
            "interests": ["sneakers", "athletic wear", "streetwear"],
            "location": "United States",
            "language": "English",
            "customer_segment": "Sportswear Shoppers"
        },
        "budget_range": {
            "min": 10000,
            "max": 15000
        },
        "duration_days": 30,
        "start_date": str(datetime.now().date())
    }
    
    print("\n" + "="*60)
    print("📨 TESTING RECOMMENDATIONS API")
    print("="*60)
    print(f"Product: {test_input['product_name']}")
    print(f"Goal: {test_input['campaign_goal']}")
    print(f"Budget: ${test_input['budget_range']['min']} - ${test_input['budget_range']['max']}")
    
    headers = {}
    if SUPABASE_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {SUPABASE_ACCESS_TOKEN}"

    response = requests.post(
        f"{BASE_URL}/api/v1/recommendations",
        json=test_input,
        headers=headers,
    )
    
    if response.status_code == 200:
        result = response.json()
        top = result.get("top_preference", result.get("top_recommendation", {}))

        print("\n✅ TOP PREFERENCE")
        print("="*60)
        print(f"Platform: {top.get('platform')}")
        print(f"Target Segment: {top.get('target_segment')}")
        print(f"Age Group (System Selected): {top.get('target_age_group')}")
        print(f"Location: {top.get('target_location')}")
        print(f"Predicted ROI: {top.get('predicted_roi')}x")
        print(f"Predicted Conversion: {top.get('predicted_conversion_rate')}%")
        print(f"Confidence: {top.get('confidence')}")
        
        return result
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_model_metrics():
    """Test model metrics endpoint"""
    response = requests.get(f"{BASE_URL}/api/v1/model/metrics")
    if response.status_code == 200:
        metrics = response.json()
        print("\n" + "="*60)
        print("📈 MODEL METRICS")
        print("="*60)
        print(f"ROI Model R²: {metrics['roi_model_r2']:.4f}")
        print(f"ROI Model RMSE: {metrics['roi_model_rmse']:.2f}")
        print(f"Conversion Model R²: {metrics['conversion_model_r2']:.4f}")
        print(f"Conversion Model RMSE: {metrics['conversion_model_rmse']:.4f}")
        print(f"Data Records: {metrics['data_records']}")
        print(f"Last Trained: {metrics['last_trained']}")
        
        print("\n🔍 Feature Importance:")
        for feature, importance in sorted(metrics['feature_importance'].items(), 
                                         key=lambda x: x[1], reverse=True):
            print(f"  {feature}: {importance:.4f}")
    else:
        print(f"Error: {response.status_code}")

def test_insights():
    """Test insights endpoint"""
    response = requests.get(f"{BASE_URL}/api/v1/insights")
    if response.status_code == 200:
        insights = response.json()
        print("\n" + "="*60)
        print("💡 DATA INSIGHTS")
        print("="*60)
        for insight in insights['insights']:
            print(f"  • {insight}")
        
        print("\n📊 Summary Stats:")
        stats = insights['summary_stats']
        print(f"  Total Records: {stats['total_records']:,}")
        print(f"  Avg ROI: {stats['roi']['mean']:.2f} ± {stats['roi']['std']:.2f}")
        print(f"  Avg Conversion: {stats['conversion_rate']['mean']:.2%}")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTING PLANNING AGENT API")
    print("="*60)
    
    # Test health first
    if test_health():
        # Run only prediction output
        test_recommendations()
    else:
        print("❌ API not available. Make sure the server is running.")
