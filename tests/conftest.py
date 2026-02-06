import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault(
    "ENCRYPTION_KEY",
    "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-with-minimum-32-characters"
)
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("V1_DEPRECATION_START", "2099-01-01T00:00:00+00:00")

ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.db.database import Base, get_db  # noqa: E402
from app.db import models  # noqa: F401,E402
from app.main import app  # noqa: E402

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE
)


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
