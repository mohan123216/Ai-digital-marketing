# Quick Start Guide - Real Data Integration

## Step 1: Set Up Supabase Database (One-Time)

### 1.1 Get Supabase Credentials
- Your `.env` file already has:
  - `SUPABASE_URL=https://ahcesqtzunrmuvqjfelk.supabase.co`
  - `SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 1.2 Create Database Tables
1. Go to: https://supabase.com/dashboard
2. Sign in with your credentials
3. Open your project
4. Click "SQL Editor" in the left sidebar
5. Click "+ New Query"
6. Copy ALL content from `backend/schema.sql`
7. Paste into SQL Editor
8. Click "Run" button
9. Wait for success message

✅ Database is now ready!

---

## Step 2: Install Backend Dependencies

Open terminal/PowerShell:

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- Flask-CORS (cross-origin requests)
- python-dotenv (environment variables)
- supabase (database client)
- openai & google-generativeai (AI APIs)

---

## Step 3: Start Backend Server

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:8000
 * Press CTRL+C to quit
```

✅ Backend is running!

---

## Step 4: Start Frontend Server

Open a NEW terminal/PowerShell window:

```bash
cd frontend
npm start
```

Frontend opens automatically at `http://localhost:3000`

✅ Frontend is running!

---

## Step 5: Test the Application

### Test 1: Create a Campaign
1. Go to http://localhost:3000
2. Click "Create New Campaign"
3. Fill in Product Name & Type
4. Go through all steps (Goal → Budget → Audience → Platforms → Duration)
5. Click "Create Campaign"
6. ✅ Campaign saved to database!

### Test 2: View Campaigns
- Scroll down to "Your Campaigns" section
- See your newly created campaign displayed
- ✅ Real data from database!

### Test 3: Launch Campaign
1. Find your campaign card
2. Click "Launch Campaign" button
3. See status change from "draft" to "active"
4. ✅ Campaign launched!

### Test 4: Delete Campaign
1. Click "Delete" button on a campaign
2. Campaign removed from database and UI
3. ✅ Works perfectly!

---

## Verify Everything Works

### Check Backend Health
```bash
curl http://localhost:8000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-30T..."
}
```

### Check Supabase Database
1. Go to Supabase Dashboard
2. Click "Table Editor"
3. You should see `campaigns` table with your data
4. Open `campaign_audience` - see audience data
5. Open `campaign_platforms` - see platform data
6. ✅ All data stored correctly!

---

## Architecture Overview

```
┌─────────────────┐
│   React UI      │
│  (Frontend)     │
└────────┬────────┘
         │ HTTP API Calls
         ↓
┌─────────────────┐
│  Flask Backend  │
│  (app.py)       │
└────────┬────────┘
         │ SQL Queries
         ↓
┌─────────────────┐
│   Supabase      │
│   Database      │
│ (PostgreSQL)    │
└─────────────────┘
```

---

## API Endpoints Available

### Campaign Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/campaigns` | POST | Create campaign |
| `/api/campaigns` | GET | Get all campaigns |
| `/api/campaigns/{id}` | GET | Get campaign details |
| `/api/campaigns/{id}` | PUT | Update campaign |
| `/api/campaigns/{id}` | DELETE | Delete campaign |
| `/api/campaigns/{id}/launch` | POST | Launch campaign |
| `/api/health` | GET | Health check |

---

## Data Stored in Database

### Campaigns Table
- Product name & type
- Campaign goal
- Budget
- Duration
- Status (draft/active/completed)
- Created & updated timestamps

### Campaign Audience Table
- Age range (min/max)
- Gender preferences
- Selected interests
- Location
- Income level

### Campaign Platforms Table
- Platform name (Facebook, Instagram, etc.)
- Allocated budget per platform
- Status

---

## Common Tasks

### View All Your Campaigns
1. Check "Your Campaigns" section on homepage
2. All campaigns from database displayed here

### Track Campaign Status
- **draft** = Created but not launched yet
- **active** = Currently running
- Click "Launch Campaign" to change from draft to active

### Modify Campaign Settings
- Would need Edit endpoint (can be added)
- Currently you can delete and recreate

### Check Database Directly
1. Supabase Dashboard → Table Editor
2. Select `campaigns` table
3. Click on any row to see full details

---

## If Something Doesn't Work

### Backend won't start
```bash
# Check if port 8000 is in use
# Solution: Modify app.py line at bottom
if __name__ == '__main__':
    app.run(debug=True, port=8001)  # Change 8000 to 8001
```

### Database connection error
```
Check in .env:
- SUPABASE_URL is correct
- SUPABASE_KEY is correct
- No extra spaces or quotes
```

### Frontend can't reach backend
```bash
# Make sure both servers running:
# Terminal 1: python app.py (port 8000)
# Terminal 2: npm start (port 3000)
```

### No campaigns showing up
```
Check:
1. Backend running? curl localhost:8000/api/health
2. Database tables exist? Check Supabase SQL Editor
3. Browser console for errors? F12 → Console tab
```

---

## Next Steps

### After Basic Testing Works:

1. **Add AI Suggestions**
   - Backend endpoint: `/api/campaigns/<id>/ai-suggestions`
   - Store recommendations in database
   - Display in campaign cards

2. **Track Campaign Performance**
   - Record daily metrics (impressions, clicks, conversions)
   - Display analytics dashboard
   - Compare against benchmarks

3. **Edit Campaigns**
   - Add PUT endpoint fully implemented
   - Update audience and platforms
   - Track version history

4. **User Authentication**
   - Add login/signup
   - Associate campaigns with users
   - Private campaigns per user

5. **Advanced Analytics**
   - ROI calculations
   - Performance predictions
   - Budget optimization

---

## Files Overview

### Backend Files
```
backend/
├── app.py                    # Main API (REST endpoints)
├── database.py               # Database functions (already updated)
├── schema.sql                # Database schema
├── requirements.txt          # Python dependencies
└── .env                      # Supabase credentials
```

### Frontend Files
```
frontend/
├── src/
│   ├── services/
│   │   └── api.js           # API calls (updated)
│   └── components/
│       └── CampaignWizard.js # Main component (updated)
└── package.json
```

### Documentation
```
├── SETUP_GUIDE.md            # Detailed setup instructions
├── REAL_DATA_INTEGRATION.md  # Complete technical docs
└── QUICK_START.md            # This file
```

---

## Success Checklist ✅

- [ ] SQL schema executed in Supabase
- [ ] `backend/requirements.txt` installed
- [ ] Backend running on localhost:8000
- [ ] Frontend running on localhost:3000
- [ ] Can create new campaign
- [ ] Campaign appears in "Your Campaigns"
- [ ] Can see campaign data in Supabase
- [ ] Can launch campaign
- [ ] Can delete campaign
- [ ] API health check works

If all checked, you're ready to use the real data system! 🎉

---

## Support

For issues:
1. Check console logs (F12 in browser)
2. Check backend terminal for errors
3. Verify Supabase connection
4. Check `.env` file credentials
5. Review REAL_DATA_INTEGRATION.md for detailed docs

Good luck! 🚀
