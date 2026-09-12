"""Persistence models: the entities held in the in-memory store.

Field names are camelCase to match `openapi.yaml` exactly, since these models
double as the API response bodies for their respective entities.
"""

from typing import Literal, Optional

from pydantic import BaseModel

PartySizeClass = Literal["A", "B", "C", "D"]

WaitlistStatus = Literal[
    "pending", "waiting", "notified", "seated", "completed", "cancelled", "no_show"
]

EntryMode = Literal["automatic", "staff_review"]

TableAvailabilityState = Literal["available", "occupied", "needs_tidying"]

NotificationChannel = Literal["sms", "email", "in_app"]
NotificationRecipientType = Literal["guest", "staff"]
NotificationTemplateType = Literal[
    "table_ready", "confirmation", "cancellation", "large_party_staff_alert"
]
NotificationDeliveryStatus = Literal["queued", "sent", "failed"]


class VenueMessageSettings(BaseModel):
    joinMessage: str
    policyAcknowledgementMessage: str
    confirmationMessage: str
    tableReadyMessage: str
    cancellationMessage: str
    closedWaitlistMessage: str
    largePartyMessage: str
    largePartyConfirmationMessage: str


class Venue(BaseModel):
    id: str
    name: str
    logoPlaceholderLabel: str
    contactPhone: str
    staffNotificationEmail: str
    menuUrl: str
    maxOnlinePartySize: int
    gracePeriodMinutes: int
    entryMode: EntryMode
    waitlistOpen: bool
    defaultWaitEstimateMinutes: dict[PartySizeClass, int]
    messages: VenueMessageSettings
    serviceDate: str


class StaffUser(BaseModel):
    """Internal only; never serialized to the API."""

    id: str
    username: str
    passwordHash: str
    staffName: str
    active: bool = True


class StaffSession(BaseModel):
    token: str
    staffName: str
    username: str
    venueId: str
    issuedAt: str
    mocked: bool = True


class Table(BaseModel):
    id: str
    name: str
    minCapacity: int
    maxCapacity: int
    active: bool
    availabilityState: TableAvailabilityState
    notes: Optional[str] = None
    occupyingTicketCode: Optional[str] = None
    occupyingEntryId: Optional[str] = None


class WaitlistEntry(BaseModel):
    id: str
    venueId: str
    serviceDate: str
    ticketCode: str
    ticketSequence: int
    guestName: str
    partySize: int
    originalPartySize: int
    originalPartyClass: PartySizeClass
    currentSeatingClass: PartySizeClass
    reviewRequired: bool
    reviewReason: Optional[str] = None
    mobileNumber: str
    seatingNote: Optional[str] = None
    status: WaitlistStatus
    arrivalTime: str
    estimatedWaitMinutes: int
    notifiedAt: Optional[str] = None
    returnByAt: Optional[str] = None
    seatedAt: Optional[str] = None
    completedAt: Optional[str] = None
    cancelledAt: Optional[str] = None
    tableId: Optional[str] = None
    tableName: Optional[str] = None
    seatingOverrideReason: Optional[str] = None
    accessToken: str


class LargePartyEnquiry(BaseModel):
    id: str
    reference: str
    venueId: str
    guestName: str
    partySize: int
    mobileNumber: str
    note: Optional[str] = None
    createdAt: str
    message: str


class Notification(BaseModel):
    id: str
    entryId: Optional[str] = None
    recipientType: NotificationRecipientType
    channel: NotificationChannel
    templateType: NotificationTemplateType
    renderedMessage: str
    deliveryStatus: NotificationDeliveryStatus
    createdAt: str
    sentAt: Optional[str] = None
    errorMessage: Optional[str] = None
