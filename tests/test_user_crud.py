from app.crud import user as user_crud
from app.schemas.user import UserCreate


def test_create_and_authenticate_user(db_session):
    created_user = user_crud.create_user(
        db_session,
        UserCreate(
            username="admin",
            email="admin@example.com",
            password="strong-password",
            is_admin=True
        )
    )

    assert created_user.id is not None
    assert created_user.hashed_password != "strong-password"
    assert created_user.is_admin is True

    assert user_crud.get_user_by_username(db_session, "admin") is not None
    assert user_crud.get_user_by_email(db_session, "admin@example.com") is not None

    authenticated = user_crud.authenticate_user(
        db_session,
        "admin",
        "strong-password"
    )
    assert authenticated is not None
    assert authenticated.username == "admin"

    assert user_crud.authenticate_user(db_session, "admin", "wrong-password") is None
    assert user_crud.authenticate_user(db_session, "missing-user", "any-password") is None
