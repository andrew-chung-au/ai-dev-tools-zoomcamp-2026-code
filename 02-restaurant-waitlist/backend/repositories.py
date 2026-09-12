"""SQLAlchemy-backed repository.

`DatabaseRepository` implements the same attribute/method surface as
`InMemoryRepository` (see `backend/repository.py`) so `backend/services/*`
and `backend/routers/*` can use either without changes:

- `repo.venue`, `repo.tables`, `repo.entries`, `repo.enquiries`,
  `repo.notifications`, `repo.staff_users` behave like the in-memory lists
  services already filter, `.append()` to, and (for `tables`) reassign.
- `repo.find_entry`, `repo.find_entry_by_access_token`, `repo.find_table`,
  `repo.next_id`, `repo.next_ticket_sequence`, `repo.next_access_token`
  keep their original signatures.

Under the hood, everything is backed by one SQLAlchemy `Session` per
request (see `backend.deps.get_repository`). Collections return ORM rows
attached to that session, so the attribute mutations services already do
(e.g. `entry.status = "seated"`) are tracked by SQLAlchemy and persisted
when the request's session commits.
"""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import (
    LargePartyEnquiry,
    Notification,
    StaffSession,
    StaffUser,
    Table,
    Venue,
    VenueMessageSettings,
    WaitlistEntry,
)
from backend.orm_models import (
    CounterORM,
    LargePartyEnquiryORM,
    NotificationORM,
    StaffUserORM,
    TableORM,
    VenueORM,
    WaitlistEntryORM,
)
from backend.security import hash_password
from backend.utils import classify_party_size, iso_at_offset, today_iso

DEMO_VENUE_ID = "venue_demo"


def _to_orm(item, orm_cls):
    """Accept either a domain (Pydantic) instance or an already-ORM row."""
    if isinstance(item, orm_cls):
        return item
    return orm_cls(**item.model_dump())


class _TrackedList(list):
    """A query result list whose `.append()` adds new rows to the session,
    converting a Pydantic domain instance to its ORM counterpart first."""

    def __init__(self, items, session: Session, orm_cls):
        super().__init__(items)
        self._session = session
        self._orm_cls = orm_cls

    def append(self, item):
        obj = _to_orm(item, self._orm_cls)
        self._session.add(obj)
        super().append(obj)


class DatabaseRepository:
    def __init__(self, session: Session, staff_sessions: dict[str, StaffSession]) -> None:
        self.session = session
        self.sessions = staff_sessions

    # -- counters ------------------------------------------------------

    def next_id(self, prefix: str) -> str:
        counter = self.session.get(CounterORM, prefix)
        if counter is None:
            counter = CounterORM(key=prefix, value=0)
            self.session.add(counter)
        counter.value += 1
        self.session.flush()
        return f"{prefix}_{counter.value:04d}"

    def next_ticket_sequence(self, service_date: str) -> int:
        key = f"seq:{service_date}"
        counter = self.session.get(CounterORM, key)
        if counter is None:
            counter = CounterORM(key=key, value=0)
            self.session.add(counter)
        counter.value += 1
        self.session.flush()
        return counter.value

    def next_access_token(self) -> str:
        return f"tok_{secrets.token_urlsafe(16)}"

    # -- lookups ---------------------------------------------------------

    def find_entry(self, entry_id: str) -> WaitlistEntryORM | None:
        return self.session.get(WaitlistEntryORM, entry_id)

    def find_entry_by_access_token(self, access_token: str) -> WaitlistEntryORM | None:
        return self.session.scalars(
            select(WaitlistEntryORM).where(WaitlistEntryORM.accessToken == access_token)
        ).first()

    def find_table(self, table_id: str) -> TableORM | None:
        return self.session.get(TableORM, table_id)

    # -- collections -------------------------------------------------------

    @property
    def venue(self) -> VenueORM:
        return self.session.get(VenueORM, DEMO_VENUE_ID)

    @venue.setter
    def venue(self, value: Venue) -> None:
        orm = VenueORM(
            id=value.id,
            name=value.name,
            logoPlaceholderLabel=value.logoPlaceholderLabel,
            contactPhone=value.contactPhone,
            staffNotificationEmail=value.staffNotificationEmail,
            menuUrl=value.menuUrl,
            maxOnlinePartySize=value.maxOnlinePartySize,
            gracePeriodMinutes=value.gracePeriodMinutes,
            entryMode=value.entryMode,
            waitlistOpen=value.waitlistOpen,
            defaultWaitEstimateMinutes=dict(value.defaultWaitEstimateMinutes),
            messagesJson=value.messages.model_dump(),
            serviceDate=value.serviceDate,
        )
        self.session.add(orm)
        self.session.flush()

    @property
    def tables(self) -> _TrackedList:
        rows = self.session.scalars(select(TableORM).order_by(TableORM.id)).all()
        return _TrackedList(rows, self.session, TableORM)

    @tables.setter
    def tables(self, value) -> None:
        existing = {t.id: t for t in self.session.scalars(select(TableORM)).all()}
        incoming = {}
        for item in value:
            obj = _to_orm(item, TableORM)
            incoming[obj.id] = obj
        for table_id, obj in existing.items():
            if table_id not in incoming:
                self.session.delete(obj)
        for table_id, obj in incoming.items():
            if table_id not in existing:
                self.session.add(obj)
        self.session.flush()

    @property
    def entries(self) -> _TrackedList:
        rows = self.session.scalars(select(WaitlistEntryORM).order_by(WaitlistEntryORM.id)).all()
        return _TrackedList(rows, self.session, WaitlistEntryORM)

    @property
    def enquiries(self) -> _TrackedList:
        rows = self.session.scalars(select(LargePartyEnquiryORM).order_by(LargePartyEnquiryORM.id)).all()
        return _TrackedList(rows, self.session, LargePartyEnquiryORM)

    @property
    def notifications(self) -> _TrackedList:
        rows = self.session.scalars(select(NotificationORM).order_by(NotificationORM.id)).all()
        return _TrackedList(rows, self.session, NotificationORM)

    @property
    def staff_users(self) -> _TrackedList:
        rows = self.session.scalars(select(StaffUserORM)).all()
        return _TrackedList(rows, self.session, StaffUserORM)

    # -- seeding -----------------------------------------------------------

    def seed(self) -> None:
        today = today_iso()

        self.venue = Venue(
            id=DEMO_VENUE_ID,
            name="Demo Restaurant",
            logoPlaceholderLabel="Demo Restaurant logo placeholder",
            contactPhone="+61 2 5550 0100",
            staffNotificationEmail="front-of-house@demo-restaurant.example",
            menuUrl="https://example.com/demo-restaurant/menu",
            maxOnlinePartySize=12,
            gracePeriodMinutes=10,
            entryMode="staff_review",
            waitlistOpen=True,
            defaultWaitEstimateMinutes={"A": 15, "B": 25, "C": 40, "D": 55},
            serviceDate=today,
            messages=VenueMessageSettings(
                joinMessage="Join tonight's walk-in waitlist. We'll text you when your table is ready.",
                policyAcknowledgementMessage=(
                    "Wait times are estimates, not guaranteed seating times. Please stay "
                    "nearby — after we notify you, we hold your table for the grace period only."
                ),
                confirmationMessage="You're on the waitlist. Keep this page open to see your ticket and status.",
                tableReadyMessage="Your table is ready. Please come to the host stand and show your ticket code.",
                cancellationMessage="Your waitlist entry has been cancelled. You're welcome to join again any time.",
                closedWaitlistMessage="Our waitlist is closed right now. Please call us or try again during service hours.",
                largePartyMessage=(
                    "For parties larger than 12, please contact the restaurant so we can "
                    "discuss seating options. Your request has not been added to the waitlist."
                ),
                largePartyConfirmationMessage=(
                    "Thanks. We have sent your large-party request to the restaurant. A staff "
                    "member will contact you to discuss available options. This request is not "
                    "a confirmed booking or waitlist ticket."
                ),
            ),
        )

        self.staff_users.append(
            StaffUser(
                id="staff_0001",
                username="manager",
                passwordHash=hash_password("waitlist123"),
                staffName="Demo Manager",
                active=True,
            )
        )

        self.tables = [
            Table(id="tbl_1", name="T1", minCapacity=1, maxCapacity=2, active=True, availabilityState="available"),
            Table(
                id="tbl_2",
                name="T2",
                minCapacity=1,
                maxCapacity=2,
                active=True,
                availabilityState="needs_tidying",
                notes="Wobbly leg, needs a shim.",
            ),
            Table(id="tbl_3", name="T3", minCapacity=2, maxCapacity=4, active=True, availabilityState="available"),
            Table(
                id="tbl_4",
                name="T4",
                minCapacity=2,
                maxCapacity=4,
                active=True,
                availabilityState="available",
                notes="Near the window.",
            ),
            Table(id="tbl_5", name="T5", minCapacity=4, maxCapacity=6, active=True, availabilityState="available"),
            Table(
                id="tbl_6",
                name="T6",
                minCapacity=4,
                maxCapacity=6,
                active=False,
                availabilityState="needs_tidying",
                notes="Out of service — leg repair scheduled.",
            ),
        ]

        def make_entry(
            *,
            guest_name: str,
            party_size: int,
            mobile_number: str,
            status: str,
            arrival_minutes_ago: float,
            original_party_size: int | None = None,
            seating_note: str | None = None,
            notified_minutes_ago: float | None = None,
            table_id: str | None = None,
        ) -> WaitlistEntry:
            seq = self.next_ticket_sequence(today)
            original_size = original_party_size if original_party_size is not None else party_size
            original_class = classify_party_size(original_size)
            current_class = classify_party_size(party_size)
            notified_at = iso_at_offset(-notified_minutes_ago) if notified_minutes_ago is not None else None
            return_by_at = (
                iso_at_offset(self.venue.gracePeriodMinutes - notified_minutes_ago)
                if notified_minutes_ago is not None
                else None
            )
            table = self.find_table(table_id) if table_id else None
            entry = WaitlistEntry(
                id=self.next_id("entry"),
                venueId=self.venue.id,
                serviceDate=today,
                ticketCode=f"{original_class}-{seq:03d}",
                ticketSequence=seq,
                guestName=guest_name,
                partySize=party_size,
                originalPartySize=original_size,
                originalPartyClass=original_class,
                currentSeatingClass=current_class,
                reviewRequired=original_class != current_class,
                reviewReason=(
                    f"Party size changed from {original_size} to {party_size}; "
                    f"seating class is now {current_class}."
                    if original_class != current_class
                    else None
                ),
                mobileNumber=mobile_number,
                seatingNote=seating_note,
                status=status,
                arrivalTime=iso_at_offset(-arrival_minutes_ago),
                estimatedWaitMinutes=self.venue.defaultWaitEstimateMinutes[current_class],
                notifiedAt=notified_at,
                returnByAt=return_by_at,
                seatedAt=iso_at_offset(-arrival_minutes_ago + 5) if status == "seated" else None,
                tableId=table.id if table else None,
                tableName=table.name if table else None,
                accessToken=self.next_access_token(),
            )
            if table:
                table.availabilityState = "occupied"
                table.occupyingEntryId = entry.id
                table.occupyingTicketCode = entry.ticketCode
            self.entries.append(entry)
            return entry

        make_entry(
            guest_name="Ava Lindqvist",
            party_size=2,
            mobile_number="+61 400 111 222",
            status="waiting",
            arrival_minutes_ago=32,
        )
        notified = make_entry(
            guest_name="Marco Feld",
            party_size=4,
            mobile_number="+61 400 333 444",
            seating_note="Prefers a booth",
            status="notified",
            arrival_minutes_ago=28,
            notified_minutes_ago=3,
        )
        make_entry(
            guest_name="The Okonkwo Party",
            party_size=6,
            mobile_number="+61 400 555 666",
            seating_note="Wheelchair access required",
            status="waiting",
            arrival_minutes_ago=21,
        )
        overdue = make_entry(
            guest_name="Priya Raman",
            party_size=3,
            mobile_number="+61 400 777 888",
            status="notified",
            arrival_minutes_ago=45,
            notified_minutes_ago=18,
        )
        make_entry(
            guest_name="Tomas Berg",
            party_size=5,
            original_party_size=3,
            mobile_number="+61 400 999 000",
            seating_note="Two extra guests arrived",
            status="waiting",
            arrival_minutes_ago=14,
        )
        make_entry(
            guest_name="Hannah Cole",
            party_size=2,
            mobile_number="+61 401 222 333",
            status="pending",
            arrival_minutes_ago=4,
        )
        make_entry(
            guest_name="Diego Salas",
            party_size=6,
            mobile_number="+61 401 444 555",
            status="seated",
            arrival_minutes_ago=60,
            table_id="tbl_5",
        )

        self.notifications.append(
            Notification(
                id=self.next_id("notif"),
                entryId=notified.id,
                recipientType="guest",
                channel="sms",
                templateType="table_ready",
                renderedMessage=self.venue.messages.tableReadyMessage,
                deliveryStatus="sent",
                createdAt=notified.notifiedAt,
                sentAt=notified.notifiedAt,
            )
        )
        self.notifications.append(
            Notification(
                id=self.next_id("notif"),
                entryId=overdue.id,
                recipientType="guest",
                channel="sms",
                templateType="table_ready",
                renderedMessage=self.venue.messages.tableReadyMessage,
                deliveryStatus="sent",
                createdAt=overdue.notifiedAt,
                sentAt=overdue.notifiedAt,
            )
        )
        self.session.flush()


def seed_if_empty(session: Session) -> None:
    if session.get(VenueORM, DEMO_VENUE_ID) is not None:
        return
    DatabaseRepository(session, staff_sessions={}).seed()
