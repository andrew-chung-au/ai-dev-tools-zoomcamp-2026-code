from backend.errors import ServiceError
from backend.models import StaffSession
from backend.repository import InMemoryRepository
from backend.security import generate_token, verify_password
from backend.utils import now_iso


def login(repo: InMemoryRepository, username: str, password: str) -> StaffSession:
    if not username.strip() or not password.strip():
        raise ServiceError(401, "invalid_credentials", "Username and password are required.")

    user = next((u for u in repo.staff_users if u.username == username.strip()), None)
    if user is None or not user.active or not verify_password(password, user.passwordHash):
        raise ServiceError(401, "invalid_credentials", "Invalid username or password.")

    token = generate_token("session")
    session = StaffSession(
        token=token,
        staffName=user.staffName,
        username=user.username,
        venueId=repo.venue.id,
        issuedAt=now_iso(),
        mocked=True,
    )
    repo.sessions[token] = session
    return session


def get_session(repo: InMemoryRepository, token: str) -> StaffSession | None:
    return repo.sessions.get(token)
