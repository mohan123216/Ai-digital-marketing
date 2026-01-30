# 🚀 Quick Start: AI Suggestions Feature

## Prerequisites
- ✅ Python 3.8+ installed
- ✅ Node.js installed
- ✅ Google Gemini API key (in `.env`)
- ✅ Supabase project set up with schema
- ✅ `marketing_campaign_dataset.csv` in backend folder

## Installation & Running

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**What it installs:**
- Flask & Flask-CORS
- Supabase SDK
- Google Generative AI (Gemini)
- Pandas (for CSV analysis)
- Python-dotenv

### Step 2: Start Backend

```bash
python app.py
```

**Expected Output:**
```
✅ Loaded marketing dataset with 100000 records
 * Running on http://127.0.0.1:8000
```

### Step 3: Start Frontend (in another terminal)

```bash
cd frontend
npm start
```

**Expected Output:**
```
Compiled successfully!
You can now view frontend in the browser.
```

---

## Using AI Suggestions

### Create a Campaign First
1. Click "Create New Campaign"
2. Fill in product details (Product Name, Type)
3. Choose goal and budget
4. Select target audience
5. Choose platforms (Facebook, Instagram, etc.)
6. Click "Create Campaign"

### Generate AI Suggestions
1. Find your campaign in the "New Campaigns" section
2. Click **"Get AI Suggestions"** button (brain icon)
3. Wait ~5-10 seconds for AI to generate suggestions
4. Beautiful modal will open with recommendations

### What You'll See
✅ **Platform Strategy** - Best platforms to use
✅ **Audience Insights** - Who to target
✅ **Budget Allocation** - How to split budget
✅ **Expected Performance** - ROI estimates
✅ **Content Tips** - What content works
✅ **Timing Strategy** - When to run ads
✅ **Historical Data** - Platform performance metrics

---

## Troubleshooting

### Error: "Could not find table 'public.campaigns'"
**Solution:** Execute schema.sql in Supabase SQL Editor first
- Go to https://supabase.com/dashboard
- SQL Editor → New Query
- Paste `schema.sql` content → Run

### Error: "Gemini API Error"
**Solution:** Check GEMINI_API_KEY in `.env`
```bash
# Check if set
echo $GEMINI_API_KEY

# If not set, add to .env
GEMINI_API_KEY=your_key_here
```

### Error: "Could not load marketing dataset"
**Solution:** Ensure CSV file exists
```bash
# Check file
ls backend/marketing_campaign_dataset.csv

# If missing, download from Kaggle and place in backend folder
```

### Modal not opening after clicking "Get AI Suggestions"
**Solution:** Check browser console for errors (F12)
- Look for network request errors
- Check backend logs for API errors
- Ensure CSS loaded properly (Network tab)

### Suggestions taking too long
**Normal:** First request takes 10-15 seconds (API calls)
**Subsequent:** Gets faster if cached
**If stuck:** Restart backend with `python app.py`

---

## Testing

### Test Campaign Data:
```
Product Name: Nike Air Max
Product Type: Shoes
Goal: Sales Conversion
Budget: $5,000
Duration: 30 days
Audience: 18-45, Male/Female, USA
Platforms: Facebook, Instagram
```

### Expected Suggestions Include:
- Platform performance comparisons
- Budget allocation recommendations
- Audience segment insights
- Estimated conversion rates
- Content strategy tips
- Risk warnings
- Success metrics to track

---

## File Structure

```
backend/
├── app.py                              # Flask API with AI endpoints
├── requirements.txt                    # Dependencies (with pandas added)
├── marketing_campaign_dataset.csv      # Kaggle dataset (100k+ records)
└── .env                                # GEMINI_API_KEY configured

frontend/
├── src/
│   ├── components/
│   │   ├── CampaignWizard.js          # Updated with modal UI
│   │   └── CampaignWizard.css         # Added modal styles
│   └── services/
│       └── api.js                     # Already has getAISuggestions()
```

---

## API Endpoints

### Generate Suggestions
```
POST /api/campaigns/{campaign_id}/ai-suggestions
```
**Response:**
```json
{
  "success": true,
  "suggestions": "AI-generated recommendations...",
  "historical_insights": {
    "Facebook": {
      "avg_conversion_rate": 0.085,
      "avg_roi": 5.67,
      "avg_engagement_score": 6.5
    }
  }
}
```

### Get Stored Recommendations
```
GET /api/campaigns/{campaign_id}/recommendations
```

---

## Performance Tips

1. **First Load:** May take 2-3 seconds to load Kaggle dataset
2. **AI Generation:** 5-10 seconds per campaign (Gemini API)
3. **Caching:** Suggestions stored in database for quick retrieval
4. **Optimization:** Consider dataset filtering by industry for faster analysis

---

## Next Steps

After implementing AI suggestions:

1. ✅ Create test campaigns
2. ✅ Generate suggestions for different platforms
3. ✅ Analyze recommendation quality
4. ✅ Apply suggestions to live campaigns
5. ✅ Track actual vs predicted performance
6. ✅ Refine AI prompts based on results

---

## Support

- **Issue with Gemini API?** Check quota at https://aistudio.google.com
- **Database error?** Check Supabase dashboard for connectivity
- **Frontend error?** Check browser DevTools (F12)
- **CSV not loading?** Verify file encoding is UTF-8

---

**Ready to get started? Run `python app.py` in the backend folder!** 🚀
