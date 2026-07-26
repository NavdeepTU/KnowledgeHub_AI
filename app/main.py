from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.core.config import settings
from app.core.logging import configure_logging


# Configure logging when the application starts.
configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(documents_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Simple endpoint used to check whether the API is running.
    """
    return {"status": "healthy"}
