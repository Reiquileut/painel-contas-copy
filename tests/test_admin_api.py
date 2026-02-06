from datetime import date, timedelta
from decimal import Decimal

import app.api.accounts as accounts_api
from app.crud import user as user_crud
from app.db.models import User
from app.main import app
from app.schemas.account import AccountCreate
from app.schemas.user import UserCreate


def build_account_payload(account_number: str, buyer_name: str, status: str = "pending") -> dict:
    return {
        "account_number": account_number,
        "account_password": "plain-account-pass",
        "server": "MetaTrader",
        "buyer_name": buyer_name,
        "buyer_email": f"{buyer_name.lower().replace(' ', '')}@example.com",
        "buyer_phone": "5511999999999",
        "buyer_notes": "notes",
        "purchase_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=30)),
        "purchase_price": "150.00",
        "status": status,
        "max_copies": 2,
        "margin_size": "2500.00",
        "phase1_target": "500.00",
        "phase1_status": "not_started",
        "phase2_target": "700.00",
        "phase2_status": None
    }


def create_admin_user(db_session, username: str = "admin") -> User:
    return user_crud.create_user(
        db_session,
        UserCreate(
            username=username,
            email=f"{username}@example.com",
            password="strong-password",
            is_admin=True
        )
    )


def create_non_admin_user(db_session, username: str = "basic") -> User:
    return user_crud.create_user(
        db_session,
        UserCreate(
            username=username,
            email=f"{username}@example.com",
            password="strong-password",
            is_admin=False
        )
    )


def test_admin_accounts_full_flow_with_errors(client, db_session):
    admin = create_admin_user(db_session)
    app.dependency_overrides[accounts_api.require_admin] = lambda: admin
    try:
        list_empty = client.get("/api/admin/accounts")
        assert list_empty.status_code == 200
        assert list_empty.json() == []

        create_resp = client.post(
            "/api/admin/accounts",
            json=build_account_payload("ACC-200", "Buyer One")
        )
        assert create_resp.status_code == 201
        account_id = create_resp.json()["id"]

        duplicate = client.post(
            "/api/admin/accounts",
            json=build_account_payload("ACC-200", "Buyer Dup")
        )
        assert duplicate.status_code == 400
        assert duplicate.json()["detail"] == "Numero da conta ja existe"

        detail_ok = client.get(f"/api/admin/accounts/{account_id}")
        assert detail_ok.status_code == 200
        assert detail_ok.json()["account_number"] == "ACC-200"

        detail_missing = client.get("/api/admin/accounts/9999")
        assert detail_missing.status_code == 404

        create_second = client.post(
            "/api/admin/accounts",
            json=build_account_payload("ACC-201", "Buyer Two")
        )
        assert create_second.status_code == 201
        second_id = create_second.json()["id"]

        update_conflict = client.put(
            f"/api/admin/accounts/{second_id}",
            json={"account_number": "ACC-200"}
        )
        assert update_conflict.status_code == 400
        assert update_conflict.json()["detail"] == "Numero da conta ja existe"

        update_ok = client.put(
            f"/api/admin/accounts/{account_id}",
            json={"buyer_name": "Buyer Updated", "account_password": "new-pass"}
        )
        assert update_ok.status_code == 200
        assert update_ok.json()["buyer_name"] == "Buyer Updated"
        assert update_ok.json()["account_password"] == "********"

        update_missing = client.put(
            "/api/admin/accounts/9999",
            json={"buyer_name": "Nobody"}
        )
        assert update_missing.status_code == 404

        invalid_status = client.patch(
            f"/api/admin/accounts/{account_id}/status",
            json={"status": "invalid_status"}
        )
        assert invalid_status.status_code == 400

        status_missing = client.patch(
            "/api/admin/accounts/9999/status",
            json={"status": "approved"}
        )
        assert status_missing.status_code == 404

        status_ok = client.patch(
            f"/api/admin/accounts/{account_id}/status",
            json={"status": "approved"}
        )
        assert status_ok.status_code == 200
        assert status_ok.json()["status"] == "approved"

        searched = client.get("/api/admin/accounts?search=Updated")
        assert searched.status_code == 200
        assert len(searched.json()) == 1

        filtered = client.get("/api/admin/accounts?status=approved")
        assert filtered.status_code == 200
        assert len(filtered.json()) == 1

        stats = client.get("/api/admin/stats")
        assert stats.status_code == 200
        assert stats.json()["total_accounts"] == 2
        assert Decimal(stats.json()["total_revenue"]) == Decimal("300.00")

        delete_ok = client.delete(f"/api/admin/accounts/{second_id}")
        assert delete_ok.status_code == 204

        delete_missing = client.delete("/api/admin/accounts/9999")
        assert delete_missing.status_code == 404
    finally:
        app.dependency_overrides.pop(accounts_api.require_admin, None)


def test_admin_endpoint_without_override_uses_auth_guard(client, db_session):
    create_non_admin_user(db_session)
    response = client.get("/api/admin/accounts")
    assert response.status_code == 403
