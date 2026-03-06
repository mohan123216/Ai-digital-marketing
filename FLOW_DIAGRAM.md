# Complete Project Flow Diagram

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                    (React Frontend @ :3000)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Navbar       │  │ Auth Page    │  │ Campaign     │           │
│  │ Navigation   │  │ Login/Signup │  │ Wizard       │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Analytics    │  │ Stats Cards  │  │ AI           │           │
│  │ Charts       │  │ KPIs         │  │ Recommendations          │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
│              ┌─────────────────────────┐                         │
│              │   API Service Layer     │                         │
│              │  (api.js)               │                         │
│              │  (campaignService.js)   │                         │
│              └────────────┬────────────┘                         │
└─────────────────────────────┼───────────────────────────────────┘
                              │ HTTP REST API
                              │ JSON Requests/Responses
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND (Flask @ :8000)                             │
│                     (app.py)                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Auth Routes  │  │ Campaign     │  │ AI           │           │
│  │ /api/auth/*  │  │ Routes       │  │ Routes       │           │
│  │              │  │ /api/        │  │ /api/        │           │
│  │              │  │ campaigns/*  │  │ suggestions/*│           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Health Check │  │ Error        │  │ CORS         │           │
│  │ /api/health  │  │ Handler      │  │ Middleware   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
│           ┌────────────────────────────┐                         │
│           │   Database Functions       │                         │
│           │  (database.py)             │                         │
│           │  - CRUD operations         │                         │
│           │  - Query builders          │                         │
│           └────────────┬───────────────┘                         │
│                        │                                          │
│           ┌────────────┴───────────────┐                         │
│           │  AI Integration            │                         │
│           │  - OpenAI API              │                         │
│           │  - Google Generative AI    │                         │
│           └────────────────────────────┘                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │ SQL Queries
                              │ Python-Supabase Client
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           SUPABASE DATABASE (PostgreSQL)                         │
│        https://ahcesqtzunrmuvqjfelk.supabase.co                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ campaigns    │  │ campaign_    │  │ campaign_    │           │
│  │ table        │  │ audience     │  │ platforms    │           │
│  │              │  │ table        │  │ table        │           │
│  │ - id         │  │              │  │              │           │
│  │ - user_id    │  │ - id         │  │ - id         │           │
│  │ - name       │  │ - campaign_id│  │ - campaign_id│           │
│  │ - product    │  │ - age_min    │  │ - platform   │           │
│  │ - budget     │  │ - age_max    │  │ - budget     │           │
│  │ - status     │  │ - gender     │  │ - status     │           │
│  │ - created_at │  │ - interests  │  │ - created_at │           │
│  │ - updated_at │  │ - location   │  │              │           │
│  │              │  │ - income     │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. User Journey Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER LANDS ON APP                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────┐
        │    Check Authentication         │
        │    (AuthPage.js)                │
        └────┬──────────────────┬─────────┘
             │                  │
        Not Logged In      Logged In
             │                  │
             ↓                  ↓
        ┌─────────────┐  ┌──────────────┐
        │ Login/Sign  │  │ Dashboard    │
        │ Up Form     │  │ (Main Home)  │
        └────┬────────┘  └──┬───────────┘
             │               │
             │ POST /login   │
             ↓               │
        ┌─────────────┐      │
        │ Backend     │      │
        │ Auth Check  │      │
        └────┬────────┘      │
             │               │
         ✅ Success      ┌────┴──────────────┐
             │           │                   │
             └───────┬───┘                   │
                     ↓                       │
           ┌──────────────────┐              │
           │ Dashboard Loads  │◄─────────────┘
           │ (App.js)         │
           └────────┬─────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ↓           ↓           ↓
   ┌─────────┐ ┌─────────┐ ┌──────────┐
   │ View    │ │ Create  │ │ View     │
   │ Existing│ │ New     │ │Analytics │
   │Campaigns│ │Campaign │ │          │
   └────┬────┘ └────┬────┘ └──────────┘
        │           │
        │           ↓
        │    ┌──────────────────────┐
        │    │ Campaign Wizard Flow  │
        │    │ (CampaignWizard.js)   │
        │    └──────────┬───────────┘
        │               │
        │    ┌──────────┼──────────┐
        │    │          │          │
        │    ↓          ↓          ↓
        │  Step1:    Step2:     Step3:
        │  Product   Goal      Budget
        │  & Type    & Timeline  Amount
        │    │          │          │
        │    └──────────┼──────────┘
        │               │
        │    ┌──────────┼──────────┐
        │    │          │          │
        │    ↓          ↓          ↓
        │  Step4:    Step5:     Step6:
        │  Audience Platforms   Review
        │  (Age,    (FB, IG,    & Save
        │   Gender, Twitter,
        │   etc)    TikTok,etc)
        │    │          │          │
        │    └──────────┼──────────┘
        │               │
        │               ↓
        │    ┌──────────────────────┐
        │    │ POST /api/campaigns  │
        │    │ (Create Campaign)    │
        │    └──────────┬───────────┘
        │               │
        │               ↓
        │    ┌──────────────────────┐
        │    │ Backend Saves to DB  │
        │    │ - campaigns table    │
        │    │ - campaign_audience  │
        │    │ - campaign_platforms │
        │    └──────────┬───────────┘
        │               │
        │    ✅ Campaign Created
        │               │
        └───────┬───────┘
                │
                ↓
        ┌──────────────────────┐
        │ Display Campaign Card│
        │ (Your Campaigns)     │
        └────┬───────┬──────┬──┘
             │       │      │
             ↓       ↓      ↓
        ┌─────┐ ┌────┐ ┌──────────┐
        │View │ │Edit│ │Delete    │
        │Detls│ │    │ │Campaign  │
        └─────┘ └────┘ └──────────┘
             │              │
             ↓              ↓
        GET /api/      DELETE /api/
        campaigns/{id} campaigns/{id}
             │              │
             ↓              ↓
        Fetch from DB   Remove from DB
```

---

## 3. API Request/Response Flow

```
FRONTEND REQUEST                    BACKEND PROCESSING              DATABASE INTERACTION
─────────────────────────────────────────────────────────────────────────────────────

Create Campaign:
POST /api/campaigns
{
  name, product, type,
  goal, duration,
  budget, audience,
  platforms
}
                ─────────────────────→  app.py: @app.route('/api/campaigns', methods=['POST'])
                                        │
                                        ├─ Receive JSON payload
                                        ├─ Validate data
                                        ├─ Call db.create_campaign()
                                        └─ db.create_campaign()
                                           │
                                           ├─ INSERT INTO campaigns
                                           ├─ INSERT INTO campaign_audience
                                           ├─ INSERT INTO campaign_platforms
                                           ↓
                                        Supabase API
                                           │
                                           ↓
                                        PostgreSQL
                                           ✅ Data saved
                                           │
                ←─────────────────────── {id, status: 'draft', created_at}
Response:
{
  success: true,
  campaign: {...}
}


Get All Campaigns:
GET /api/campaigns
                ─────────────────────→  app.py: @app.route('/api/campaigns', methods=['GET'])
                                        │
                                        ├─ Call db.get_campaigns()
                                        └─ db.get_campaigns()
                                           │
                                           ├─ SELECT * FROM campaigns
                                           ├─ SELECT * FROM campaign_audience
                                           ├─ SELECT * FROM campaign_platforms
                                           ├─ JOIN tables
                                           ↓
                                        PostgreSQL
                                           ✅ Data retrieved
                                           │
                ←─────────────────────── [{campaign1}, {campaign2}, ...]
Response:
[
  {
    id, name, product, budget,
    status, audience, platforms,
    created_at
  }
]


Launch Campaign:
POST /api/campaigns/{id}/launch
                ─────────────────────→  app.py: @app.route('/api/campaigns/<id>/launch', methods=['POST'])
                                        │
                                        ├─ Get campaign by ID
                                        ├─ Validate campaign exists
                                        ├─ Call db.update_campaign_status()
                                        └─ db.update_campaign_status(id, 'active')
                                           │
                                           ├─ UPDATE campaigns
                                           │  SET status = 'active'
                                           ↓
                                        PostgreSQL
                                           ✅ Status updated
                                           │
                ←─────────────────────── {status: 'active', updated_at}
Response:
{
  success: true,
  campaign: {..., status: 'active'}
}


Delete Campaign:
DELETE /api/campaigns/{id}
                ─────────────────────→  app.py: @app.route('/api/campaigns/<id>', methods=['DELETE'])
                                        │
                                        ├─ Get campaign by ID
                                        ├─ Call db.delete_campaign()
                                        └─ db.delete_campaign(id)
                                           │
                                           ├─ DELETE FROM campaign_platforms
                                           ├─ DELETE FROM campaign_audience
                                           ├─ DELETE FROM campaigns
                                           ↓
                                        PostgreSQL
                                           ✅ Data deleted
                                           │
                ←─────────────────────── {success: true}
Response:
{
  success: true
}


Get AI Suggestions:
GET /api/campaigns/{id}/ai-suggestions
                ─────────────────────→  app.py: @app.route('/api/campaigns/<id>/ai-suggestions', methods=['GET'])
                                        │
                                        ├─ Get campaign from DB
                                        ├─ Format campaign data
                                        ├─ Call OpenAI or Google GenAI
                                        │
                                        └─ AI API Call
                                           │ (external service)
                                           │
                                        AI Response
                                           │
                                           ├─ Parse suggestions
                                           ├─ Optional: Save to DB
                                           ↓
                ←─────────────────────── {suggestions: [...]}
Response:
{
  suggestions: [
    {type, recommendation, impact}
  ]
}
```

---

## 4. Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    App.js (Root)                             │
│           (Main component, state management)                  │
└──────────────┬─────────────────────────────────────────────┘
               │
        ┌──────┼──────┬──────────┬──────────┐
        │      │      │          │          │
        ↓      ↓      ↓          ↓          ↓
    ┌───────┐┌──────┐┌────────┐┌────────┐┌────────────┐
    │Navbar ││Auth  ││Campaign││Campaign││Analytics  │
    │       ││Page  ││Wizard  ││List    ││Dashboard  │
    │       ││      ││        ││        ││           │
    │       ││      ││        ││        ││           │
    │ - Nav ││ - Log││ - Form ││ - Card ││ - Charts  │
    │ Items ││ In   ││ Fields ││ Layout ││ - Stats   │
    │ - Logo││ - S.││ - Multi││ - Stats││ - KPIs    │
    │       ││ Up  ││ Step   ││ - Actn││ - Trends  │
    └───┬───┘└──┬──┘└───┬────┘└───┬───┘└──┬────────┘
        │       │       │         │       │
        └───────┼───────┼─────────┼───────┘
                │       │         │
                └───────┼─────────┘
                        │
                        ↓
            ┌──────────────────────┐
            │  api.js Service      │
            │ (All API calls)      │
            │                      │
            │ - axios instance     │
            │ - baseURL config     │
            │ - headers setup      │
            │ - interceptors       │
            └──────────┬───────────┘
                       │
                       ↓
            ┌──────────────────────┐
            │ campaignService.js   │
            │ (Business logic)     │
            │                      │
            │ - getCampaigns()     │
            │ - createCampaign()   │
            │ - updateCampaign()   │
            │ - deleteCampaign()   │
            │ - launchCampaign()   │
            └──────────┬───────────┘
                       │
                       ↓
            ┌──────────────────────┐
            │  Backend API         │
            │  (:8000)             │
            └──────────────────────┘
```

---

## 5. Data Flow - Campaign Creation Detailed

```
USER ENTERS DATA                    FRONTEND PROCESSING              BACKEND PROCESSING
──────────────────────────────────────────────────────────────────────────────────────

Step 1-6 Form Wizard
├─ Product Name
├─ Product Type
├─ Campaign Goal
├─ Budget Amount
├─ Audience Details
│  ├─ Age Range
│  ├─ Gender
│  ├─ Interests
│  ├─ Location
│  └─ Income
└─ Platforms
   ├─ Facebook Budget
   ├─ Instagram Budget
   ├─ Twitter Budget
   └─ TikTok Budget
        │
        │ User clicks "Create Campaign"
        │
        ↓
State collected in CampaignWizard.js:
{
  productName: "Nike Shoes",
  productType: "Athletic",
  goal: "Increase Sales",
  duration: "30 days",
  totalBudget: 5000,
  audience: {
    ageMin: 18,
    ageMax: 45,
    gender: "All",
    interests: ["Sports", "Fashion"],
    location: "USA",
    income: "Mid-High"
  },
  platforms: [
    {name: "Facebook", budget: 1500},
    {name: "Instagram", budget: 1500},
    {name: "Twitter", budget: 1000},
    {name: "TikTok", budget: 1000}
  ]
}
        │
        │ Call: campaignService.createCampaign(data)
        │
        ↓
POST http://localhost:8000/api/campaigns
Headers:
  Content-Type: application/json
  Authorization: Bearer {token}
Body: {campaign data}
        │
        ↓ Network Request
        │
──────────────────────────────────────────────────────────────────
                     BACKEND RECEIVES
──────────────────────────────────────────────────────────────────
        │
        ↓
app.py: @app.route('/api/campaigns', methods=['POST'])
        │
        ├─ Parse JSON request body
        ├─ Validate schema
        │  ├─ Check required fields
        │  ├─ Check data types
        │  └─ Check field values
        │
        ├─ Extract data:
        │  ├─ campaign_data = {
        │  │    user_id: 123,
        │  │    name: "Nike Shoes Campaign",
        │  │    product_name: "Nike Shoes",
        │  │    product_type: "Athletic",
        │  │    goal: "Increase Sales",
        │  │    duration: 30,
        │  │    budget: 5000,
        │  │    status: "draft",
        │  │  }
        │  │
        │  ├─ audience_data = {campaign_id, age_min, age_max, ...}
        │  └─ platforms_data = [{campaign_id, platform, budget}, ...]
        │
        ├─ Call database.create_campaign(campaign_data, audience_data, platforms_data)
        │
        └─ database.py Function Execution:
           │
           ├─ supabase.table('campaigns').insert({...})
           │  │
           │  ↓ SQL Generated:
           │  INSERT INTO campaigns (user_id, name, product_name, ...)
           │  VALUES (123, 'Nike...', 'Nike...', ...)
           │  RETURNING id, created_at, *
           │
           │  ✅ Returns: {id: 456, created_at: '2024-01-30T...'}
           │
           ├─ campaign_id = 456
           │
           ├─ supabase.table('campaign_audience').insert({...})
           │  │
           │  ↓ SQL Generated:
           │  INSERT INTO campaign_audience (campaign_id, age_min, age_max, ...)
           │  VALUES (456, 18, 45, ...)
           │  RETURNING *
           │
           │  ✅ Returns: {id: 789, campaign_id: 456, ...}
           │
           ├─ supabase.table('campaign_platforms').insert([...])
           │  │
           │  ↓ SQL Generated:
           │  INSERT INTO campaign_platforms (campaign_id, platform, budget, ...)
           │  VALUES (456, 'Facebook', 1500, ...),
           │         (456, 'Instagram', 1500, ...),
           │         (456, 'Twitter', 1000, ...),
           │         (456, 'TikTok', 1000, ...)
           │  RETURNING *
           │
           │  ✅ Returns: [{id: 111, campaign_id: 456, ...}, ...]
           │
           └─ Return success response
              │
              ↓ Response JSON:
              {
                success: true,
                campaign: {
                  id: 456,
                  name: "Nike Shoes Campaign",
                  status: "draft",
                  budget: 5000,
                  audience: {...},
                  platforms: [...],
                  created_at: "2024-01-30T10:30:00Z"
                }
              }
              
              ↓ HTTP 201 Created
```

---

## 6. AI Suggestions Flow

```
┌────────────────────────────────────┐
│ User Clicks "Get AI Suggestions"   │
│ (AIRecommendations component)      │
└────────────┬───────────────────────┘
             │
             ↓
  campaignService.getAISuggestions(campaignId)
             │
             ↓
  GET /api/campaigns/{id}/ai-suggestions
             │
             ↓
┌────────────────────────────────────┐
│ Backend Processing                 │
│ app.py: ai_suggestions route       │
└────────┬───────────────────────────┘
         │
         ├─ Get campaign from database
         │
         ├─ Get audience data
         │
         ├─ Format context for AI:
         │  ├─ Campaign goals
         │  ├─ Budget constraints
         │  ├─ Target audience
         │  └─ Selected platforms
         │
         ├─ Check .env for API keys:
         │  ├─ OPENAI_API_KEY
         │  └─ GOOGLE_GENAI_API_KEY
         │
         ├─ Call AI API (OpenAI or Google)
         │  │
         │  └─→ External API Request
         │      │
         │      Prompt Example:
         │      "Given a campaign with:
         │       - Budget: $5000
         │       - Audience: 18-45, Sports/Fashion
         │       - Platforms: Facebook, Instagram, Twitter, TikTok
         │       Suggest:
         │       1. Budget allocation per platform
         │       2. Target audience refinements
         │       3. Ad creative recommendations
         │       4. Posting schedule"
         │
         │      ↓ AI Response
         │      {
         │        suggestions: [
         │          {
         │            type: "budget_allocation",
         │            recommendation: "Allocate 35% to Instagram...",
         │            impact: "High engagement expected"
         │          },
         │          {
         │            type: "audience_refinement",
         │            recommendation: "Focus on ages 25-35...",
         │            impact: "Better ROI"
         │          },
         │          ...
         │        ]
         │      }
         │
         ├─ Parse AI response
         │
         ├─ Optional: Save suggestions to database
         │  └─ INSERT INTO campaign_suggestions
         │
         └─ Return to frontend
            │
            ↓
Response JSON:
{
  success: true,
  suggestions: [
    {
      type: "budget_allocation",
      recommendation: "...",
      impact: "..."
    },
    {
      type: "content_strategy",
      recommendation: "...",
      impact: "..."
    },
    ...
  ]
}
            │
            ↓
┌────────────────────────────────────┐
│ Frontend: AIRecommendations.js     │
│ Display suggestions to user        │
│ - Show recommendation cards        │
│ - Allow implementation options     │
│ - Track which were applied         │
└────────────────────────────────────┘
```

---

## 7. Database Schema Relationships

```
campaigns (Parent)
├─ id (Primary Key)
├─ user_id
├─ name
├─ product_name
├─ product_type
├─ goal
├─ duration
├─ budget (total)
├─ status (draft/active/completed)
├─ created_at
└─ updated_at
   │
   ├──────────────────────┬──────────────────────┐
   │                      │                      │
   ↓                      ↓                      ↓

campaign_audience      campaign_platforms    campaign_suggestions
(One-to-One)          (One-to-Many)          (One-to-Many)

├─ id                 ├─ id                   ├─ id
├─ campaign_id (FK)   ├─ campaign_id (FK)     ├─ campaign_id (FK)
├─ age_min            ├─ platform_name        ├─ suggestion_type
├─ age_max            ├─ allocated_budget     ├─ recommendation
├─ gender             ├─ status               ├─ impact_score
├─ interests[]        ├─ created_at           ├─ applied (boolean)
├─ location           └─ updated_at           ├─ created_at
├─ income                                     └─ updated_at
├─ created_at
└─ updated_at
```

---

## 8. Error Handling Flow

```
USER ACTION
    │
    ↓
TRY:
├─ Make API request
│  
CATCH:
├─ Network Error
│  ├─ No internet connection
│  ├─ Show toast: "Unable to connect to server"
│  └─ Retry button
│
├─ Backend Error (500)
│  ├─ Database connection failed
│  ├─ API error
│  ├─ Log error details
│  ├─ Show toast: "Server error occurred"
│  └─ Retry button
│
├─ Validation Error (400)
│  ├─ Invalid input
│  ├─ Missing required fields
│  ├─ Parse error details
│  ├─ Show specific field errors
│  └─ User corrects & retries
│
├─ Auth Error (401/403)
│  ├─ Token expired
│  ├─ Unauthorized access
│  ├─ Clear session
│  ├─ Redirect to login
│  └─ Show message: "Please login again"
│
└─ Unknown Error
   ├─ Log full error
   ├─ Show generic message
   └─ Contact support option
```

---

## 9. State Management Flow

```
┌──────────────────────────────┐
│      React State (App.js)     │
│                              │
│ ├─ campaigns[]               │
│ ├─ selectedCampaign          │
│ ├─ isLoading                 │
│ ├─ error                     │
│ ├─ user                      │
│ ├─ suggestions[]             │
│ ├─ isLoadingSuggestions      │
│ └─ filters                   │
└───────────┬──────────────────┘
            │
    ┌───────┼───────┐
    │       │       │
    ↓       ↓       ↓
Update  Fetch   Filter
Campaign Data   Results
    │       │       │
    ├───────┴───────┤
    │               │
    ↓               ↓
POST Request    GET Request
    │               │
    ├───────┬───────┤
    │       │
    ↓       ↓
Supabase Database
    │
    ↓
New State
    │
    ↓
Re-render Components
```

---

## 10. Complete Feature Lifecycle

```
FEATURE REQUEST
    │
    ├─ User creates campaign
    │  ├─ Frontend: CampaignWizard collects data
    │  ├─ State: Stores in local state
    │  ├─ Submit: POST /api/campaigns
    │  ├─ Backend: Validates & saves
    │  ├─ Database: Inserts records
    │  ├─ Response: Returns campaign with ID
    │  └─ UI: Shows campaign card
    │
    ├─ User views campaigns
    │  ├─ Frontend: App component mounts
    │  ├─ Fetch: GET /api/campaigns
    │  ├─ Backend: Queries database
    │  ├─ Join: Combines with audience & platforms
    │  ├─ Response: Returns full campaign data
    │  └─ Display: Maps to campaign cards
    │
    ├─ User launches campaign
    │  ├─ Frontend: Click launch button
    │  ├─ Request: POST /api/campaigns/{id}/launch
    │  ├─ Backend: Updates status to 'active'
    │  ├─ Database: UPDATE campaigns SET status='active'
    │  ├─ Response: Returns updated campaign
    │  └─ UI: Updates status display
    │
    ├─ User gets AI suggestions
    │  ├─ Frontend: Click suggestions button
    │  ├─ Request: GET /api/campaigns/{id}/ai-suggestions
    │  ├─ Backend: Retrieves campaign data
    │  ├─ Call AI: Format & send to OpenAI/Google
    │  ├─ Parse Response: Extract recommendations
    │  ├─ Format: Prepare for frontend
    │  └─ Display: Show suggestion cards
    │
    └─ User deletes campaign
       ├─ Frontend: Click delete button
       ├─ Confirm: Show delete dialog
       ├─ Request: DELETE /api/campaigns/{id}
       ├─ Backend: Remove all related data
       ├─ Database: DELETE from all related tables
       ├─ Response: Confirm deletion
       └─ UI: Remove from list
```

---

## 11. Tech Stack Summary

```
┌────────────────────────────────────────────┐
│            FRONTEND LAYER                  │
│            React @ localhost:3000          │
├────────────────────────────────────────────┤
│ - React Hooks (useState, useEffect)        │
│ - axios (HTTP client)                      │
│ - React Router (Navigation)                │
│ - CSS (Styling)                            │
│ - Components (Presentational)              │
│ - Services (API communication)             │
└────────────────────────────────────────────┘
         ↕ HTTP REST API (JSON)
┌────────────────────────────────────────────┐
│            BACKEND LAYER                   │
│           Flask @ localhost:8000           │
├────────────────────────────────────────────┤
│ - Flask (Web framework)                    │
│ - Flask-CORS (Cross-origin support)        │
│ - python-dotenv (Configuration)            │
│ - supabase-py (Database client)            │
│ - openai (AI API)                          │
│ - google-generativeai (AI API)             │
│ - Routes (API endpoints)                   │
│ - Database functions (CRUD)                │
└────────────────────────────────────────────┘
         ↕ SQL Queries
┌────────────────────────────────────────────┐
│           DATA LAYER                       │
│     Supabase (PostgreSQL) Cloud            │
├────────────────────────────────────────────┤
│ - campaigns table                          │
│ - campaign_audience table                  │
│ - campaign_platforms table                 │
│ - campaign_suggestions table (optional)    │
│ - Real-time capabilities                   │
│ - Authentication support                   │
└────────────────────────────────────────────┘
         ↕ External APIs
┌────────────────────────────────────────────┐
│           AI SERVICES                      │
├────────────────────────────────────────────┤
│ - OpenAI GPT (Recommendations)             │
│ - Google Generative AI (Alternative)       │
└────────────────────────────────────────────┘
```

---

## 12. File Structure & Responsibilities

```
AI-DIGITAL-MARKETING/
│
├── backend/
│   ├── app.py ......................... Main Flask application & routes
│   │   ├─ Flask app initialization
│   │   ├─ CORS configuration
│   │   ├─ Route definitions
│   │   │  ├─ POST /api/campaigns (create)
│   │   │  ├─ GET /api/campaigns (list)
│   │   │  ├─ GET /api/campaigns/{id} (get one)
│   │   │  ├─ PUT /api/campaigns/{id} (update)
│   │   │  ├─ DELETE /api/campaigns/{id} (delete)
│   │   │  ├─ POST /api/campaigns/{id}/launch
│   │   │  ├─ GET /api/campaigns/{id}/ai-suggestions
│   │   │  └─ GET /api/health (health check)
│   │   └─ Error handlers
│   │
│   ├── database.py ................... Database operations
│   │   ├─ Supabase client initialization
│   │   ├─ create_campaign(data)
│   │   ├─ get_campaigns()
│   │   ├─ get_campaign_by_id(id)
│   │   ├─ update_campaign(id, data)
│   │   ├─ delete_campaign(id)
│   │   ├─ launch_campaign(id)
│   │   └─ Helper functions
│   │
│   ├── requirements.txt .............. Python dependencies
│   │   ├─ Flask
│   │   ├─ python-dotenv
│   │   ├─ supabase
│   │   ├─ openai
│   │   ├─ google-generativeai
│   │   └─ flask-cors
│   │
│   ├── schema.sql .................... Database schema definition
│   │   ├─ campaigns table
│   │   ├─ campaign_audience table
│   │   ├─ campaign_platforms table
│   │   └─ Indexes & relationships
│   │
│   ├── .env .......................... Environment variables
│   │   ├─ SUPABASE_URL
│   │   ├─ SUPABASE_KEY
│   │   ├─ OPENAI_API_KEY
│   │   └─ GOOGLE_GENAI_API_KEY
│   │
│   └── marketing_campaign_dataset.csv  Sample data
│
└── frontend/
    ├── package.json ................. NPM configuration & dependencies
    │   ├─ React
    │   ├─ axios
    │   ├─ react-router-dom
    │   └─ build scripts
    │
    ├── src/
    │   ├── App.js .................... Root component & state management
    │   │   ├─ campaigns state
    │   │   ├─ selectedCampaign state
    │   │   ├─ isLoading state
    │   │   ├─ error handling
    │   │   └─ renders main layout
    │   │
    │   ├── index.js .................. Entry point
    │   │   └─ Renders App to DOM
    │   │
    │   ├── App.css ................... Main styling
    │   │
    │   ├── components/
    │   │   ├── Navbar.js ............. Navigation component
    │   │   │
    │   │   ├── AuthPage.js ........... Login/Signup page
    │   │   │
    │   │   ├── CampaignWizard.js ..... Multi-step form
    │   │   │   ├─ Step 1: Product info
    │   │   │   ├─ Step 2: Goal & Timeline
    │   │   │   ├─ Step 3: Budget
    │   │   │   ├─ Step 4: Audience
    │   │   │   ├─ Step 5: Platforms
    │   │   │   └─ Step 6: Review & Submit
    │   │   │
    │   │   ├── AIRecommendations.js .. AI suggestions display
    │   │   │   ├─ Fetch suggestions
    │   │   │   ├─ Display cards
    │   │   │   └─ Handle implementation
    │   │   │
    │   │   ├── AnalyticsChart.js ..... Charts & graphs
    │   │   │   ├─ Campaign performance
    │   │   │   ├─ Metrics visualization
    │   │   │   └─ Trend analysis
    │   │   │
    │   │   ├── StatsCards.js ......... KPI display
    │   │   │   ├─ Campaign stats
    │   │   │   ├─ Budget info
    │   │   │   └─ Status info
    │   │   │
    │   │   └── CSS files ............ Component styling
    │   │
    │   ├── services/
    │   │   ├── api.js ................ Axios configuration
    │   │   │   ├─ baseURL setup
    │   │   │   ├─ Headers config
    │   │   │   └─ Interceptors
    │   │   │
    │   │   └── campaignService.js .... Business logic
    │   │       ├─ getCampaigns()
    │   │       ├─ createCampaign()
    │   │       ├─ updateCampaign()
    │   │       ├─ deleteCampaign()
    │   │       ├─ launchCampaign()
    │   │       ├─ getAISuggestions()
    │   │       └─ getAnalytics()
    │   │
    │   └── styles/
    │       └── CSS files
    │
    └── public/
        ├── index.html ............... HTML entry point
        ├── manifest.json ............ PWA manifest
        └── robots.txt ............... SEO configuration
```

---

## Summary

This is a **3-tier web application** with:
- **Frontend**: React UI with multi-step campaign creation wizard
- **Backend**: Flask API server handling business logic & database operations
- **Database**: Supabase PostgreSQL with campaigns, audience, and platforms tables
- **AI Integration**: OpenAI/Google GenAI for suggestions & recommendations
- **Data Flow**: Unidirectional from UI → Backend → Database → Response → UI

The application allows users to create, manage, and optimize digital marketing campaigns with AI-powered recommendations.
