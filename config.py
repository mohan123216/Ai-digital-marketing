# config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
# Load both env files so API routes that use os.getenv can see Google Ads vars.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "google_ads_mcp" / ".env")

class Settings(BaseSettings):
    # Base paths
    BASE_DIR: Path = BASE_DIR
    DATA_PATH: str = str(BASE_DIR / "data" / "marketing_campaign_dataset_corrected.csv")
    MODEL_PATH: str = str(BASE_DIR / "models/")
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Marketing Planning Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    # Supabase settings
    SUPABASE_URL: str = "https://ahcesqtzunrmuvqjfelk.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFoY2VzcXR6dW5ybXV2cWpmZWxrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzMDA3MjIsImV4cCI6MjA4NDg3NjcyMn0.pkyjLJGvU_gDXzdCimjY01H62CWZDuDnHUIsJVb8MqE"
    SUPABASE_SERVICE_ROLE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFoY2VzcXR6dW5ybXV2cWpmZWxrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTMwMDcyMiwiZXhwIjoyMDg0ODc2NzIyfQ.HpoWf1aWXvDs0cKimMNT60VlFBtOeJsWPl0Ac1ZlNbs"
    SUPABASE_CAMPAIGN_TABLE: str = "campaign_runs"
    SUPABASE_USERS_TABLE: str = "app_users"

    # Custom auth settings
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # Model Settings
    TEST_SIZE: float = 0.2
    RANDOM_STATE: int = 42
    N_ESTIMATORS: int = 200
    MAX_DEPTH: int = 10
    
    # Recommendation Settings
    MAX_RECOMMENDATIONS: int = 5
    MIN_CONFIDENCE_THRESHOLD: float = 0.3
    BUDGET_BUFFER: float = 0.2  # 20% buffer for budget recommendations

    # Groq LLM settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    
    class Config:
        env_file = (".env", "google_ads_mcp/.env")
        case_sensitive = True
        extra = "ignore"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Allow common environment labels for debug mode."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return bool(value)

# Create global settings object
settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.DATA_PATH), exist_ok=True)
os.makedirs(settings.MODEL_PATH, exist_ok=True)
