"""Global exception handlers and custom error responses."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.app.core.logging import logger


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please contact the administrator.",
            "path": request.url.path
        }
    )

