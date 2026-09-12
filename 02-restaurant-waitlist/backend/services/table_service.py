from backend.errors import ServiceError
from backend.models import Table
from backend.repository import InMemoryRepository
from backend.schemas import CreateTableRequest, SetTableAvailabilityRequest, UpdateTableRequest


def list_tables(repo: InMemoryRepository) -> list[Table]:
    return repo.tables


def find_table_or_404(repo: InMemoryRepository, table_id: str) -> Table:
    table = repo.find_table(table_id)
    if table is None:
        raise ServiceError(404, "table_not_found", "That table does not exist.")
    return table


def create_table(repo: InMemoryRepository, payload: CreateTableRequest) -> Table:
    if not payload.name.strip():
        raise ServiceError(400, "invalid_name", "Table name is required.")
    if payload.minCapacity < 1:
        raise ServiceError(
            400, "invalid_min_capacity", "Minimum capacity must be a whole number of one or more."
        )
    if payload.maxCapacity < payload.minCapacity:
        raise ServiceError(
            400,
            "invalid_max_capacity",
            "Maximum capacity must be a whole number at least as large as the minimum capacity.",
        )
    table = Table(
        id=repo.next_id("tbl"),
        name=payload.name.strip(),
        minCapacity=payload.minCapacity,
        maxCapacity=payload.maxCapacity,
        active=True,
        availabilityState="available",
        notes=payload.notes.strip() if payload.notes and payload.notes.strip() else None,
    )
    repo.tables.append(table)
    return table


def update_table(repo: InMemoryRepository, table_id: str, payload: UpdateTableRequest) -> Table:
    table = find_table_or_404(repo, table_id)
    fields = payload.model_fields_set

    next_min = payload.minCapacity if payload.minCapacity is not None else table.minCapacity
    next_max = payload.maxCapacity if payload.maxCapacity is not None else table.maxCapacity

    if "name" in fields:
        if payload.name is None or not payload.name.strip():
            raise ServiceError(400, "invalid_name", "Table name is required.")
        table.name = payload.name.strip()

    if "minCapacity" in fields or "maxCapacity" in fields:
        if next_min < 1:
            raise ServiceError(
                400, "invalid_min_capacity", "Minimum capacity must be a whole number of one or more."
            )
        if next_max < next_min:
            raise ServiceError(
                400,
                "invalid_max_capacity",
                "Maximum capacity must be a whole number at least as large as the minimum capacity.",
            )
        table.minCapacity = next_min
        table.maxCapacity = next_max

    if "active" in fields and payload.active is not None:
        table.active = payload.active

    if "notes" in fields:
        table.notes = payload.notes.strip() if payload.notes and payload.notes.strip() else None

    return table


def delete_table(repo: InMemoryRepository, table_id: str) -> None:
    table = find_table_or_404(repo, table_id)
    if table.availabilityState == "occupied":
        raise ServiceError(
            400, "table_occupied", f"{table.name} is currently occupied and cannot be deleted."
        )
    repo.tables = [t for t in repo.tables if t.id != table_id]


def set_table_availability(
    repo: InMemoryRepository, table_id: str, payload: SetTableAvailabilityRequest
) -> Table:
    table = find_table_or_404(repo, table_id)
    if payload.availabilityState == "available" and table.availabilityState != "needs_tidying":
        raise ServiceError(
            400,
            "invalid_availability_transition",
            f"{table.name} can only be marked available from needs_tidying.",
        )
    if payload.availabilityState == "needs_tidying" and table.availabilityState == "occupied":
        table.occupyingEntryId = None
        table.occupyingTicketCode = None
    table.availabilityState = payload.availabilityState
    return table
