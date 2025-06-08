from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health", summary="Health check endpoint", response_description="Application health status")
async def health_check():
    """
    Checks the health of the application.
    Returns a simple success message if the application is running.
    """
    return {"status": "ok", "message": "Application is running normally."}


@router.get("/version", summary="Application version endpoint", response_description="Application name and version")
async def get_version():
    """
    Returns the current application name and version.
    """
    return {"app_name": settings.APP_NAME, "version": settings.APP_VERSION}
