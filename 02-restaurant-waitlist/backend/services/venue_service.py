from backend.errors import ServiceError
from backend.models import Venue
from backend.repository import InMemoryRepository
from backend.schemas import UpdateVenueRequest


def get_venue(repo: InMemoryRepository) -> Venue:
    return repo.venue


def update_venue(repo: InMemoryRepository, payload: UpdateVenueRequest) -> Venue:
    venue = repo.venue
    fields = payload.model_fields_set

    if "name" in fields:
        if payload.name is None or not payload.name.strip():
            raise ServiceError(400, "invalid_name", "Venue name is required.")
        venue.name = payload.name.strip()
    if "contactPhone" in fields and payload.contactPhone is not None:
        venue.contactPhone = payload.contactPhone
    if "staffNotificationEmail" in fields and payload.staffNotificationEmail is not None:
        venue.staffNotificationEmail = payload.staffNotificationEmail
    if "menuUrl" in fields and payload.menuUrl is not None:
        venue.menuUrl = payload.menuUrl
    if "maxOnlinePartySize" in fields:
        if payload.maxOnlinePartySize is None or payload.maxOnlinePartySize < 1:
            raise ServiceError(
                400,
                "invalid_max_party_size",
                "Maximum online party size must be a positive whole number.",
            )
        venue.maxOnlinePartySize = payload.maxOnlinePartySize
    if "gracePeriodMinutes" in fields:
        if payload.gracePeriodMinutes is None or payload.gracePeriodMinutes < 1:
            raise ServiceError(
                400,
                "invalid_grace_period",
                "Grace period must be a positive whole number of minutes.",
            )
        venue.gracePeriodMinutes = payload.gracePeriodMinutes
    if "entryMode" in fields and payload.entryMode is not None:
        venue.entryMode = payload.entryMode
    if "waitlistOpen" in fields and payload.waitlistOpen is not None:
        venue.waitlistOpen = payload.waitlistOpen
    if "defaultWaitEstimateMinutes" in fields and payload.defaultWaitEstimateMinutes is not None:
        for key, value in payload.defaultWaitEstimateMinutes.model_dump(exclude_unset=True).items():
            venue.defaultWaitEstimateMinutes[key] = value
    if "messages" in fields and payload.messages is not None:
        updates = payload.messages.model_dump(exclude_unset=True)
        venue.messages = venue.messages.model_copy(update=updates)

    return venue
