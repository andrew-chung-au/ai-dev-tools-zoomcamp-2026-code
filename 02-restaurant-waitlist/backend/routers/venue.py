from fastapi import APIRouter, Depends

from backend.deps import get_repository, require_staff
from backend.models import StaffSession, Venue
from backend.repository import InMemoryRepository
from backend.schemas import UpdateVenueRequest
from backend.services import venue_service

router = APIRouter(tags=["venue"])


@router.get("/venue", response_model=Venue)
def get_venue(repo: InMemoryRepository = Depends(get_repository)):
    return venue_service.get_venue(repo)


@router.patch("/venue", response_model=Venue)
def update_venue(
    payload: UpdateVenueRequest,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return venue_service.update_venue(repo, payload)
