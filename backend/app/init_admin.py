"""
Script to create initial admin user on first run.
"""
from app.db.database import SessionLocal
from app.crud.user import get_user_by_username, create_user
from app.schemas.user import UserCreate
from app.config import get_settings


def init_admin():
    settings = get_settings()
    db = SessionLocal()

    try:
        # Check if admin already exists
        existing = get_user_by_username(db, settings.admin_username)
        if existing:
            print(f"Admin user '{settings.admin_username}' already exists")
            return

        # Create admin user
        admin = UserCreate(
            username=settings.admin_username,
            email=settings.admin_email,
            password=settings.admin_password,
            is_admin=True
        )
        create_user(db, admin)
        print(f"Admin user '{settings.admin_username}' created successfully!")

    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    init_admin()
