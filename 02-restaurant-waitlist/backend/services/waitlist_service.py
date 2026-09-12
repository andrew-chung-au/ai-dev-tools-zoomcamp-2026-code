from datetime import datetime, timedelta

from backend.errors import ServiceError
from backend.models import Notification, Table, WaitlistEntry
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.schemas import (
    CreateGuestEntryRequest,
    CreateGuestEntryResult,
    CreateGuestEntryResultClosed,
    CreateGuestEntryResultEntry,
    CreateGuestEntryResultLargePartyEnquiry,
    DashboardData,
    DashboardSummary,
    GuestStatus,
    LargePartyEnquiryRequest,
    SeatEntryRequest,
)
from backend.services import large_party_service
from backend.utils import (
    classify_party_size,
    is_needs_attention,
    is_table_compatible,
    is_valid_mobile_number,
    iso_at_offset,
    now_iso,
    sort_entries,
)

ACTIVE_CANCELLABLE_STATUSES = {"pending", "waiting", "notified"}
CLOSED_STATUSES = {"completed", "cancelled", "no_show"}


def find_entry_or_404(repo: InMemoryRepository, entry_id: str) -> WaitlistEntry:
    entry = repo.find_entry(entry_id)
    if entry is None:
        raise ServiceError(404, "entry_not_found", "Waitlist entry not found.")
    return entry


def find_entry_by_token_or_404(repo: InMemoryRepository, access_token: str) -> WaitlistEntry:
    entry = repo.find_entry_by_access_token(access_token)
    if entry is None:
        raise ServiceError(404, "entry_not_found", "We couldn't find this waitlist entry.")
    return entry


def _release_table(repo: InMemoryRepository, entry: WaitlistEntry) -> None:
    if not entry.tableId:
        return
    table = repo.find_table(entry.tableId)
    if table is not None:
        table.availabilityState = "needs_tidying"
        table.occupyingEntryId = None
        table.occupyingTicketCode = None


def get_dashboard(repo: InMemoryRepository, service_date: str | None) -> DashboardData:
    date = service_date or repo.venue.serviceDate
    entries = sort_entries([e for e in repo.entries if e.serviceDate == date])
    summary = DashboardSummary(
        activeWaiting=sum(1 for e in entries if e.status == "waiting"),
        pendingReview=sum(1 for e in entries if e.status == "pending"),
        notified=sum(1 for e in entries if e.status == "notified"),
        needsAttention=sum(1 for e in entries if is_needs_attention(e)),
    )
    return DashboardData(
        venue=repo.venue, serviceDate=date, summary=summary, entries=entries, tables=repo.tables
    )


def list_entries(
    repo: InMemoryRepository,
    *,
    status: str | None,
    party_size_class: str | None,
    review_required_only: bool | None,
    needs_attention_only: bool | None,
    service_date: str | None,
) -> list[WaitlistEntry]:
    date = service_date or repo.venue.serviceDate
    entries = [e for e in repo.entries if e.serviceDate == date]
    if status and status != "all":
        entries = [e for e in entries if e.status == status]
    if party_size_class and party_size_class != "all":
        entries = [e for e in entries if e.currentSeatingClass == party_size_class]
    if review_required_only:
        entries = [e for e in entries if e.reviewRequired]
    if needs_attention_only:
        entries = [e for e in entries if is_needs_attention(e)]
    return sort_entries(entries)


def create_guest_entry(
    repo: InMemoryRepository,
    payload: CreateGuestEntryRequest,
    notifier: NotificationProvider,
) -> CreateGuestEntryResult:
    venue = repo.venue
    if not venue.waitlistOpen:
        return CreateGuestEntryResultClosed(message=venue.messages.closedWaitlistMessage)

    if not payload.policyAcknowledged:
        raise ServiceError(
            400, "policy_not_acknowledged", "You must acknowledge the waitlist policy before joining."
        )
    if not payload.guestName.strip():
        raise ServiceError(400, "invalid_name", "Please enter a name for the party.")
    if payload.partySize < 1:
        raise ServiceError(400, "invalid_party_size", "Party size must be a whole number of one or more.")
    if not is_valid_mobile_number(payload.mobileNumber):
        raise ServiceError(
            400,
            "invalid_mobile_number",
            "Please enter a valid mobile number, for example +61 400 000 000.",
        )

    if payload.partySize > venue.maxOnlinePartySize:
        enquiry = large_party_service.create_enquiry(
            repo,
            LargePartyEnquiryRequest(
                guestName=payload.guestName.strip(),
                partySize=payload.partySize,
                mobileNumber=payload.mobileNumber.strip(),
                note=payload.seatingNote,
            ),
            notifier,
        )
        return CreateGuestEntryResultLargePartyEnquiry(
            enquiry=enquiry, message=venue.messages.largePartyConfirmationMessage
        )

    date = venue.serviceDate
    seq = repo.next_ticket_sequence(date)
    party_class = classify_party_size(payload.partySize)
    entry = WaitlistEntry(
        id=repo.next_id("entry"),
        venueId=venue.id,
        serviceDate=date,
        ticketCode=f"{party_class}-{seq:03d}",
        ticketSequence=seq,
        guestName=payload.guestName.strip(),
        partySize=payload.partySize,
        originalPartySize=payload.partySize,
        originalPartyClass=party_class,
        currentSeatingClass=party_class,
        reviewRequired=False,
        mobileNumber=payload.mobileNumber.strip(),
        seatingNote=payload.seatingNote.strip() if payload.seatingNote and payload.seatingNote.strip() else None,
        status="pending" if venue.entryMode == "staff_review" else "waiting",
        arrivalTime=now_iso(),
        estimatedWaitMinutes=venue.defaultWaitEstimateMinutes[party_class],
        accessToken=repo.next_access_token(),
    )
    repo.entries.append(entry)

    notification = Notification(
        id=repo.next_id("notif"),
        entryId=entry.id,
        recipientType="guest",
        channel="in_app",
        templateType="confirmation",
        renderedMessage=venue.messages.confirmationMessage,
        deliveryStatus="sent",
        createdAt=now_iso(),
        sentAt=now_iso(),
    )
    repo.notifications.append(notification)
    notifier.send(notification)

    return CreateGuestEntryResultEntry(
        entry=entry, accessToken=entry.accessToken, message=venue.messages.confirmationMessage
    )


def _guest_message(repo: InMemoryRepository, entry: WaitlistEntry) -> str:
    m = repo.venue.messages
    if entry.status == "notified":
        return m.tableReadyMessage
    if entry.status == "cancelled":
        return m.cancellationMessage
    if entry.status == "seated":
        return f"You're seated at {entry.tableName or 'your table'}. Enjoy your meal."
    if entry.status == "completed":
        return "Thanks for dining with us today."
    if entry.status == "no_show":
        return "We weren't able to seat this party. Please talk to the host stand."
    if entry.status == "pending":
        return "Your request is with our host stand for review."
    return m.confirmationMessage


def get_guest_entry(repo: InMemoryRepository, access_token: str) -> GuestStatus:
    entry = find_entry_by_token_or_404(repo, access_token)
    return GuestStatus(
        ticketCode=entry.ticketCode,
        guestName=entry.guestName,
        partySize=entry.partySize,
        status=entry.status,
        estimatedWaitMinutes=entry.estimatedWaitMinutes,
        message=_guest_message(repo, entry),
        notifiedAt=entry.notifiedAt,
        returnByAt=entry.returnByAt,
        needsAttention=is_needs_attention(entry),
        cancellationAllowed=entry.status in ACTIVE_CANCELLABLE_STATUSES,
        venueName=repo.venue.name,
        venueLogoPlaceholderLabel=repo.venue.logoPlaceholderLabel,
        serviceDate=entry.serviceDate,
    )


def cancel_guest_entry(
    repo: InMemoryRepository, access_token: str, notifier: NotificationProvider
) -> WaitlistEntry:
    entry = find_entry_by_token_or_404(repo, access_token)
    if entry.status not in ACTIVE_CANCELLABLE_STATUSES:
        raise ServiceError(
            400, "cancellation_not_allowed", "This entry can no longer be cancelled online."
        )
    entry.status = "cancelled"
    entry.cancelledAt = now_iso()
    notification = Notification(
        id=repo.next_id("notif"),
        entryId=entry.id,
        recipientType="staff",
        channel="in_app",
        templateType="cancellation",
        renderedMessage=f"{entry.ticketCode} ({entry.guestName}) cancelled their waitlist entry.",
        deliveryStatus="sent",
        createdAt=now_iso(),
        sentAt=now_iso(),
    )
    repo.notifications.append(notification)
    notifier.send(notification)
    return entry


def approve_entry(repo: InMemoryRepository, entry_id: str) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status != "pending":
        raise ServiceError(400, "invalid_status", "Only pending entries can be approved.")
    entry.status = "waiting"
    return entry


def cancel_entry(repo: InMemoryRepository, entry_id: str) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status in CLOSED_STATUSES:
        raise ServiceError(400, "invalid_status", "This entry is already closed.")
    _release_table(repo, entry)
    entry.status = "cancelled"
    entry.cancelledAt = now_iso()
    return entry


def notify_entry(
    repo: InMemoryRepository, entry_id: str, notifier: NotificationProvider
) -> tuple[WaitlistEntry, Notification]:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status not in {"waiting", "notified"}:
        raise ServiceError(400, "invalid_status", "Only waiting guests can be notified.")
    entry.status = "notified"
    entry.notifiedAt = now_iso()
    entry.returnByAt = iso_at_offset(repo.venue.gracePeriodMinutes)
    notification = Notification(
        id=repo.next_id("notif"),
        entryId=entry.id,
        recipientType="guest",
        channel="sms",
        templateType="table_ready",
        renderedMessage=repo.venue.messages.tableReadyMessage,
        deliveryStatus="sent",
        createdAt=now_iso(),
        sentAt=now_iso(),
    )
    repo.notifications.append(notification)
    notifier.send(notification)
    return entry, notification


def return_to_waiting(repo: InMemoryRepository, entry_id: str) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status != "notified":
        raise ServiceError(400, "invalid_status", "Only notified entries can return to waiting.")
    entry.status = "waiting"
    entry.notifiedAt = None
    entry.returnByAt = None
    return entry


def extend_return_by(repo: InMemoryRepository, entry_id: str, additional_minutes: int) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status != "notified" or entry.returnByAt is None:
        raise ServiceError(400, "invalid_status", "Only notified entries have a return-by time.")
    entry.returnByAt = (
        datetime.fromisoformat(entry.returnByAt) + timedelta(minutes=additional_minutes)
    ).isoformat()
    return entry


def update_wait_estimate(repo: InMemoryRepository, entry_id: str, estimated_wait_minutes: int) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if estimated_wait_minutes < 0:
        raise ServiceError(400, "invalid_estimate", "Estimated wait must be a whole number of minutes.")
    entry.estimatedWaitMinutes = estimated_wait_minutes
    return entry


def seat_entry(repo: InMemoryRepository, entry_id: str, payload: SeatEntryRequest) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status in {"cancelled", "no_show", "completed", "seated"}:
        raise ServiceError(400, "invalid_status", "This entry cannot be seated.")
    table = repo.find_table(payload.tableId)
    if table is None:
        raise ServiceError(404, "table_not_found", "That table does not exist.")
    if not table.active:
        raise ServiceError(400, "table_inactive", f"{table.name} is inactive.")
    if table.availabilityState == "occupied":
        raise ServiceError(400, "table_occupied", f"{table.name} is already occupied.")
    if table.availabilityState == "needs_tidying":
        raise ServiceError(
            400, "table_not_available", f"{table.name} needs tidying before it can be seated."
        )
    if table.maxCapacity < entry.partySize:
        raise ServiceError(
            400,
            "table_too_small",
            f"{table.name} seats up to {table.maxCapacity} and this party is {entry.partySize}.",
        )
    if table.minCapacity > entry.partySize:
        raise ServiceError(
            400,
            "table_capacity_mismatch",
            f"{table.name} seats a minimum of {table.minCapacity} and this party is {entry.partySize}.",
        )

    entry.status = "seated"
    entry.seatedAt = now_iso()
    entry.tableId = table.id
    entry.tableName = table.name
    entry.seatingOverrideReason = (
        payload.seatingOverrideReason.strip() if payload.seatingOverrideReason and payload.seatingOverrideReason.strip() else None
    )
    table.availabilityState = "occupied"
    table.occupyingEntryId = entry.id
    table.occupyingTicketCode = entry.ticketCode
    return entry


def mark_no_show(repo: InMemoryRepository, entry_id: str) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status != "notified":
        raise ServiceError(400, "invalid_status", "Only notified guests can be marked no-show.")
    entry.status = "no_show"
    return entry


def complete_entry(repo: InMemoryRepository, entry_id: str) -> WaitlistEntry:
    entry = find_entry_or_404(repo, entry_id)
    if entry.status != "seated":
        raise ServiceError(400, "invalid_status", "Only seated parties can be completed.")
    _release_table(repo, entry)
    entry.status = "completed"
    entry.completedAt = now_iso()
    return entry


def list_compatible_tables(repo: InMemoryRepository, entry_id: str) -> list[Table]:
    entry = find_entry_or_404(repo, entry_id)
    return [t for t in repo.tables if is_table_compatible(t, entry.partySize)]
