"""Core application factory."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from ..api import health_router
from ..api.models import ErrorResponse
from ..common import get_logger, settings

logger = get_logger()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        debug=settings.debug,
    )

    # Include routers
    app.include_router(health_router)

    # Add exception handlers
    add_exception_handlers(app)

    # Add middleware
    add_middleware(app)

    logger.info(f"FastAPI app created: {settings.api_title} v{settings.api_version}")
    return app


def add_exception_handlers(app: FastAPI) -> None:
    """Add global exception handlers."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                message=exc.detail,
                error_code=f"HTTP_{exc.status_code}",
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}")

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                success=False,
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                details={"error": str(exc)} if settings.debug else None,
            ).model_dump(),
        )


def add_middleware(app: FastAPI) -> None:
    """Add middleware to the application."""

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """Log requests and responses."""
        start_time = request.state.start_time = __import__("time").time()

        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = __import__("time").time() - start_time
        logger.info(
            f"Response: {response.status_code} - {process_time:.3f}s"
        )

        return response
