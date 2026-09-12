from fastapi import APIRouter, Depends

from backend.deps import get_notifier, get_repository
from backend.models import LargePartyEnquiry
from backend.notifications import NotificationProvider
from backend.repository import InMemoryRepository
from backend.schemas import LargePartyEnquiryRequest
from backend.services import large_party_service

router = APIRouter(tags=["large-party-enquiries"])


@router.post("/large-party-enquiries", status_code=201, response_model=LargePartyEnquiry)
def create_large_party_enquiry(
    payload: LargePartyEnquiryRequest,
    repo: InMemoryRepository = Depends(get_repository),
    notifier: NotificationProvider = Depends(get_notifier),
):
    return large_party_service.create_enquiry(repo, payload, notifier)
