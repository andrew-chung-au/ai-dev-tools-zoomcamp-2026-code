from fastapi import APIRouter, Depends, Response

from backend.deps import get_repository, require_staff
from backend.models import StaffSession, Table
from backend.repository import InMemoryRepository
from backend.schemas import CreateTableRequest, SetTableAvailabilityRequest, UpdateTableRequest
from backend.services import table_service

router = APIRouter(tags=["tables"])


@router.get("/tables", response_model=list[Table])
def list_tables(
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return table_service.list_tables(repo)


@router.post("/tables", status_code=201, response_model=Table)
def create_table(
    payload: CreateTableRequest,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return table_service.create_table(repo, payload)


@router.patch("/tables/{tableId}", response_model=Table)
def update_table(
    tableId: str,
    payload: UpdateTableRequest,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return table_service.update_table(repo, tableId, payload)


@router.delete("/tables/{tableId}", status_code=204)
def delete_table(
    tableId: str,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    table_service.delete_table(repo, tableId)
    return Response(status_code=204)


@router.patch("/tables/{tableId}/availability", response_model=Table)
def set_table_availability(
    tableId: str,
    payload: SetTableAvailabilityRequest,
    repo: InMemoryRepository = Depends(get_repository),
    _staff: StaffSession = Depends(require_staff),
):
    return table_service.set_table_availability(repo, tableId, payload)
