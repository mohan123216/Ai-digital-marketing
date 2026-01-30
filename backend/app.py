from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from database import (
    supabase,
    create_campaign,
    get_campaign_by_id,
    update_campaign_status
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Load marketing dataset
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'marketing_campaign_dataset.csv')
try:
    marketing_data = pd.read_csv(DATASET_PATH)
    print(f"✅ Loaded marketing dataset with {len(marketing_data)} records")
except Exception as e:
    print(f"⚠️ Warning: Could not load marketing dataset: {e}")
    marketing_data = None

# ==================== CAMPAIGN ENDPOINTS ====================

@app.route('/api/campaigns', methods=['POST'])
def create_new_campaign():
    """
    Create a new campaign with product info and campaign details
    Expected JSON structure:
    {
        "productName": "Product Name",
        "productType": "Product Type",
        "goal": "Campaign Goal",
        "budget": 5000,
        "duration": 30,
        "audience": {
            "age": {"min": 18, "max": 65},
            "gender": ["male", "female"],
            "interests": ["Technology", "Sports"],
            "location": "United States",
            "income": "all"
        },
        "platforms": ["Facebook", "Instagram"]
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['productName', 'productType', 'goal', 'budget', 'audience', 'platforms']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Prepare campaign data for database
        campaign_data = {
            'product_name': data['productName'],
            'product_type': data['productType'],
            'goal': data['goal'],
            'budget': float(data['budget']),
            'duration': int(data.get('duration', 30)),
            'status': 'draft',
            'created_at': datetime.now().isoformat()
        }
        
        # Insert campaign into database
        response = supabase.table('campaigns').insert(campaign_data).execute()
        campaign = response.data[0]
        campaign_id = campaign['id']
        
        # Insert audience data
        audience_data = data.get('audience', {})
        supabase.table('campaign_audience').insert({
            'campaign_id': campaign_id,
            'age_min': audience_data.get('age', {}).get('min', 18),
            'age_max': audience_data.get('age', {}).get('max', 65),
            'genders': audience_data.get('gender', []),
            'interests': audience_data.get('interests', []),
            'location': audience_data.get('location', 'Global'),
            'income_level': audience_data.get('income', 'all')
        }).execute()
        
        # Insert platform data
        platforms = data.get('platforms', [])
        if platforms:
            budget_per_platform = float(data['budget']) / len(platforms)
            for platform in platforms:
                supabase.table('campaign_platforms').insert({
                    'campaign_id': campaign_id,
                    'platform': platform,
                    'allocated_budget': budget_per_platform,
                    'status': 'draft'
                }).execute()
        
        print(f"✅ Campaign created successfully: {campaign_id}")
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Campaign created successfully',
            'campaign': campaign
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating campaign: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns', methods=['GET'])
def get_all_campaigns():
    """
    Get all campaigns with their details
    """
    try:
        # Get all campaigns
        campaigns_response = supabase.table('campaigns').select('*').execute()
        campaigns = campaigns_response.data if campaigns_response.data else []
        
        # Enrich each campaign with its related data
        enriched_campaigns = []
        for campaign in campaigns:
            campaign_id = campaign['id']
            
            # Get audience
            audience_response = supabase.table('campaign_audience').select('*').eq('campaign_id', campaign_id).execute()
            audience = audience_response.data[0] if audience_response.data else {}
            
            # Get platforms
            platforms_response = supabase.table('campaign_platforms').select('*').eq('campaign_id', campaign_id).execute()
            platforms = [p['platform'] for p in platforms_response.data] if platforms_response.data else []
            
            enriched_campaign = {
                **campaign,
                'audience': audience,
                'platforms': platforms
            }
            enriched_campaigns.append(enriched_campaign)
        
        return jsonify({
            'success': True,
            'campaigns': enriched_campaigns,
            'count': len(enriched_campaigns)
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching campaigns: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """
    Get a specific campaign with all its details
    """
    try:
        # Get main campaign
        campaign_response = supabase.table('campaigns').select('*').eq('id', campaign_id).execute()
        if not campaign_response.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        campaign = campaign_response.data[0]
        
        # Get audience
        audience_response = supabase.table('campaign_audience').select('*').eq('campaign_id', campaign_id).execute()
        audience = audience_response.data[0] if audience_response.data else {}
        
        # Get platforms
        platforms_response = supabase.table('campaign_platforms').select('*').eq('campaign_id', campaign_id).execute()
        platforms = platforms_response.data if platforms_response.data else []
        
        # Get AI recommendations if any
        recommendations_response = supabase.table('ai_recommendations').select('*').eq('campaign_id', campaign_id).execute()
        recommendations = recommendations_response.data if recommendations_response.data else []
        
        # Get predictions if any
        predictions_response = supabase.table('campaign_predictions').select('*').eq('campaign_id', campaign_id).execute()
        predictions = predictions_response.data[0] if predictions_response.data else {}
        
        enriched_campaign = {
            **campaign,
            'audience': audience,
            'platforms': platforms,
            'recommendations': recommendations,
            'predictions': predictions
        }
        
        return jsonify({
            'success': True,
            'campaign': enriched_campaign
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching campaign: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns/<campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """
    Update campaign details
    """
    try:
        data = request.json
        
        # Update main campaign fields
        update_data = {}
        if 'goal' in data:
            update_data['goal'] = data['goal']
        if 'budget' in data:
            update_data['budget'] = float(data['budget'])
        if 'duration' in data:
            update_data['duration'] = int(data['duration'])
        if 'status' in data:
            update_data['status'] = data['status']
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update campaign
        supabase.table('campaigns').update(update_data).eq('id', campaign_id).execute()
        
        # Update audience if provided
        if 'audience' in data:
            audience = data['audience']
            supabase.table('campaign_audience').update({
                'age_min': audience.get('age', {}).get('min', 18),
                'age_max': audience.get('age', {}).get('max', 65),
                'genders': audience.get('gender', []),
                'interests': audience.get('interests', []),
                'location': audience.get('location', 'Global'),
                'income_level': audience.get('income', 'all'),
                'updated_at': datetime.now().isoformat()
            }).eq('campaign_id', campaign_id).execute()
        
        # Update platforms if provided
        if 'platforms' in data:
            platforms = data['platforms']
            # Delete old platforms
            supabase.table('campaign_platforms').delete().eq('campaign_id', campaign_id).execute()
            # Add new platforms
            if platforms:
                budget_per_platform = float(data.get('budget', 0)) / len(platforms)
                for platform in platforms:
                    supabase.table('campaign_platforms').insert({
                        'campaign_id': campaign_id,
                        'platform': platform,
                        'allocated_budget': budget_per_platform,
                        'status': 'draft'
                    }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Campaign updated successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating campaign: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns/<campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """
    Delete a campaign and all related data
    """
    try:
        # Delete related data first
        supabase.table('campaign_audience').delete().eq('campaign_id', campaign_id).execute()
        supabase.table('campaign_platforms').delete().eq('campaign_id', campaign_id).execute()
        supabase.table('ai_recommendations').delete().eq('campaign_id', campaign_id).execute()
        supabase.table('campaign_predictions').delete().eq('campaign_id', campaign_id).execute()
        
        # Delete campaign
        supabase.table('campaigns').delete().eq('id', campaign_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Campaign deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Error deleting campaign: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns/<campaign_id>/launch', methods=['POST'])
def launch_campaign(campaign_id):
    """
    Launch a campaign (update status to active)
    """
    try:
        supabase.table('campaigns').update({
            'status': 'active',
            'launched_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).eq('id', campaign_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Campaign launched successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Error launching campaign: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== AI SUGGESTIONS ENDPOINT ====================

def get_historical_performance(platform=None, product_type=None, target_audience=None):
    """
    Get historical performance data from our database
    """
    if marketing_data is None:
        return None
    
    filtered_data = marketing_data.copy()
    
    if platform:
        filtered_data = filtered_data[filtered_data['Channel_Used'].str.contains(platform, case=False, na=False)]
    
    if product_type:
        filtered_data = filtered_data[filtered_data['Campaign_Type'].str.contains(product_type, case=False, na=False)]
    
    if target_audience:
        filtered_data = filtered_data[filtered_data['Target_Audience'].str.contains(target_audience, case=False, na=False)]
    
    if filtered_data.empty:
        return None
    
    # Calculate average metrics
    stats = {
        'avg_conversion_rate': filtered_data['Conversion_Rate'].mean(),
        'avg_roi': filtered_data['ROI'].mean(),
        'avg_engagement_score': filtered_data['Engagement_Score'].mean(),
        'avg_acquisition_cost': filtered_data['Acquisition_Cost'].str.replace('$', '').str.replace(',', '').astype(float).mean(),
        'total_records': len(filtered_data),
        'top_customers': filtered_data['Customer_Segment'].value_counts().head(3).to_dict(),
        'best_duration': filtered_data['Duration'].mode().values[0] if not filtered_data['Duration'].mode().empty else '30 days',
        'best_language': filtered_data['Language'].mode().values[0] if not filtered_data['Language'].mode().empty else 'English'
    }
    
    return stats


def generate_ai_suggestions(campaign_data):
    """
    Generate AI suggestions using Gemini based on campaign data and historical performance
    """
    try:
        # Get campaign details
        product_name = campaign_data.get('product_name', 'Product')
        product_type = campaign_data.get('product_type', 'General')
        goal = campaign_data.get('goal', 'Sales Conversion')
        budget = campaign_data.get('budget', 0)
        duration = campaign_data.get('duration', 30)
        audience_data = campaign_data.get('audience', {})
        platforms = campaign_data.get('platforms', [])
        
        # Get historical insights
        historical_insights = {}
        for platform in platforms:
            historical_insights[platform] = get_historical_performance(
                platform=platform,
                product_type=product_type,
                target_audience=audience_data.get('location', '')
            )
        
        # Build context for Gemini
        context = f"""
        You are an expert AI marketing strategist. Analyze this campaign and provide smart recommendations.
        
        CAMPAIGN DETAILS:
        - Product: {product_name}
        - Type: {product_type}
        - Goal: {goal}
        - Budget: ${budget}
        - Duration: {duration} days
        - Target Audience: {audience_data.get('location', 'Not specified')}, Ages {audience_data.get('age', {}).get('min', 18)}-{audience_data.get('age', {}).get('max', 65)}
        - Platforms: {', '.join(platforms)}
        - Interests: {', '.join(audience_data.get('interests', ['General']))}
        
        HISTORICAL MARKET DATA (from real campaigns):
        {json.dumps(historical_insights, indent=2)}
        
        Based on this data and historical performance patterns, provide:
        1. Platform Strategy - Best platform recommendations with reasoning
        2. Audience Insights - Key audience segments to target
        3. Budget Allocation - How to split budget across platforms
        4. Expected Performance - Realistic ROI and conversion rate estimates
        5. Content Recommendations - Type of content that works best
        6. Timing Strategy - Best days/times to run ads
        7. Risk Mitigation - Potential pitfalls and how to avoid them
        8. Success Metrics - KPIs to track
        
        Format your response clearly with bullet points and specific recommendations.
        """
        print("\navaliable models:")
        models = genai.list_models()
        for m in models:
            print(f"- {m.name} (version: {m.version})")
        print()
        # Call Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(context)
        
        suggestions_text = response.text
        
        # Store suggestions in database
        supabase.table('ai_recommendations').insert({
            'campaign_id': campaign_data.get('id'),
            'recommendation_type': 'strategy',
            'content': suggestions_text,
            'score': 9.0
        }).execute()
        
        return {
            'success': True,
            'suggestions': suggestions_text,
            'historical_insights': historical_insights
        }
        
    except Exception as e:
        print(f"❌ Error generating AI suggestions: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/api/campaigns/<campaign_id>/ai-suggestions', methods=['GET', 'POST'])
def get_ai_suggestions(campaign_id):
    """
    Get AI-powered suggestions for a campaign
    Uses Gemini LLM + historical market data
    """
    try:
        # Get campaign details
        campaign_response = supabase.table('campaigns').select('*').eq('id', campaign_id).execute()
        
        if not campaign_response.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        campaign = campaign_response.data[0]
        
        # Get audience data
        audience_response = supabase.table('campaign_audience').select('*').eq('campaign_id', campaign_id).execute()
        audience = audience_response.data[0] if audience_response.data else {}
        
        # Get platforms data
        platforms_response = supabase.table('campaign_platforms').select('*').eq('campaign_id', campaign_id).execute()
        platforms = [p['platform'] for p in platforms_response.data] if platforms_response.data else []
        
        # Prepare campaign data
        campaign_data = {
            'id': campaign_id,
            'product_name': campaign['product_name'],
            'product_type': campaign['product_type'],
            'goal': campaign['goal'],
            'budget': campaign['budget'],
            'duration': campaign['duration'],
            'audience': {
                'age': {'min': audience.get('age_min', 18), 'max': audience.get('age_max', 65)},
                'location': audience.get('location', 'Global'),
                'interests': audience.get('interests', []),
                'income': audience.get('income_level', 'all')
            },
            'platforms': platforms
        }
        
        # Generate AI suggestions
        result = generate_ai_suggestions(campaign_data)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        print(f"❌ Error in AI suggestions endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns/<campaign_id>/recommendations', methods=['GET'])
def get_recommendations(campaign_id):
    """
    Get stored AI recommendations for a campaign
    """
    try:
        response = supabase.table('ai_recommendations').select('*').eq('campaign_id', campaign_id).execute()
        
        return jsonify({
            'success': True,
            'recommendations': response.data
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching recommendations: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=8000)
