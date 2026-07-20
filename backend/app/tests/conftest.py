import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import model_registry  # noqa: F401
from app.database.base import Base
from app.database.session import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _fk_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class _FakeStorageBackend:
    """In-memory stand-in for S3StorageBackend so tests don't need real AWS creds."""

    def upload(self, file_obj, key, content_type):
        return f"https://test-bucket.s3.ap-south-1.amazonaws.com/{key}"

    def delete(self, key):
        pass


@pytest.fixture(autouse=True)
def fake_storage_backend(monkeypatch):
    fake = lambda: _FakeStorageBackend()  # noqa: E731
    monkeypatch.setattr("app.integrations.storage.get_storage_backend", fake)
    monkeypatch.setattr("app.modules.resources.service.get_storage_backend", fake)
    monkeypatch.setattr("app.modules.verification.service.get_storage_backend", fake)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def register_student(client):
    def _register(email="student1@example.com", password="Student123!"):
        resp = client.post(
            "/api/v1/auth/register/student",
            json={
                "full_name": "Test Student",
                "email": email,
                "password": password,
                "confirm_password": password,
                "school": "Test School",
                "grade": "A/L",
            },
        )
        return resp

    return _register


@pytest.fixture
def register_mentor(client):
    def _register(email="mentor1@example.com", password="Mentor123!"):
        resp = client.post(
            "/api/v1/auth/register/mentor",
            json={"full_name": "Test Mentor", "email": email, "password": password, "confirm_password": password},
        )
        return resp

    return _register
