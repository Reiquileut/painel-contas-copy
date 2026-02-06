import asyncio

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user, require_admin
from app.core.security import create_access_token
from app.crud import user as user_crud
from app.schemas.user import UserCreate


def _run(coro):
    return asyncio.run(coro)


def create_user(db_session, username: str, is_admin: bool = False, is_active: bool = True):
    user = user_crud.create_user(
        db_session,
        UserCreate(
            username=username,
            email=f"{username}@example.com",
            password="strong-password",
            is_admin=is_admin
        )
    )
    user.is_active = is_active
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_success(db_session):
    user = create_user(db_session, "john", is_admin=False, is_active=True)
    token = create_access_token({"sub": user.username})
    current = _run(get_current_user(credentials=auth_credentials(token), db=db_session))
    assert current.username == "john"


def test_get_current_user_invalid_token(db_session):
    with pytest.raises(HTTPException) as exc:
        _run(get_current_user(credentials=auth_credentials("invalid-token"), db=db_session))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Token invalido ou expirado"


def test_get_current_user_token_without_sub(db_session):
    token = create_access_token({"foo": "bar"})
    with pytest.raises(HTTPException) as exc:
        _run(get_current_user(credentials=auth_credentials(token), db=db_session))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Token invalido"


def test_get_current_user_user_not_found(db_session):
    token = create_access_token({"sub": "ghost"})
    with pytest.raises(HTTPException) as exc:
        _run(get_current_user(credentials=auth_credentials(token), db=db_session))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Usuario nao encontrado"


def test_get_current_user_inactive_user(db_session):
    user = create_user(db_session, "inactive", is_active=False)
    token = create_access_token({"sub": user.username})
    with pytest.raises(HTTPException) as exc:
        _run(get_current_user(credentials=auth_credentials(token), db=db_session))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Usuario inativo"


def test_require_admin_success_and_forbidden(db_session):
    admin = create_user(db_session, "admin-user", is_admin=True)
    basic = create_user(db_session, "basic-user", is_admin=False)

    allowed = _run(require_admin(current_user=admin))
    assert allowed.username == "admin-user"

    with pytest.raises(HTTPException) as exc:
        _run(require_admin(current_user=basic))
    assert exc.value.status_code == 403
    assert exc.value.detail == "Acesso restrito a administradores"
