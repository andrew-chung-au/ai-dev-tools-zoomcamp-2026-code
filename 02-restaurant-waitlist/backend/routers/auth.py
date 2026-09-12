from fastapi import APIRouter, Depends

from backend.deps import get_repository
from backend.models import StaffSession
from backend.repository import InMemoryRepository
from backend.schemas import LoginRequest
from backend.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=StaffSession)
def login(payload: LoginRequest, repo: InMemoryRepository = Depends(get_repository)):
    return auth_service.login(repo, payload.username, payload.password)
