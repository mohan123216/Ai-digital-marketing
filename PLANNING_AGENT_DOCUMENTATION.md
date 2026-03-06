# Planning Agent - Campaign Creation Flow
## AI-Powered Campaign Planning System

**Status**: ✅ **ACTIVE & RUNNING**  
**Backend**: http://127.0.0.1:8000  
**Date**: February 24, 2026

---

## 🎯 Overview

The Planning Agent is an intelligent system that automates campaign planning by:
1. **Accepting campaign inputs** from users
2. **Analyzing dataset benchmarks** from 200,000 historical campaigns
3. **Querying LLM (Google Gemini)** for AI-powered recommendations
4. **Structuring responses** in a standardized JSON format
5. **Storing plans** in the database for retrieval

---

## 📊 System Architecture

```
User Creates Campaign
        ↓
Campaign Data Validated
        ↓
Campaign Saved to Database
        ↓
    ┌─────────────────────────────────┐
    │   PLANNING AGENT TRIGGERED      │
    └─────────────────────────────────┘
        ↓
├─ Step 1: Load Dataset (200K records)
│
├─ Step 2: Get Relevant Benchmarks
│   • Filter by product type
│   • Filter by platform/channel
│   • Calculate metrics:
│     - Avg Conversion Rate
│     - Avg ROI
│     - Avg Customer Acquisition Cost
│     - Avg Engagement Score
│     - Avg CTR
│
├─ Step 3: Format LLM Prompt
│   (Includes campaign data + benchmarks)
│
├─ Step 4: Call LLM (Google Gemini)
│   Returns structured planning recommendations
│
├─ Step 5: Parse & Structure Response
│   JSON with keys:
│   - strategy_overview
│   - budget_allocation
│   - kpi_targets
│   - content_strategy
│   - audience_refinements
│   - risk_assessment
│   - success_metrics
│
└─ Step 6: Store Plan in Database
        ↓
Return Plan to Frontend
```

---

## 📁 New Files & Changes

### 1. **planning_agent.py** (NEW)
**Location**: `backend/planning_agent.py`

**Key Components**:
- `CampaignPlanningAgent` class
- `_load_dataset()` - Loads 200K marketing records
- `_get_relevant_benchmarks()` - Filters historical data
- `_format_llm_prompt()` - Builds context-aware prompt
- `_parse_llm_response()` - Extracts JSON from LLM response
- `plan_campaign()` - Main orchestration method

**Usage**:
```python
from planning_agent import get_campaign_plan

campaign_data = {
    'product_name': 'Nike Shoes',
    'product_type': 'Footwear',
    'goal': 'Increase Sales',
    'budget': 10000,
    'platforms': ['Facebook', 'Instagram'],
    'audience': {...}
}

result = get_campaign_plan(campaign_data)
```

### 2. **app.py** (MODIFIED)
**Changes**:
- Added import: `from planning_agent import get_campaign_plan`
- Modified `@app.post('/api/campaigns')` endpoint
- Integrated agent call in campaign creation flow
- Saves plan to `campaign_plans` table
- Returns plan in response

**New Endpoint**:
```
GET /api/campaigns/<campaign_id>/plan
Returns: {
    success: boolean,
    plan: {...structured recommendations...},
    benchmarks: {...historical metrics...},
    created_at: timestamp
}
```

### 3. **schema.sql** (MODIFIED)
**New Table**: `campaign_plans`
```sql
CREATE TABLE campaign_plans (
  id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
  plan_data JSON NOT NULL,
  benchmarks JSON NOT NULL,
  raw_response TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**RLS Policies added for secure access**

---

## 🚀 Campaign Creation Flow (NEW)

### Request
```bash
POST /api/campaigns
Authorization: Bearer <token>

{
    "productName": "Nike Performance Shoes",
    "productType": "Footwear",
    "goal": "Increase Online Sales",
    "budget": 15000,
    "duration": 60,
    "audience": {
        "age": {"min": 20, "max": 45},
        "gender": ["male", "female"],
        "interests": ["Sports", "Fitness"],
        "location": "United States",
        "income": "middle-high"
    },
    "platforms": ["Facebook", "Instagram", "TikTok"]
}
```

### Response
```json
{
    "success": true,
    "campaign_id": "12345",
    "message": "Campaign created successfully with AI plan",
    "campaign": {...campaign_data...},
    "plan": {
        "strategy_overview": "Focus on high-engagement sports content...",
        "budget_allocation": {
            "Facebook": 5000,
            "Instagram": 5000,
            "TikTok": 5000
        },
        "kpi_targets": {
            "conversion_rate": "2.5%",
            "roi": "300%",
            "ctr": "1.8%"
        },
        "content_strategy": [
            "Athlete testimonials and performance demos",
            "Behind-the-scenes product quality footage",
            "User-generated content from satisfied customers"
        ],
        "audience_refinements": [
            "Add gym enthusiasts and marathon runners",
            "Target college athletes separately",
            "Focus on eco-conscious consumers"
        ],
        "risk_assessment": [
            "Competition from established brands",
            "Market saturation on major platforms",
            "Seasonal demand fluctuations"
        ],
        "success_metrics": [
            "Track daily conversion rates vs. benchmarks",
            "Monitor engagement rate changes",
            "Measure customer acquisition cost trends"
        ]
    },
    "benchmarks": {
        "avg_conversion_rate": 0.0185,
        "avg_roi": 2.45,
        "avg_cac": 28.50,
        "avg_engagement_score": 68.5,
        "avg_ctr": 0.0142,
        "data_points_used": 4250
    }
}
```

---

## 💾 Retrieving Campaign Plans

### Request
```bash
GET /api/campaigns/12345/plan
Authorization: Bearer <token>
```

### Response
```json
{
    "success": true,
    "plan": {...structured recommendations...},
    "benchmarks": {...historical metrics...},
    "created_at": "2026-02-24T10:30:00"
}
```

---

## 📊 Dataset Context

**Source File**: `marketing_campaign_dataset.csv`  
**Records**: 200,000 historical campaigns  
**Columns**: 16 metrics including:
- Campaign_ID, Company, Campaign_Type
- Target_Audience, Duration, Channel_Used
- Conversion_Rate, Acquisition_Cost, ROI
- Location, Language, Clicks, Impressions
- Engagement_Score, Customer_Segment, Date

**Benchmarks Generated From**:
- Similar product types
- Same/related advertising channels
- Comparable audience demographics
- Historical performance data

---

## 🤖 LLM Integration

**Model**: Google Generative AI (Gemini Pro)  
**Configuration**: `backend/planning_agent.py` (lines 18-20)

**Prompt Structure**:
1. Campaign Details
2. Industry Benchmarks
3. Request for specific recommendations
4. JSON format requirement

**Response Parsing**:
- Extracts JSON from LLM response
- Maps to standardized keys
- Validates structure before storage

---

## ✅ Testing the Flow

### Test 1: Check Backend Status
```bash
curl http://127.0.0.1:8000/
# Should return: {"status": "healthy"}
```

### Test 2: Create Campaign with Plan
```bash
curl -X POST http://127.0.0.1:8000/api/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @campaign_request.json
```

### Test 3: Retrieve Plan
```bash
curl http://127.0.0.1:8000/api/campaigns/123/plan \
  -H "Authorization: Bearer <token>"
```

---

## 🔄 Workflow Summary

| Step | Component | Action | Output |
|------|-----------|--------|---------|
| 1 | Frontend | User inputs campaign data | Campaign request |
| 2 | API | Validate & store campaign | campaign_id |
| 3 | Planning Agent | Load dataset & benchmarks | Relevant metrics |
| 4 | Planning Agent | Call LLM with context | AI recommendations |
| 5 | Planning Agent | Parse & structure response | JSON plan |
| 6 | Database | Store plan | Plan record |
| 7 | API | Return response | Plan to frontend |

---

## 📋 File Locations

```
backend/
├── app.py ..................... Main Flask application (MODIFIED)
├── planning_agent.py ........... New Planning Agent (NEW)
├── database.py ................. Database functions
├── schema.sql .................. Database schema (MODIFIED)
├── marketing_campaign_dataset.csv .. Dataset (200K records)
└── requirements.txt ............ Dependencies
```

---

## 🔧 Environment Variables Required

```
GOOGLE_API_KEY=your-google-genai-api-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
JWT_SECRET=your-jwt-secret
```

---

## 📈 Next Steps

1. ✅ Test campaign creation with planning agent
2. ✅ Verify benchmark calculations
3. ✅ Test LLM response parsing
4. ✅ Validate JSON structure
5. Test frontend integration with new endpoints
6. Monitor plan quality and accuracy
7. Refine LLM prompts based on results
8. Add plan versioning (track plan updates)
9. Add plan comparison (A/B planning)
10. Add plan execution tracking

---

## 🎯 Key Features

✅ **Automatic Plan Generation** - Plans created instantly on campaign initialization  
✅ **Data-Driven** - Uses 200K historical campaigns for benchmarks  
✅ **LLM-Powered** - Google Gemini provides intelligent recommendations  
✅ **Structured Output** - JSON format ensures consistency  
✅ **Persistent Storage** - Plans saved for future reference  
✅ **Retrieved on Demand** - Plans accessible via dedicated endpoint  

---

**System Status**: ✅ **OPERATIONAL**  
**Backend**: http://127.0.0.1:8000  
**Checkpoint**: crt_version  

Ready for testing and frontend integration!
