from backend.errors import ServiceError
from backend.models import LargePartyEnquiry, Notification
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.schemas import LargePartyEnquiryRequest
from backend.utils import is_valid_mobile_number, now_iso


def create_enquiry(
    repo: InMemoryRepository,
    payload: LargePartyEnquiryRequest,
    notifier: NotificationProvider,
) -> LargePartyEnquiry:
    if not payload.guestName.strip():
        raise ServiceError(400, "invalid_name", "Please enter a name for the party.")
    if not is_valid_mobile_number(payload.mobileNumber):
        raise ServiceError(400, "invalid_mobile_number", "Please enter a valid mobile number.")

    enquiry = LargePartyEnquiry(
        id=repo.next_id("enq"),
        reference=f"LP-{len(repo.enquiries) + 1:03d}",
        venueId=repo.venue.id,
        guestName=payload.guestName.strip(),
        partySize=payload.partySize,
        mobileNumber=payload.mobileNumber.strip(),
        note=payload.note.strip() if payload.note and payload.note.strip() else None,
        createdAt=now_iso(),
        message=repo.venue.messages.largePartyConfirmationMessage,
    )
    repo.enquiries.append(enquiry)

    notification = Notification(
        id=repo.next_id("notif"),
        entryId=None,
        recipientType="staff",
        channel="in_app",
        templateType="large_party_staff_alert",
        renderedMessage=(
            f"Large-party enquiry {enquiry.reference}: {enquiry.guestName}, "
            f"party of {enquiry.partySize}."
        ),
        deliveryStatus="sent",
        createdAt=now_iso(),
        sentAt=now_iso(),
    )
    repo.notifications.append(notification)
    notifier.send(notification)

    return enquiry
