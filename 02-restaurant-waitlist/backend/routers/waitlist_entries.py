from typing import Optional

from fastapi import APIRouter, Depends

from backend.deps import get_notifier, get_repository, require_staff
from backend.models import StaffSession, Table, WaitlistEntry
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.schemas import (
    CreateGuestEntryRequest,
    CreateGuestEntryResult,
    ExtendReturnByRequest,
    NotificationResult,
    SeatEntryRequest,
    UpdateWaitEstimateRequest,
)
from backend.services import waitlist_service

router = APIRouter(tags=["waitlist-entries"])


@router.get("/waitlist-entries", response_model=list[WaitlistEntry])
def list_waitlist_entries(
    status: Optional[str] = None,
    partySizeClass: Optional[str] = None,
    reviewRequiredOnly: Optional[bool] = None,
    needsAttentionOnly: Optional[bool] = None,
    serviceDate: Optional[str] = None,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.list_entries(
        repo,
        status=status,
        party_size_class=partySizeClass,
        review_required_only=reviewRequiredOnly,
        needs_attention_only=needsAttentionOnly,
        service_date=serviceDate,
    )


@router.post("/waitlist-entries", status_code=201, response_model=CreateGuestEntryResult)
def create_guest_entry(
    payload: CreateGuestEntryRequest,
    repo: InMemoryRepository = Depends(get_repository),
    notifier: NotificationProvider = Depends(get_notifier),
):
    return waitlist_service.create_guest_entry(repo, payload, notifier)


@router.post("/waitlist-entries/{entryId}/approve", response_model=WaitlistEntry)
def approve_entry(
    entryId: str,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.approve_entry(repo, entryId)


@router.post("/waitlist-entries/{entryId}/cancel", response_model=WaitlistEntry)
def cancel_entry(
    entryId: str,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.cancel_entry(repo, entryId)


@router.post("/waitlist-entries/{entryId}/notify", response_model=NotificationResult)
def notify_entry(
    entryId: str,
    repo: InMemoryRepository = Depends(get_repository),
    notifier: NotificationProvider = Depends(get_notifier),
    _staff: StaffSession = Depends(require_staff),
):
    entry, notification = waitlist_service.notify_entry(repo, entryId, notifier)
    return NotificationResult(entry=entry, notification=notification)


@router.post("/waitlist-entries/{entryId}/return-to-waiting", response_model=WaitlistEntry)
def return_to_waiting(
    entryId: str,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.return_to_waiting(repo, entryId)


@router.post("/waitlist-entries/{entryId}/extend-return-by", response_model=WaitlistEntry)
def extend_return_by(
    entryId: str,
    payload: ExtendReturnByRequest,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.extend_return_by(repo, entryId, payload.additionalMinutes)


@router.patch("/waitlist-entries/{entryId}/wait-estimate", response_model=WaitlistEntry)
def update_wait_estimate(
    entryId: str,
    payload: UpdateWaitEstimateRequest,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.update_wait_estimate(repo, entryId, payload.estimatedWaitMinutes)


@router.post("/waitlist-entries/{entryId}/seat", response_model=WaitlistEntry)
def seat_entry(
    entryId: str,
    payload: SeatEntryRequest,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.seat_entry(repo, entryId, payload)


@router.post("/waitlist-entries/{entryId}/no-show", response_model=WaitlistEntry)
def mark_no_show(
    entryId: str,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.mark_no_show(repo, entryId)


@router.post("/waitlist-entries/{entryId}/complete", response_model=WaitlistEntry)
def complete_entry(
    entryId: str,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.complete_entry(repo, entryId)


@router.get("/waitlist-entries/{entryId}/compatible-tables", response_model=list[Table])
def list_compatible_tables(
    entryId: str,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return waitlist_service.list_compatible_tables(repo, entryId)
