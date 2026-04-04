# AI Marketing Planner with Supabase Storage

This project includes:
- FastAPI backend with custom JWT auth.
- Supabase persistence for users and campaign workflow history.
- React frontend for signup, login, campaign generation, and workflow history.

## 1) Supabase setup

1. Create a Supabase project.
2. Run SQL from `supabase/schema.sql` in the SQL editor.
3. Copy keys:
   - Project URL
   - service role key
4. Update backend `.env` values:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

## 2) Backend setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run API:
   ```bash
   python run.py
   ```

## 3) Frontend setup

1. Ensure `frontend/.env` contains:
   - `VITE_API_BASE_URL=http://localhost:8000`
2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Run frontend:
   ```bash
   npm run dev
   ```

Frontend URL: `http://localhost:5173`  
Backend URL: `http://localhost:8000`

## Auth + workflow sequence

1. User signs up or logs in on React frontend using backend auth endpoints.
2. Backend hashes passwords and stores user rows in Supabase `app_users`.
3. Backend returns JWT access token.
4. Frontend calls protected endpoints with `Authorization: Bearer <token>`.
5. Backend validates JWT and stores campaign outputs in Supabase `campaign_runs`.
