from typing import Optional

from fastapi import APIRouter, Depends

from backend.deps import get_repository, require_staff
from backend.models import StaffSession
from backend.repository import InMemoryRepository
from backend.schemas import DashboardData
from backend.services import waitlist_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardData)
def get_dashboard(
    serviceDate: Optional[str] = None,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.get_dashboard(repo, serviceDate)
