from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("CLERK_JWKS_URL", "https://example.test/.well-known/jwks.json")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("CIVICSENSE_ALLOW_FAKE_ADAPTERS", "true")

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_current_user, get_db, get_optional_user
from app.core.security import ClerkUser
from app.db.base import Base
from app.main import app
from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel
from app.models.category import Category
from app.models.city import City, CityStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.models.submission import SubmissionConsent


@compiles(PGUUID, "sqlite")
def _compile_uuid_sqlite(type_, compiler, **kw):  # noqa: ARG001
    return "CHAR(36)"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):  # noqa: ARG001
    return "JSON"


def _sqlite_url() -> str:
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def engine():
    url = _sqlite_url()
    if not url.startswith("sqlite"):
        pytest.skip("Set TEST_DATABASE_URL=sqlite:///:memory: for default DB tests")

    eng = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _sqlite_pragma(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def city(db: Session) -> City:
    row = City(
        slug="pune",
        name="Pune",
        state_name="Maharashtra",
        center_lat=18.5204,
        center_lng=73.8567,
        status=CityStatus.ACTIVE,
        supports_reporting=True,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def category(db: Session) -> Category:
    row = Category(name="Roads", slug="roads", is_active=True)
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def sensitive_complaint(db: Session, city: City, category: Category) -> Complaint:
    row = Complaint(
        user_id="user_owner",
        title="Sensitive corruption report",
        description="Confidential details about bribery",
        status=ComplaintStatus.SUBMITTED,
        category_id=category.id,
        address="Hidden location, Pune",
        city="Pune",
        city_id=city.id,
        is_sensitive=True,
        public_caption="Sensitive civic issue in Pune",
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def complaint(db: Session, city: City, category: Category) -> Complaint:
    row = Complaint(
        user_id="user_owner",
        title="Pothole on FC Road",
        description="Large pothole causing traffic issues",
        status=ComplaintStatus.SUBMITTED,
        category_id=category.id,
        address="FC Road, Pune",
        city="Pune",
        city_id=city.id,
        is_sensitive=False,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def test_channel(db: Session, city: City) -> ExternalChannel:
    row = ExternalChannel(
        city_id=city.id,
        channel_type="email",
        destination="grievance@example.test",
        mode=ChannelMode.EMAIL,
        activation=ChannelActivation.TEST_ONLY,
        on_behalf_policy="allowed",
        enabled=False,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def consent(db: Session, complaint: Complaint, test_channel: ExternalChannel) -> SubmissionConsent:
    import json

    row = SubmissionConsent(
        complaint_id=complaint.id,
        user_id=complaint.user_id,
        channel_id=test_channel.id,
        payload_hash="abc123",
        disclosure_json=json.dumps({"summary": "Test complaint"}),
        version="1",
        authorized_at=datetime.now(UTC),
        scope="single_dispatch",
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def api_client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def set_api_user(api_client: TestClient) -> Generator[Callable[[ClerkUser | None], None], None, None]:
    del api_client

    def _set(user: ClerkUser | None) -> None:
        if user is None:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides[get_optional_user] = lambda: None
            return

        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_optional_user] = lambda: user

    yield _set
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_optional_user, None)
