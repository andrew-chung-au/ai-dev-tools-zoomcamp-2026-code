from fastapi import APIRouter, Depends

from backend.deps import get_notifier, get_repository, require_staff
from backend.models import Notification, StaffSession
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.schemas import CreateNotificationEventRequest
from backend.services import notification_service

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[Notification])
def list_notifications(
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return notification_service.list_notifications(repo)


@router.post("/notifications", status_code=201, response_model=Notification)
def create_notification_event(
    payload: CreateNotificationEventRequest,
    repo: InMemoryRepository = Depends(get_repository),
    notifier: NotificationProvider = Depends(get_notifier),
    _staff: StaffSession = Depends(require_staff),
):
    return notification_service.create_notification_event(repo, payload, notifier)
