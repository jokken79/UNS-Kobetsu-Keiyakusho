"""
Pytest configuration and fixtures for backend tests.
"""
import pytest
from datetime import date, time
from decimal import Decimal
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token


# Test database URL (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """Create authentication headers for test requests."""
    token = create_access_token({
        "sub": 1,
        "email": "test@example.com",
        "role": "admin",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_contract_data() -> dict:
    """Sample contract data for testing."""
    return {
        "factory_id": 1,
        "employee_ids": [1, 2],
        "contract_date": str(date.today()),
        "dispatch_start_date": "2024-12-01",
        "dispatch_end_date": "2025-11-30",
        "work_content": "製造ライン作業、検品、梱包業務の補助作業",
        "responsibility_level": "通常業務",
        "worksite_name": "テスト株式会社 本社工場",
        "worksite_address": "東京都千代田区丸の内1-1-1",
        "organizational_unit": "第1製造部",
        "supervisor_department": "製造部",
        "supervisor_position": "課長",
        "supervisor_name": "田中太郎",
        "work_days": ["月", "火", "水", "木", "金"],
        "work_start_time": "08:00",
        "work_end_time": "17:00",
        "break_time_minutes": 60,
        "overtime_max_hours_day": 3,
        "overtime_max_hours_month": 45,
        "hourly_rate": 1500,
        "overtime_rate": 1875,
        "haken_moto_complaint_contact": {
            "department": "人事部",
            "position": "課長",
            "name": "山田花子",
            "phone": "03-1234-5678",
        },
        "haken_saki_complaint_contact": {
            "department": "総務部",
            "position": "係長",
            "name": "佐藤次郎",
            "phone": "03-9876-5432",
        },
        "haken_moto_manager": {
            "department": "派遣事業部",
            "position": "部長",
            "name": "鈴木一郎",
            "phone": "03-1234-5678",
        },
        "haken_saki_manager": {
            "department": "人事部",
            "position": "部長",
            "name": "高橋三郎",
            "phone": "03-9876-5432",
        },
    }


@pytest.fixture
def sample_update_data() -> dict:
    """Sample update data for testing."""
    return {
        "work_content": "更新された業務内容です。新しい作業が追加されました。",
        "hourly_rate": 1600,
        "notes": "テスト更新",
    }
