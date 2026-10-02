from fastapi import FastAPI

app = FastAPI(
    title="ReviewPilot",
    description="AI-powered GitHub Pull Request Reviewer",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "reviewpilot",
    }