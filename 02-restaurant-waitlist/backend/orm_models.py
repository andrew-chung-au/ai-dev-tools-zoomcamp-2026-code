"""SQLAlchemy ORM entities backing `DatabaseRepository`.

Named to match the Pydantic domain/response models in `backend/models.py`
field-for-field (including the camelCase attribute names, to match
`openapi.yaml` and to keep conversion between the two trivial). Kept in a
separate module from `backend/models.py` because those Pydantic classes are
also used directly as FastAPI response bodies throughout `backend/routers`
and `backend/services`, so reusing their names here would collide.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from backend.db import Base
from backend.models import VenueMessageSettings


class VenueORM(Base):
    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    logoPlaceholderLabel: Mapped[str] = mapped_column(String)
    contactPhone: Mapped[str] = mapped_column(String)
    staffNotificationEmail: Mapped[str] = mapped_column(String)
    menuUrl: Mapped[str] = mapped_column(String)
    maxOnlinePartySize: Mapped[int] = mapped_column(Integer)
    gracePeriodMinutes: Mapped[int] = mapped_column(Integer)
    entryMode: Mapped[str] = mapped_column(String)
    waitlistOpen: Mapped[bool] = mapped_column(Boolean)
    defaultWaitEstimateMinutes: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))
    messagesJson: Mapped[dict] = mapped_column("messages", JSON)
    serviceDate: Mapped[str] = mapped_column(String)

    @property
    def messages(self) -> VenueMessageSettings:
        return VenueMessageSettings(**self.messagesJson)

    @messages.setter
    def messages(self, value: VenueMessageSettings) -> None:
        self.messagesJson = value.model_dump()


class StaffUserORM(Base):
    __tablename__ = "staff_users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    passwordHash: Mapped[str] = mapped_column(String)
    staffName: Mapped[str] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TableORM(Base):
    __tablename__ = "tables"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    minCapacity: Mapped[int] = mapped_column(Integer)
    maxCapacity: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean)
    availabilityState: Mapped[str] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    occupyingTicketCode: Mapped[str | None] = mapped_column(String, nullable=True)
    occupyingEntryId: Mapped[str | None] = mapped_column(String, nullable=True)


class WaitlistEntryORM(Base):
    __tablename__ = "waitlist_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    venueId: Mapped[str] = mapped_column(String)
    serviceDate: Mapped[str] = mapped_column(String)
    ticketCode: Mapped[str] = mapped_column(String)
    ticketSequence: Mapped[int] = mapped_column(Integer)
    guestName: Mapped[str] = mapped_column(String)
    partySize: Mapped[int] = mapped_column(Integer)
    originalPartySize: Mapped[int] = mapped_column(Integer)
    originalPartyClass: Mapped[str] = mapped_column(String)
    currentSeatingClass: Mapped[str] = mapped_column(String)
    reviewRequired: Mapped[bool] = mapped_column(Boolean)
    reviewReason: Mapped[str | None] = mapped_column(String, nullable=True)
    mobileNumber: Mapped[str] = mapped_column(String)
    seatingNote: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    arrivalTime: Mapped[str] = mapped_column(String)
    estimatedWaitMinutes: Mapped[int] = mapped_column(Integer)
    notifiedAt: Mapped[str | None] = mapped_column(String, nullable=True)
    returnByAt: Mapped[str | None] = mapped_column(String, nullable=True)
    seatedAt: Mapped[str | None] = mapped_column(String, nullable=True)
    completedAt: Mapped[str | None] = mapped_column(String, nullable=True)
    cancelledAt: Mapped[str | None] = mapped_column(String, nullable=True)
    tableId: Mapped[str | None] = mapped_column(String, nullable=True)
    tableName: Mapped[str | None] = mapped_column(String, nullable=True)
    seatingOverrideReason: Mapped[str | None] = mapped_column(String, nullable=True)
    accessToken: Mapped[str] = mapped_column(String, unique=True)


class LargePartyEnquiryORM(Base):
    __tablename__ = "large_party_enquiries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    reference: Mapped[str] = mapped_column(String)
    venueId: Mapped[str] = mapped_column(String)
    guestName: Mapped[str] = mapped_column(String)
    partySize: Mapped[int] = mapped_column(Integer)
    mobileNumber: Mapped[str] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)


class NotificationORM(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    entryId: Mapped[str | None] = mapped_column(String, nullable=True)
    recipientType: Mapped[str] = mapped_column(String)
    channel: Mapped[str] = mapped_column(String)
    templateType: Mapped[str] = mapped_column(String)
    renderedMessage: Mapped[str] = mapped_column(String)
    deliveryStatus: Mapped[str] = mapped_column(String)
    createdAt: Mapped[str] = mapped_column(String)
    sentAt: Mapped[str | None] = mapped_column(String, nullable=True)
    errorMessage: Mapped[str | None] = mapped_column(String, nullable=True)


class CounterORM(Base):
    """Backs `next_id`/`next_ticket_sequence` so ids survive restarts."""

    __tablename__ = "counters"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, default=0)
