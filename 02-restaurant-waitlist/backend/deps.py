from typing import Iterator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.errors import ServiceError
from backend.models import StaffSession
from backend.notifications import NotificationProvider
from backend.repositories import DatabaseRepository
from backend.services.auth_service import get_session

bearer_scheme = HTTPBearer(auto_error=False)


def get_repository(request: Request) -> Iterator[DatabaseRepository]:
    """One SQLAlchemy session per request; committed on success, rolled
    back if the request raises. Staff sessions (bearer tokens) live on
    `app.state` instead of the database, shared across requests like the
    original in-memory store's session dict."""
    session = request.app.state.session_factory()
    repo = DatabaseRepository(session, staff_sessions=request.app.state.staff_sessions)
    try:
        yield repo
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_notifier(request: Request) -> NotificationProvider:
    return request.app.state.notifier


def require_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    repo: DatabaseRepository = Depends(get_repository),
) -> StaffSession:
    if credentials is None:
        raise ServiceError(401, "unauthorized", "Missing bearer token.")
    session = get_session(repo, credentials.credentials)
    if session is None:
        raise ServiceError(401, "unauthorized", "Invalid or expired session token.")
    return session
