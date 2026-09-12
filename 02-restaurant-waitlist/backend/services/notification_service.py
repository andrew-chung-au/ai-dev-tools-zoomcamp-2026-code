from backend.models import Notification
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.schemas import CreateNotificationEventRequest
from backend.utils import now_iso


def list_notifications(repo: InMemoryRepository) -> list[Notification]:
    return list(reversed(repo.notifications))


def create_notification_event(
    repo: InMemoryRepository,
    payload: CreateNotificationEventRequest,
    notifier: NotificationProvider,
) -> Notification:
    notification = Notification(
        id=repo.next_id("notif"),
        entryId=payload.entryId,
        recipientType=payload.recipientType,
        channel=payload.channel,
        templateType=payload.templateType,
        renderedMessage=payload.renderedMessage,
        deliveryStatus="sent",
        createdAt=now_iso(),
        sentAt=now_iso(),
    )
    repo.notifications.append(notification)
    notifier.send(notification)
    return notification
