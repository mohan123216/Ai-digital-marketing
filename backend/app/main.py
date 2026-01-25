from fastapi import FastAPI

app = FastAPI(
    title="AI Marketing Automation System",
    version="1.0"
)

@app.get("/")
def root():
    return {"message": "AI Marketing Automation Backend is running"}
