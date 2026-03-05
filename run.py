# run.py
import uvicorn
import sys
from pathlib import Path

if __name__ == "__main__":
    print("="*60)
    print("🚀 STARTING PLANNING AGENT")
    print("="*60)
    print("\n📊 API will be available at: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("📈 ReDoc: http://localhost:8000/redoc")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )