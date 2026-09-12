from fastapi import APIRouter, Depends

from backend.deps import get_notifier, get_repository
from backend.models import WaitlistEntry
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.schemas import GuestStatus
from backend.services import waitlist_service

router = APIRouter(tags=["guest"])


@router.get("/guest/entries/{accessToken}", response_model=GuestStatus)
def get_guest_entry(accessToken: str, repo: InMemoryRepository = Depends(get_repository)):
    return waitlist_service.get_guest_entry(repo, accessToken)


@router.post("/guest/entries/{accessToken}/cancel", response_model=WaitlistEntry)
def cancel_guest_entry(
    accessToken: str,
    repo: InMemoryRepository = Depends(get_repository),
    notifier: NotificationProvider = Depends(get_notifier),
):
    return waitlist_service.cancel_guest_entry(repo, accessToken, notifier)
