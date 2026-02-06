from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.crud import account as account_crud
from app.crud import user as user_crud
from app.schemas.account import AccountCreate, AccountUpdate
from app.schemas.user import UserCreate


def build_account_payload(
    account_number: str,
    buyer_name: str,
    status: str = "pending",
    purchase_price: str = "100.00",
    purchase_date: Optional[date] = None
) -> AccountCreate:
    return AccountCreate(
        account_number=account_number,
        account_password="plain-account-pass",
        server="MetaTrader",
        buyer_name=buyer_name,
        buyer_email=f"{buyer_name.lower().replace(' ', '')}@example.com",
        buyer_phone="5511999999999",
        buyer_notes="notes",
        purchase_date=purchase_date or date.today(),
        expiry_date=date.today() + timedelta(days=30),
        purchase_price=Decimal(purchase_price),
        status=status,
        max_copies=2,
        margin_size=Decimal("2500.00"),
        phase1_target=Decimal("500.00"),
        phase1_status="not_started",
        phase2_target=Decimal("700.00"),
        phase2_status=None
    )


def create_admin_user(db_session):
    return user_crud.create_user(
        db_session,
        UserCreate(
            username="admin",
            email="admin@example.com",
            password="strong-password",
            is_admin=True
        )
    )


def test_account_crud_full_flow(db_session):
    admin = create_admin_user(db_session)
    created = account_crud.create_account(
        db_session,
        build_account_payload("ACC-001", "Alice"),
        admin.id
    )

    assert created.id is not None
    assert created.account_password != "plain-account-pass"

    by_id = account_crud.get_account(db_session, created.id)
    by_number = account_crud.get_account_by_number(db_session, "ACC-001")
    assert by_id is not None
    assert by_number is not None

    updated = account_crud.update_account(
        db_session,
        created.id,
        AccountUpdate(
            account_password="new-account-pass",
            buyer_name="Alice Updated"
        )
    )
    assert updated is not None
    assert updated.buyer_name == "Alice Updated"
    assert updated.account_password != "new-account-pass"

    decrypted = account_crud.decrypt_account_for_response(updated)
    assert decrypted["account_password"] == "new-account-pass"

    changed_status = account_crud.update_account_status(
        db_session,
        created.id,
        "approved"
    )
    assert changed_status is not None
    assert changed_status.status == "approved"

    assert account_crud.update_account(db_session, 999999, AccountUpdate(status="expired")) is None
    assert account_crud.update_account_status(db_session, 999999, "expired") is None

    assert account_crud.delete_account(db_session, created.id) is True
    assert account_crud.delete_account(db_session, created.id) is False


def test_get_accounts_filters_stats_and_admin_stats(db_session):
    admin = create_admin_user(db_session)
    previous_month_day = date.today().replace(day=1) - timedelta(days=1)

    account_crud.create_account(
        db_session,
        build_account_payload("ACC-PEND", "Buyer Pending", "pending", "100.00"),
        admin.id
    )
    account_crud.create_account(
        db_session,
        build_account_payload("ACC-APPR", "Buyer Approved", "approved", "200.00"),
        admin.id
    )
    account_crud.create_account(
        db_session,
        build_account_payload("ACC-COPY", "Buyer Copy", "in_copy", "300.00"),
        admin.id
    )
    account_crud.create_account(
        db_session,
        build_account_payload("ACC-EXPR", "Buyer Expired", "expired", "400.00"),
        admin.id
    )
    account_crud.create_account(
        db_session,
        build_account_payload(
            "ACC-SUSP",
            "Buyer Suspended",
            "suspended",
            "500.00",
            purchase_date=previous_month_day
        ),
        admin.id
    )

    approved_accounts = account_crud.get_accounts(db_session, status="approved")
    assert len(approved_accounts) == 1
    assert approved_accounts[0].account_number == "ACC-APPR"

    searched_accounts = account_crud.get_accounts(db_session, search="Suspended")
    assert len(searched_accounts) == 1
    assert searched_accounts[0].account_number == "ACC-SUSP"

    stats = account_crud.get_stats(db_session)
    assert stats == {
        "total_accounts": 5,
        "pending": 1,
        "approved": 1,
        "in_copy": 1,
        "expired": 1,
        "suspended": 1
    }

    admin_stats = account_crud.get_admin_stats(db_session)
    assert admin_stats["total_revenue"] == Decimal("1500.00")
    assert admin_stats["accounts_this_month"] == 4
