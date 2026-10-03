from fastapi import FastAPI

from app.api.webhooks import router as webhook_router

app = FastAPI(
    title="ReviewPilot",
    description="AI-powered GitHub Pull Request Reviewer",
    version="0.1.0",
)

app.include_router(
    webhook_router,
    prefix="/api/v1/webhooks",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "reviewpilot",
    }