from flask import Flask, request, jsonify, g
from flask_cors import CORS
import json
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database import (
    supabase,
    create_campaign,
    get_campaign_by_id,
    update_campaign_status
)
from planning_agent import get_campaign_plan

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ==================== AUTH CONFIG ====================
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "dev-secret-change-me"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))


def create_access_token(user):
    payload = {
        "sub": user["id"],
        "email": user.get("email"),
        "name": user.get("name"),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRES_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "", 1).strip()
    return None


def get_user_from_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        response = supabase.table("users").select("id, name, email").eq("id", user_id).execute()
        if not response.data:
            return None
        return response.data[0]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Missing or invalid authorization token"}), 401
        user = get_user_from_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper

# ==================== HEALTH CHECK ====================
@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Digital Marketing Backend is running',
        'api_version': '1.0'
    }), 200


# ==================== AUTH ENDPOINTS ====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """
    Create a new user account
    Expected JSON: { "name": "...", "email": "...", "password": "..." }
    """
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        existing = supabase.table('users').select('id').eq('email', email).execute()
        if existing.data:
            return jsonify({'error': 'Email is already registered'}), 409

        password_hash = generate_password_hash(password)
        response = supabase.table('users').insert({
            'name': name or email.split('@')[0],
            'email': email,
            'password_hash': password_hash
        }).execute()

        user = response.data[0]
        token = create_access_token(user)

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'name': user.get('name'),
                'email': user.get('email')
            }
        }), 201

    except Exception as e:
        print(f"❌ Error during signup: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login user
    Expected JSON: { "email": "...", "password": "..." }
    """
    try:
        data = request.json or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        response = supabase.table('users').select('*').eq('email', email).execute()
        if not response.data:
            return jsonify({'error': 'Invalid credentials'}), 401

        user = response.data[0]
        if not check_password_hash(user.get('password_hash', ''), password):
            return jsonify({'error': 'Invalid credentials'}), 401

        token = create_access_token(user)

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'name': user.get('name'),
                'email': user.get('email')
            }
        }), 200

    except Exception as e:
        print(f"❌ Error during login: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/me', methods=['GET'])
@require_auth
def get_current_user():
    """Return the current authenticated user"""
    user = g.current_user
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'name': user.get('name'),
            'email': user.get('email')
        }
    }), 200

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
@require_auth
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
        user = g.current_user
        
        # Validate required fields
        required_fields = ['productName', 'productType', 'goal', 'budget', 'audience', 'platforms']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Prepare campaign data for database
        campaign_data = {
            'user_id': user['id'],
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
        
        # ==================== PLANNING AGENT ====================
        # Step 1: Call Planning Agent to generate campaign plan
        print(f"📌 Triggering Planning Agent for campaign {campaign_id}...")
        agent_input = {
            'product_name': data['productName'],
            'product_type': data['productType'],
            'goal': data['goal'],
            'budget': float(data['budget']),
            'duration': int(data.get('duration', 30)),
            'platforms': data.get('platforms', []),
            'audience': audience_data
        }
        
        campaign_plan = get_campaign_plan(agent_input)
        
        # Step 2: Store plan in database
        if campaign_plan.get('success'):
            try:
                supabase.table('campaign_plans').insert({
                    'campaign_id': campaign_id,
                    'plan_data': json.dumps(campaign_plan['plan']),
                    'benchmarks': json.dumps(campaign_plan['benchmarks']),
                    'raw_response': campaign_plan.get('raw_llm_response', ''),
                    'created_at': datetime.now().isoformat()
                }).execute()
                print(f"✅ Campaign plan saved to database")
            except Exception as e:
                print(f"⚠️ Warning: Could not save plan to database: {e}")
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Campaign created successfully with AI plan',
            'campaign': campaign,
            'plan': campaign_plan.get('plan', {}),
            'benchmarks': campaign_plan.get('benchmarks', {})
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating campaign: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns', methods=['GET'])
@require_auth
def get_all_campaigns():
    """
    Get all campaigns with their details
    """
    try:
        # Get all campaigns
        user = g.current_user
        campaigns_response = supabase.table('campaigns').select('*').eq('user_id', user['id']).execute()
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
@require_auth
def get_campaign(campaign_id):
    """
    Get a specific campaign with all its details
    """
    try:
        # Get main campaign
        user = g.current_user
        campaign_response = supabase.table('campaigns').select('*').eq('id', campaign_id).eq('user_id', user['id']).execute()
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
@require_auth
def update_campaign(campaign_id):
    """
    Update campaign details
    """
    try:
        data = request.json
        user = g.current_user

        existing = supabase.table('campaigns').select('id').eq('id', campaign_id).eq('user_id', user['id']).execute()
        if not existing.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
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
@require_auth
def delete_campaign(campaign_id):
    """
    Delete a campaign and all related data
    """
    try:
        user = g.current_user
        existing = supabase.table('campaigns').select('id').eq('id', campaign_id).eq('user_id', user['id']).execute()
        if not existing.data:
            return jsonify({'error': 'Campaign not found'}), 404

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
@require_auth
def launch_campaign(campaign_id):
    """
    Launch a campaign (update status to active)
    """
    try:
        user = g.current_user
        existing = supabase.table('campaigns').select('id').eq('id', campaign_id).eq('user_id', user['id']).execute()
        if not existing.data:
            return jsonify({'error': 'Campaign not found'}), 404

        supabase.table('campaigns').update({
            'status': 'active',
            'launched_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).eq('id', campaign_id).eq('user_id', user['id']).execute()
        
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


def _format_suggestions_short(text, max_lines=7):
    """Normalize and shorten LLM text into clean bullet lines."""
    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = []
    for line in lines:
        # Remove common bullet/number prefixes and normalize whitespace.
        line = line.lstrip("-*").strip()
        if len(line) >= 2 and line[0].isdigit() and line[1] in {".", ")"}:
            line = line[2:].strip()
        cleaned.append(" ".join(line.split()))

    short_lines = cleaned[:max_lines]
    return "\n".join([f"- {line}" for line in short_lines])


def _format_suggestions_structured(text):
    """Format LLM JSON output into labeled short bullet lines."""
    if not text:
        return ""

    payload = None
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                payload = json.loads(stripped[start:end + 1])
            except json.JSONDecodeError:
                payload = None

    if not isinstance(payload, dict):
        return _format_suggestions_short(text, max_lines=7)

    labels = [
        ("suggested_platform", "Suggested Platform"),
        ("suggested_budget", "Suggested Budget"),
        ("suggested_audience", "Suggested Audience"),
        ("suggested_content", "Suggested Content"),
        ("suggested_timing", "Suggested Timing"),
        ("suggested_kpis", "Suggested KPIs"),
        ("suggested_risks", "Suggested Risks"),
    ]

    lines = []
    for key, label in labels:
        value = payload.get(key)
        if not value:
            continue
        if isinstance(value, list):
            value = ", ".join([str(item) for item in value if item])
        lines.append(f"- {label}: {str(value).strip()}")

    return "\n".join(lines[:7])


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
        
        Based on this data and historical performance patterns, respond ONLY with a JSON object
        using these keys and short values (under 18 words each):
        - suggested_platform
        - suggested_budget
        - suggested_audience
        - suggested_content
        - suggested_timing
        - suggested_kpis
        - suggested_risks
        """
       
        # Call Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(context)
        
        suggestions_text = _format_suggestions_structured(response.text)
        
        # Store suggestions in database
        supabase.table('ai_recommendations').insert({
            'campaign_id': campaign_data.get('id'),
            'title': 'AI Strategy Summary',
            'description': suggestions_text,
            'category': 'strategy',
            'confidence_score': 90.0,
            'impact_level': 'high',
            'action_type': 'strategy',
            'applied': False
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


# ==================== CAMPAIGN PLANNING ====================

@app.route('/api/campaigns/<campaign_id>/plan', methods=['GET'])
@require_auth
def get_campaign_plan_endpoint(campaign_id):
    """
    Get the AI-generated plan for a campaign
    """
    try:
        user = g.current_user
        
        # Verify campaign exists and belongs to user
        campaign_response = supabase.table('campaigns').select('*').eq('id', campaign_id).eq('user_id', user['id']).execute()
        if not campaign_response.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get the campaign plan
        plan_response = supabase.table('campaign_plans').select('*').eq('campaign_id', campaign_id).execute()
        
        if not plan_response.data:
            return jsonify({
                'success': False,
                'message': 'No plan generated yet for this campaign'
            }), 404
        
        plan = plan_response.data[0]
        
        return jsonify({
            'success': True,
            'plan': json.loads(plan['plan_data']) if isinstance(plan['plan_data'], str) else plan['plan_data'],
            'benchmarks': json.loads(plan['benchmarks']) if isinstance(plan['benchmarks'], str) else plan['benchmarks'],
            'created_at': plan['created_at']
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching campaign plan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/campaigns/<campaign_id>/ai-suggestions', methods=['GET', 'POST'])
@require_auth
def get_ai_suggestions(campaign_id):
    """
    Get AI-powered suggestions for a campaign
    Uses Gemini LLM + historical market data
    """
    try:
        # Get campaign details
        user = g.current_user
        campaign_response = supabase.table('campaigns').select('*').eq('id', campaign_id).eq('user_id', user['id']).execute()
        
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
@require_auth
def get_recommendations(campaign_id):
    """
    Get stored AI recommendations for a campaign
    """
    try:
        user = g.current_user
        existing = supabase.table('campaigns').select('id').eq('id', campaign_id).eq('user_id', user['id']).execute()
        if not existing.data:
            return jsonify({'error': 'Campaign not found'}), 404

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


# ==================== MANUAL POST ENDPOINT ====================

@app.route('/api/manual-post', methods=['POST'])
def manual_post():
    """
    Post an ad manually (without API integration)
    Removes campaign from campaigns table and creates record in launched_campaigns table
    """
    try:
        data = request.json
        campaign_id = data.get('campaign_id')
        
        if not campaign_id:
            return jsonify({'error': 'Campaign ID required'}), 400
        
        # Validate required fields
        required_fields = ['platform', 'title', 'description', 'budget', 'duration']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        try:
            # Get campaign details before deletion
            campaign = supabase.table('campaigns').select('*').eq('id', campaign_id).execute()
            if not campaign.data:
                return jsonify({'error': 'Campaign not found'}), 404
            
            campaign_data = campaign.data[0]
            
            # Insert into launched_campaigns table with user-provided data
            launched = supabase.table('launched_campaigns').insert({
                'campaign_id': campaign_id,
                'platform': data.get('platform'),
                'title': data.get('title'),
                'description': data.get('description'),
                'budget': float(data.get('budget', 0)),
                'duration': int(data.get('duration', 30)),
                'target_audience': data.get('target_audience', ''),
                'status': 'active',
                'media_urls': data.get('media_urls', []),
                'ctr': float(data.get('ctr', 0)) if data.get('ctr') else 0,
                'cpc': float(data.get('cpc', 0)) if data.get('cpc') else 0,
                'cpa': float(data.get('cpa', 0)) if data.get('cpa') else 0,
                'impressions': int(data.get('impressions', 0)) if data.get('impressions') else 0,
                'clicks': int(data.get('clicks', 0)) if data.get('clicks') else 0,
                'conversions': int(data.get('conversions', 0)) if data.get('conversions') else 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'launched_at': datetime.now().isoformat()
            }).execute()
            
            # Delete from campaigns table
            supabase.table('campaigns').delete().eq('id', campaign_id).execute()
            
            print(f"✅ Ad posted manually and campaign moved to launched_campaigns")
            
            return jsonify({
                'success': True,
                'message': 'Ad posted successfully!',
                'launched_campaign': launched.data[0] if launched.data else {}
            }), 201
            
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            return jsonify({'error': f'Database error: {str(db_error)}'}), 500
            
    except Exception as e:
        print(f"❌ Error posting manually: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/launched-campaigns', methods=['GET'])
def get_launched_campaigns():
    """
    Get all manually posted campaigns from launched_campaigns table
    """
    try:
        result = supabase.table('launched_campaigns').select('*').order('created_at', desc=True).execute()
        
        return jsonify({
            'success': True,
            'launched_campaigns': result.data if result.data else [],
            'total': len(result.data) if result.data else 0
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting launched campaigns: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/launched-campaigns/<campaign_id>', methods=['PUT'])
def update_launched_campaign(campaign_id):
    """
    Update metrics for a launched campaign
    """
    try:
        data = request.json
        
        metrics_update = {
            'ctr': float(data.get('ctr', 0)) if data.get('ctr') else 0,
            'cpc': float(data.get('cpc', 0)) if data.get('cpc') else 0,
            'cpa': float(data.get('cpa', 0)) if data.get('cpa') else 0,
            'impressions': int(data.get('impressions', 0)) if data.get('impressions') else 0,
            'clicks': int(data.get('clicks', 0)) if data.get('clicks') else 0,
            'conversions': int(data.get('conversions', 0)) if data.get('conversions') else 0,
            'updated_at': datetime.now().isoformat()
        }
        
        supabase.table('launched_campaigns').update(metrics_update).eq('id', campaign_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Metrics updated successfully!',
            'updated_metrics': metrics_update
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating metrics: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
