from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import ALLOWED_ORIGINS, DATABASE_URL
from backend.db import Base, make_engine, make_session_factory
from backend.errors import ServiceError
from backend.notifications import ConsoleNotificationProvider
from backend.repositories import seed_if_empty
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


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="Restaurant Waitlist API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    engine = make_engine(database_url or DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_if_empty(session)
        session.commit()

    app.state.session_factory = session_factory
    app.state.staff_sessions = {}
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
