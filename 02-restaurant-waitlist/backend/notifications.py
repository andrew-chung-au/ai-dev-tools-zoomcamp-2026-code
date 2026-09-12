from abc import ABC, abstractmethod

from backend.models import Notification


class NotificationProvider(ABC):
    """Delivery abstraction so real SMS/email/webhook providers can be added later
    without changing waitlist logic."""

    @abstractmethod
    def send(self, notification: Notification) -> None: ...


class ConsoleNotificationProvider(NotificationProvider):
    def send(self, notification: Notification) -> None:
        print(
            f"[notification] to={notification.recipientType} "
            f"channel={notification.channel} template={notification.templateType}: "
            f"{notification.renderedMessage}"
        )
