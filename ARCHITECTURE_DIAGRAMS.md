# System Architecture & Data Flow Diagrams

## 1. Overall System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CampaignWizard.js                                          │  │
│  │ ├─ Product Input Form                                      │  │
│  │ ├─ Campaign Setup Steps                                    │  │
│  │ ├─ Campaign Card Display                                   │  │
│  │ └─ Campaign Actions                                        │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ api.js (API Client)                                        │  │
│  │ ├─ createCampaign()                                        │  │
│  │ ├─ getAllCampaigns()                                       │  │
│  │ ├─ getCampaignById()                                       │  │
│  │ ├─ updateCampaign()                                        │  │
│  │ ├─ deleteCampaign()                                        │  │
│  │ ├─ launchCampaign()                                        │  │
│  │ └─ getAISuggestions()                                      │  │
│  └────────────────────┬───────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                          │ HTTP API Calls
                          │ (JSON)
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask)                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ app.py - REST API Server                                   │  │
│  │ ├─ POST   /api/campaigns                                   │  │
│  │ ├─ GET    /api/campaigns                                   │  │
│  │ ├─ GET    /api/campaigns/<id>                              │  │
│  │ ├─ PUT    /api/campaigns/<id>                              │  │
│  │ ├─ DELETE /api/campaigns/<id>                              │  │
│  │ ├─ POST   /api/campaigns/<id>/launch                       │  │
│  │ └─ GET    /api/health                                      │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ database.py - Database Functions                           │  │
│  │ ├─ Supabase Client                                         │  │
│  │ ├─ Query Builders                                          │  │
│  │ └─ Data Processing                                         │  │
│  └────────────────────┬───────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                          │ SQL Queries
                          │ 
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DATABASE (Supabase)                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ PostgreSQL Tables                                          │  │
│  │ ├─ campaigns                                               │  │
│  │ ├─ campaign_audience                                       │  │
│  │ ├─ campaign_platforms                                      │  │
│  │ ├─ ai_recommendations                                      │  │
│  │ ├─ campaign_predictions                                    │  │
│  │ ├─ campaign_performance                                    │  │
│  │ ├─ campaign_benchmark_comparison                           │  │
│  │ └─ ad_benchmarks                                           │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Campaign Creation Flow

```
┌─────────────────────┐
│  User Opens App     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ useEffect runs                          │
│ fetchCampaigns() called                 │
│ GET /api/campaigns                      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Supabase queries all campaigns          │
│ Returns array of campaigns              │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Campaigns displayed in grid             │
│ Empty if first time                     │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ User clicks "Create Campaign"           │
│ Wizard form opens (showWizard = true)   │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Step 1: Product Information             │
│ - Enter product name                    │
│ - Select product type                   │
└──────────┬──────────────────────────────┘
           │
           ▼ (Continue)
┌─────────────────────────────────────────┐
│ Steps 2-6: Campaign Setup               │
│ - Goal selection                        │
│ - Budget input                          │
│ - Audience targeting                    │
│ - Platform selection                    │
│ - Duration setting                      │
└──────────┬──────────────────────────────┘
           │
           ▼ (Create Campaign)
┌─────────────────────────────────────────┐
│ launchCampaign() function called        │
│ Prepares payload:                       │
│ {                                       │
│   productName: "...",                   │
│   productType: "...",                   │
│   goal: "...",                          │
│   budget: 5000,                         │
│   duration: 30,                         │
│   audience: {...},                      │
│   platforms: [...]                      │
│ }                                       │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ campaignAPI.createCampaign(payload)     │
│ POST /api/campaigns                     │
│ setLoading(true)                        │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Backend receives request                │
│ Validates all fields                    │
│ ✓ productName present?                  │
│ ✓ budget is numeric?                    │
│ ✓ platforms is array?                   │
│ ✓ audience data valid?                  │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ If validation fails:                    │
│ return error response (400)             │
│                                         │
│ If validation passes:                   │
│ Continue to database insertion          │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Database Transaction:                   │
│                                         │
│ 1. INSERT campaigns                     │
│    └─ Returns campaign_id               │
│                                         │
│ 2. INSERT campaign_audience             │
│    └─ Links to campaign_id              │
│                                         │
│ 3. INSERT campaign_platforms (loop)     │
│    └─ One per platform selected         │
│       Links to campaign_id              │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Backend returns response:               │
│ {                                       │
│   "success": true,                      │
│   "campaign_id": 123,                   │
│   "campaign": {...}                     │
│ }                                       │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Frontend receives response              │
│ - Show success alert                    │
│ - Reset form to initial state           │
│ - Reset step to 1                       │
│ - Hide wizard (showWizard = false)      │
│ - setLoading(false)                     │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Call fetchCampaigns() again             │
│ GET /api/campaigns                      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Backend returns updated list            │
│ (including newly created campaign)      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Frontend updates state:                 │
│ setCampaigns(result.campaigns)          │
│                                         │
│ UI re-renders with new campaign         │
│ displayed in campaign grid              │
└─────────────────────────────────────────┘
```

---

## 3. Campaign Display Flow

```
┌────────────────────────────────────┐
│ User Sees "Your Campaigns" Section │
└──────────────┬─────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Check campaigns array                   │
│ if (campaigns.length === 0)             │
│   Show empty state                      │
│ else                                    │
│   Show campaign grid                    │
└──────────┬──────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ For each campaign in campaigns array:        │
│                                              │
│ Campaign Card:                               │
│ ┌──────────────────────────────────────────┐ │
│ │ Header                                   │ │
│ │ - product_name (from DB)                 │ │
│ │ - product_type (from DB)                 │ │
│ │ - created_at date (from DB)              │ │
│ ├──────────────────────────────────────────┤ │
│ │ Details                                  │ │
│ │ - Goal: campaign.goal                    │ │
│ │ - Budget: $campaign.budget               │ │
│ │ - Duration: campaign.duration days       │ │
│ │ - Platforms: [list from DB]              │ │
│ │ - Audience: interests, age range         │ │
│ │ - Status: campaign.status                │ │
│ ├──────────────────────────────────────────┤ │
│ │ Actions                                  │ │
│ │ - [Get AI Suggestions]                   │ │
│ │ - [Launch Campaign]                      │ │
│ │ - [Delete]                               │ │
│ └──────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ User clicks "Launch Campaign"                │
│                                              │
│ launchCampaign(campaign.id) called           │
│ campaignAPI.launchCampaign(id)               │
│ POST /api/campaigns/{id}/launch              │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ Backend:                                     │
│ UPDATE campaigns                             │
│ SET status = 'active'                        │
│ SET launched_at = now()                      │
│ SET updated_at = now()                       │
│ WHERE id = {id}                              │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ Database updates campaign record             │
│ Status changed: draft → active               │
│ launched_at timestamp recorded               │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ Backend returns success response             │
│ Frontend shows alert: "Campaign Launched!"   │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ Frontend calls fetchCampaigns() again        │
│ Campaign card updates with new status        │
│ "Launch Campaign" button disabled            │
│ Shows "Active" instead                       │
└──────────────────────────────────────────────┘
```

---

## 4. Database Schema Relationships

```
campaigns (Main Table)
│
│ 1-to-1 relationship
├─→ campaign_audience
│   ├─ age_min, age_max
│   ├─ genders[]
│   ├─ interests[]
│   ├─ location
│   └─ income_level
│
│ 1-to-many relationship
├─→ campaign_platforms
│   ├─ platform (e.g., "Facebook")
│   ├─ allocated_budget
│   └─ status
│
│ 1-to-many relationship
├─→ ai_recommendations
│   ├─ title
│   ├─ description
│   ├─ confidence_score
│   └─ impact_level
│
│ 1-to-1 relationship
├─→ campaign_predictions
│   ├─ estimated_reach
│   ├─ estimated_clicks
│   ├─ estimated_ctr
│   └─ estimated_roas
│
│ 1-to-many relationship
├─→ campaign_performance
│   ├─ date
│   ├─ platform
│   ├─ impressions
│   ├─ clicks
│   ├─ conversions
│   └─ revenue
│
└─→ campaign_benchmark_comparison
    ├─ platform
    ├─ metric
    ├─ campaign_value
    └─ benchmark_value

Reference Tables:
└─→ ad_benchmarks
    ├─ platform
    ├─ industry
    ├─ metric
    ├─ value
    └─ source
```

---

## 5. API Request-Response Flow

```
╔════════════════════════════════════════════════════════════════════╗
║                    CREATE CAMPAIGN REQUEST                         ║
╚════════════════════════════════════════════════════════════════════╝

POST /api/campaigns
Content-Type: application/json

{
  "productName": "Nike Air Max",
  "productType": "Shoes",
  "goal": "Sales Conversion",
  "budget": 5000,
  "duration": 30,
  "audience": {
    "age": {"min": 18, "max": 45},
    "gender": ["male", "female"],
    "interests": ["Sports", "Fashion"],
    "location": "United States",
    "income": "all"
  },
  "platforms": ["Facebook", "Instagram"]
}

                    ↓ (HTTP)

        ┌─────────────────────────┐
        │   Backend Processing    │
        ├─────────────────────────┤
        │ 1. Validate input       │
        │ 2. Insert campaigns     │
        │ 3. Insert audience      │
        │ 4. Insert platforms     │
        │ 5. Build response       │
        └─────────────────────────┘

                    ↓ (HTTP)

╔════════════════════════════════════════════════════════════════════╗
║                   CREATE CAMPAIGN RESPONSE                         ║
╚════════════════════════════════════════════════════════════════════╝

HTTP 201 Created

{
  "success": true,
  "campaign_id": 123,
  "message": "Campaign created successfully",
  "campaign": {
    "id": 123,
    "product_name": "Nike Air Max",
    "product_type": "Shoes",
    "goal": "Sales Conversion",
    "budget": 5000,
    "duration": 30,
    "status": "draft",
    "created_at": "2024-01-30T10:00:00",
    "updated_at": "2024-01-30T10:00:00",
    "launched_at": null
  }
}

                    ↓ (Frontend)

        ┌─────────────────────────┐
        │   Frontend Update       │
        ├─────────────────────────┤
        │ 1. Check success flag   │
        │ 2. Show alert           │
        │ 3. Reset form           │
        │ 4. Fetch campaigns      │
        │ 5. Update display       │
        └─────────────────────────┘
```

---

## 6. State Management

```
CampaignWizard Component State:

┌───────────────────────────────────────┐
│ showWizard (boolean)                  │
│ true  = Show creation form            │
│ false = Show campaign list            │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ currentStep (number: 1-6)             │
│ 1 = Product Info                      │
│ 2 = Goal Selection                    │
│ 3 = Budget                            │
│ 4 = Audience                          │
│ 5 = Platforms                         │
│ 6 = Duration                          │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ productName (string)                  │
│ User input for product name           │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ productType (string)                  │
│ User selection for product type       │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ campaigns (array)                     │
│ [                                     │
│   {id, product_name, product_type,    │
│    goal, budget, duration, status,    │
│    created_at, audience, platforms},  │
│   {...}                               │
│ ]                                     │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ campaignData (object)                 │
│ {                                     │
│   goal, budget, duration,             │
│   audience: {                         │
│     age, gender, interests,           │
│     location, income                  │
│   },                                  │
│   platforms: []                       │
│ }                                     │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ loading (boolean)                     │
│ true  = API call in progress          │
│ false = Ready                         │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ selectedCampaign (object)             │
│ Current campaign being edited         │
└───────────────────────────────────────┘
```

---

## 7. Error Handling Flow

```
User Action
    │
    ▼
Try Block
    │
    ├─ Validation Check
    │   │
    │   ├─ Passed? Continue
    │   └─ Failed? Throw Error
    │
    └─ API Call
        │
        ├─ Success? Process Response
        └─ Failed? Throw Error

                ▼

        Error Caught
            │
            ├─ Catch Block
            │   │
            │   ├─ Log error
            │   ├─ Extract message
            │   ├─ Show alert to user
            │   └─ Don't update UI
            │
            └─ Finally Block
                │
                ├─ setLoading(false)
                └─ Clean up state
```

---

## 8. Component Lifecycle

```
Component Mounts
    │
    ├─ States initialized
    ├─ useEffect triggered
    │   │
    │   └─ fetchCampaigns()
    │       │
    │       ├─ setLoading(true)
    │       ├─ campaignAPI.getAllCampaigns()
    │       ├─ setCampaigns(result)
    │       └─ setLoading(false)
    │
    └─ Component Rendered
        │
        ├─ If showWizard = true
        │   └─ Show wizard form
        └─ If showWizard = false
            └─ Show campaign cards

User Interaction
    │
    ├─ Creates campaign
    │   └─ launchCampaign()
    │       └─ fetchCampaigns()
    │           └─ Re-render with new data
    │
    └─ Launches campaign
        └─ launchCampaign(id)
            └─ fetchCampaigns()
                └─ Re-render with updated status
```

---

This visual representation should help understand:
- Overall system architecture
- Data flow for campaign creation
- Database relationships
- API request-response patterns
- State management
- Error handling
- Component lifecycle

All working together to create a seamless real-data campaign management system!
