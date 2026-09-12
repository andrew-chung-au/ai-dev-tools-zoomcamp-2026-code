"""Request bodies and composite/derived response shapes (not persisted entities)."""

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from backend.models import (
    EntryMode,
    LargePartyEnquiry,
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationTemplateType,
    Table,
    Venue,
    WaitlistEntry,
    WaitlistStatus,
)


class Error(BaseModel):
    code: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateGuestEntryRequest(BaseModel):
    guestName: str
    partySize: int
    mobileNumber: str
    seatingNote: Optional[str] = None
    policyAcknowledged: bool


class CreateGuestEntryResultEntry(BaseModel):
    kind: Literal["entry"] = "entry"
    entry: WaitlistEntry
    accessToken: str
    message: str


class CreateGuestEntryResultLargePartyEnquiry(BaseModel):
    kind: Literal["large_party_enquiry"] = "large_party_enquiry"
    enquiry: LargePartyEnquiry
    message: str


class CreateGuestEntryResultClosed(BaseModel):
    kind: Literal["closed"] = "closed"
    message: str


CreateGuestEntryResult = Union[
    CreateGuestEntryResultEntry,
    CreateGuestEntryResultLargePartyEnquiry,
    CreateGuestEntryResultClosed,
]


class GuestStatus(BaseModel):
    ticketCode: str
    guestName: str
    partySize: int
    status: WaitlistStatus
    estimatedWaitMinutes: int
    message: str
    notifiedAt: Optional[str] = None
    returnByAt: Optional[str] = None
    needsAttention: bool
    cancellationAllowed: bool
    venueName: str
    venueLogoPlaceholderLabel: str
    serviceDate: str


class SeatEntryRequest(BaseModel):
    tableId: str
    seatingOverrideReason: Optional[str] = None


class ExtendReturnByRequest(BaseModel):
    additionalMinutes: int


class UpdateWaitEstimateRequest(BaseModel):
    estimatedWaitMinutes: int = Field(ge=0)


class PartialDefaultWaitEstimateMinutes(BaseModel):
    A: Optional[int] = None
    B: Optional[int] = None
    C: Optional[int] = None
    D: Optional[int] = None


class PartialVenueMessageSettings(BaseModel):
    joinMessage: Optional[str] = None
    policyAcknowledgementMessage: Optional[str] = None
    confirmationMessage: Optional[str] = None
    tableReadyMessage: Optional[str] = None
    cancellationMessage: Optional[str] = None
    closedWaitlistMessage: Optional[str] = None
    largePartyMessage: Optional[str] = None
    largePartyConfirmationMessage: Optional[str] = None


class UpdateVenueRequest(BaseModel):
    name: Optional[str] = None
    contactPhone: Optional[str] = None
    staffNotificationEmail: Optional[str] = None
    menuUrl: Optional[str] = None
    maxOnlinePartySize: Optional[int] = None
    gracePeriodMinutes: Optional[int] = None
    entryMode: Optional[EntryMode] = None
    waitlistOpen: Optional[bool] = None
    defaultWaitEstimateMinutes: Optional[PartialDefaultWaitEstimateMinutes] = None
    messages: Optional[PartialVenueMessageSettings] = None


class NotificationResult(BaseModel):
    entry: WaitlistEntry
    notification: Notification


class LargePartyEnquiryRequest(BaseModel):
    guestName: str
    partySize: int
    mobileNumber: str
    note: Optional[str] = None


class DashboardSummary(BaseModel):
    activeWaiting: int
    pendingReview: int
    notified: int
    needsAttention: int


class DashboardData(BaseModel):
    venue: Venue
    serviceDate: str
    summary: DashboardSummary
    entries: list[WaitlistEntry]
    tables: list[Table]


class CreateTableRequest(BaseModel):
    name: str
    minCapacity: int = Field(ge=1)
    maxCapacity: int = Field(ge=1)
    notes: Optional[str] = None


class UpdateTableRequest(BaseModel):
    name: Optional[str] = None
    minCapacity: Optional[int] = Field(default=None, ge=1)
    maxCapacity: Optional[int] = Field(default=None, ge=1)
    active: Optional[bool] = None
    notes: Optional[str] = None


class SetTableAvailabilityRequest(BaseModel):
    availabilityState: Literal["available", "needs_tidying"]


class CreateNotificationEventRequest(BaseModel):
    entryId: Optional[str] = None
    recipientType: NotificationRecipientType
    channel: NotificationChannel
    templateType: NotificationTemplateType
    renderedMessage: str
