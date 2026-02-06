from datetime import date, timedelta
from decimal import Decimal

from app.crud import account as account_crud
from app.crud import user as user_crud
from app.schemas.account import AccountCreate
from app.schemas.user import UserCreate


def build_account_payload(account_number: str, buyer_name: str, status: str) -> AccountCreate:
    return AccountCreate(
        account_number=account_number,
        account_password="plain-account-pass",
        server="MetaTrader",
        buyer_name=buyer_name,
        buyer_email=f"{buyer_name.lower().replace(' ', '')}@example.com",
        buyer_phone="5511999999999",
        buyer_notes="notes",
        purchase_date=date.today(),
        expiry_date=date.today() + timedelta(days=30),
        purchase_price=Decimal("150.00"),
        status=status,
        max_copies=2,
        margin_size=Decimal("2500.00"),
        phase1_target=Decimal("500.00"),
        phase1_status="not_started",
        phase2_target=Decimal("700.00"),
        phase2_status=None
    )


def test_health_and_root_endpoints(client):
    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"

    root_response = client.get("/")
    assert root_response.status_code == 200
    assert root_response.json()["docs"] == "/docs"


def test_public_stats_endpoint_returns_aggregated_counts(client, db_session):
    admin = user_crud.create_user(
        db_session,
        UserCreate(
            username="admin",
            email="admin@example.com",
            password="strong-password",
            is_admin=True
        )
    )
    account_crud.create_account(
        db_session,
        build_account_payload("ACC-101", "Buyer 101", "pending"),
        admin.id
    )
    account_crud.create_account(
        db_session,
        build_account_payload("ACC-102", "Buyer 102", "approved"),
        admin.id
    )

    response = client.get("/api/public/stats")
    assert response.status_code == 200
    assert response.json() == {
        "total_accounts": 2,
        "pending": 1,
        "approved": 1,
        "in_copy": 0,
        "expired": 0,
        "suspended": 0
    }
