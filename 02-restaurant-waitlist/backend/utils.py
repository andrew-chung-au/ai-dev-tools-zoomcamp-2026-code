import re
from datetime import datetime, timedelta, timezone

from backend.models import PartySizeClass, Table, WaitlistEntry, WaitlistStatus

MOBILE_PATTERN = re.compile(r"^\+?[0-9][0-9\s\-]{6,17}$")

STATUS_RANK: dict[WaitlistStatus, int] = {
    "notified": 0,
    "pending": 1,
    "waiting": 2,
    "seated": 3,
    "completed": 4,
    "no_show": 5,
    "cancelled": 6,
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


def iso_at_offset(minutes: float) -> str:
    return (now_utc() + timedelta(minutes=minutes)).isoformat()


def today_iso() -> str:
    return now_utc().date().isoformat()


def classify_party_size(party_size: int) -> PartySizeClass:
    if party_size <= 2:
        return "A"
    if party_size <= 4:
        return "B"
    if party_size <= 6:
        return "C"
    return "D"


def is_valid_mobile_number(mobile_number: str) -> bool:
    return bool(MOBILE_PATTERN.match(mobile_number.strip()))


def is_needs_attention(entry: WaitlistEntry, now: datetime | None = None) -> bool:
    if entry.status != "notified" or entry.returnByAt is None:
        return False
    reference = now or now_utc()
    return datetime.fromisoformat(entry.returnByAt) < reference


def sort_entries(entries: list[WaitlistEntry]) -> list[WaitlistEntry]:
    return sorted(
        entries,
        key=lambda e: (
            STATUS_RANK[e.status],
            e.currentSeatingClass,
            e.arrivalTime,
        ),
    )


def is_table_compatible(table: Table, party_size: int) -> bool:
    return (
        table.active
        and table.availabilityState == "available"
        and table.minCapacity <= party_size <= table.maxCapacity
    )
