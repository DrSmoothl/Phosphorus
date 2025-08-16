"""Main application entry point."""

import uvicorn

from .common import get_logger, settings, setup_logging
from .core import create_app


def main() -> None:
    """Main entry point."""
    # Setup logging first
    setup_logging()
    logger = get_logger()

    logger.info("Starting Phosphorus server...")
    logger.info(f"Configuration: host={settings.host}, port={settings.port}")

    # Create FastAPI app
    app = create_app()

    # Configure uvicorn to use loguru
    uvicorn_config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_config=None,  # Disable uvicorn's default logging
    )

    # Override uvicorn loggers to use loguru
    import logging

    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn.access").handlers.clear()

    # Create and run server
    server = uvicorn.Server(uvicorn_config)
    server.run()


if __name__ == "__main__":
    main()
