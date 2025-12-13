"""API routes for ETL Pipeline"""

from src.api.routes.jobs import router as jobs_router
from src.api.routes.status import router as status_router
from src.api.routes.data import router as data_router
from src.api.routes.websocket import router as websocket_router

__all__ = ["jobs_router", "status_router", "data_router", "websocket_router"]
