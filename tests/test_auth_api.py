from app.crud import user as user_crud
from app.schemas.user import UserCreate


def create_admin(db_session, username: str = "admin"):
    return user_crud.create_user(
        db_session,
        UserCreate(
            username=username,
            email=f"{username}@example.com",
            password="strong-password",
            is_admin=True
        )
    )


def login(client, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_success_and_invalid_credentials(client, db_session):
    create_admin(db_session)

    ok = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "strong-password"}
    )
    assert ok.status_code == 200
    assert ok.json()["token_type"] == "bearer"
    assert "access_token" in ok.json()

    invalid = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"}
    )
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Usuario ou senha incorretos"


def test_me_and_logout_endpoints(client, db_session):
    create_admin(db_session)
    token = login(client, "admin", "strong-password")
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["is_admin"] is True

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json()["message"] == "Logout realizado com sucesso"
