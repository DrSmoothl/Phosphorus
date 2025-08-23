"""API routes package."""

from .health import router as health_router
from .hydro import hydro_router
from .jplag import jplag_router

__all__ = ["health_router", "hydro_router", "jplag_router"]
