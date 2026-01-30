# Database Setup Guide

## Prerequisites
- Supabase Account (https://supabase.com)
- Python 3.8+
- pip (Python package manager)

## Step 1: Create Supabase Project
1. Go to https://supabase.com and create an account
2. Create a new project
3. Go to Project Settings -> API to find your:
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (Service Role Key or Anon Key)

## Step 2: Set Environment Variables
Create/Update `.env` file in the `backend` folder:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key
```

## Step 3: Run SQL Migration
1. Go to Supabase Dashboard
2. Click on "SQL Editor" in the sidebar
3. Click "+ New Query"
4. Copy all content from `schema.sql` file
5. Paste into the SQL Editor
6. Click "Run" button

This will create all necessary tables and indexes.

## Step 4: Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

## Step 5: Run Backend Server
```bash
python app.py
```

The backend will start on `http://localhost:8000`

## Step 6: Verify Database Connection
Test the health endpoint:
```bash
curl http://localhost:8000/api/health
```

You should receive:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-30T..."
}
```

## Database Schema

### campaigns
- Stores main campaign information
- Fields: product_name, product_type, goal, budget, duration, status, timestamps

### campaign_audience
- Stores audience targeting information
- Fields: age_min, age_max, genders, interests, location, income_level

### campaign_platforms
- Stores platforms selected for the campaign
- Fields: platform, allocated_budget, status

### ai_recommendations
- Stores AI-generated recommendations
- Fields: title, description, confidence_score, impact_level

### campaign_predictions
- Stores predicted campaign performance
- Fields: estimated_reach, estimated_clicks, estimated_ctr, estimated_roas, etc.

### campaign_performance
- Stores actual performance data
- Fields: impressions, clicks, conversions, spend, revenue, metrics

### ad_benchmarks
- Reference data for industry benchmarks
- Fields: platform, industry, metric, value, source

## API Endpoints

### Campaign Management
- `POST /api/campaigns` - Create new campaign
- `GET /api/campaigns` - Get all campaigns
- `GET /api/campaigns/<id>` - Get campaign details
- `PUT /api/campaigns/<id>` - Update campaign
- `DELETE /api/campaigns/<id>` - Delete campaign
- `POST /api/campaigns/<id>/launch` - Launch campaign

### Health Check
- `GET /api/health` - Check API health

## Troubleshooting

### "Unable to connect to Supabase"
- Verify SUPABASE_URL and SUPABASE_KEY in .env
- Check internet connection
- Ensure Supabase project is active

### "Table does not exist"
- Run the schema.sql migration again
- Check Supabase SQL Editor for errors
- Verify all tables are created in Supabase dashboard

### CORS Errors
- CORS is already enabled in Flask app
- If issues persist, check browser console for specific errors

### Port Already in Use
If port 8000 is already in use, modify `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=8001)  # Change to different port
```
