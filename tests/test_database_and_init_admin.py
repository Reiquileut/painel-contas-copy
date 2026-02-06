from types import SimpleNamespace

import app.db.database as database_module
import app.init_admin as init_admin_module


def test_get_db_yields_session_and_closes(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    fake = FakeSession()
    monkeypatch.setattr(database_module, "SessionLocal", lambda: fake)

    gen = database_module.get_db()
    yielded = next(gen)
    assert yielded is fake

    try:
        next(gen)
    except StopIteration:
        pass

    assert fake.closed is True


def test_init_admin_when_user_exists(monkeypatch, capsys):
    events = {"closed": False}

    class FakeDb:
        def close(self):
            events["closed"] = True

    monkeypatch.setattr(
        init_admin_module,
        "get_settings",
        lambda: SimpleNamespace(
            admin_username="admin",
            admin_email="admin@example.com",
            admin_password="secret"
        )
    )
    monkeypatch.setattr(init_admin_module, "SessionLocal", lambda: FakeDb())
    monkeypatch.setattr(init_admin_module, "get_user_by_username", lambda db, username: object())
    monkeypatch.setattr(init_admin_module, "create_user", lambda db, admin: None)

    init_admin_module.init_admin()
    output = capsys.readouterr().out

    assert "already exists" in output
    assert events["closed"] is True


def test_init_admin_creates_user_successfully(monkeypatch, capsys):
    events = {"closed": False, "created": False}

    class FakeDb:
        def close(self):
            events["closed"] = True

    monkeypatch.setattr(
        init_admin_module,
        "get_settings",
        lambda: SimpleNamespace(
            admin_username="admin",
            admin_email="admin@example.com",
            admin_password="secret"
        )
    )
    monkeypatch.setattr(init_admin_module, "SessionLocal", lambda: FakeDb())
    monkeypatch.setattr(init_admin_module, "get_user_by_username", lambda db, username: None)
    monkeypatch.setattr(init_admin_module, "create_user", lambda db, admin: events.__setitem__("created", True))

    init_admin_module.init_admin()
    output = capsys.readouterr().out

    assert events["created"] is True
    assert events["closed"] is True
    assert "created successfully" in output


def test_init_admin_handles_exception(monkeypatch, capsys):
    events = {"closed": False}

    class FakeDb:
        def close(self):
            events["closed"] = True

    monkeypatch.setattr(
        init_admin_module,
        "get_settings",
        lambda: SimpleNamespace(
            admin_username="admin",
            admin_email="admin@example.com",
            admin_password="secret"
        )
    )
    monkeypatch.setattr(init_admin_module, "SessionLocal", lambda: FakeDb())
    monkeypatch.setattr(init_admin_module, "get_user_by_username", lambda db, username: None)

    def _raise_create(db, admin):
        raise RuntimeError("boom")

    monkeypatch.setattr(init_admin_module, "create_user", _raise_create)

    init_admin_module.init_admin()
    output = capsys.readouterr().out

    assert events["closed"] is True
    assert "Error creating admin user" in output
