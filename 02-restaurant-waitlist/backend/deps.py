from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.errors import ServiceError
from backend.models import StaffSession
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.services.auth_service import get_session

bearer_scheme = HTTPBearer(auto_error=False)


def get_repository(request: Request) -> InMemoryRepository:
    return request.app.state.repository


def get_notifier(request: Request) -> NotificationProvider:
    return request.app.state.notifier


def require_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    repo: InMemoryRepository = Depends(get_repository),
) -> StaffSession:
    if credentials is None:
        raise ServiceError(401, "unauthorized", "Missing bearer token.")
    session = get_session(repo, credentials.credentials)
    if session is None:
        raise ServiceError(401, "unauthorized", "Invalid or expired session token.")
    return session
