from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import ALLOWED_ORIGINS
from backend.errors import ServiceError
from backend.notifications import ConsoleNotificationProvider
from backend.repository import create_seed_repository
from backend.routers import (
    auth,
    dashboard,
    guest,
    large_party_enquiries,
    notifications,
    tables,
    venue,
    waitlist_entries,
)


def create_app() -> FastAPI:
    app = FastAPI(title="Restaurant Waitlist API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.repository = create_seed_repository()
    app.state.notifier = ConsoleNotificationProvider()

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})

    api_router = APIRouter(prefix="/api")
    api_router.include_router(auth.router)
    api_router.include_router(venue.router)
    api_router.include_router(dashboard.router)
    api_router.include_router(waitlist_entries.router)
    api_router.include_router(guest.router)
    api_router.include_router(tables.router)
    api_router.include_router(large_party_enquiries.router)
    api_router.include_router(notifications.router)
    app.include_router(api_router)

    return app


app = create_app()
