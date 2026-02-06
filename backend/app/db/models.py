from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date,
    Numeric, Text, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship
    accounts_created = relationship(
        "CopyTradeAccount",
        back_populates="created_by_user"
    )
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    security_logs = relationship("SecurityAuditLog", back_populates="user")


class CopyTradeAccount(Base):
    __tablename__ = "copy_trade_accounts"

    id = Column(Integer, primary_key=True, index=True)

    # Account credentials (sensitive)
    account_number = Column(String(50), unique=True, nullable=False, index=True)
    account_password = Column(String(255), nullable=False)  # Encrypted
    server = Column(String(100), nullable=False)

    # Buyer information (sensitive)
    buyer_name = Column(String(100), nullable=False)
    buyer_email = Column(String(100))
    buyer_phone = Column(String(20))
    buyer_notes = Column(Text)

    # Purchase information
    purchase_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    purchase_price = Column(Numeric(10, 2))

    # Status tracking
    status = Column(String(20), nullable=False, default="pending", index=True)

    # Copy tracking
    copy_count = Column(Integer, default=0)
    max_copies = Column(Integer, default=1)

    # Proprietary trading (Mesa Proprietaria)
    margin_size = Column(Numeric(12, 2))
    phase1_target = Column(Numeric(12, 2))
    phase1_status = Column(String(20), default="not_started")
    phase2_target = Column(Numeric(12, 2))
    phase2_status = Column(String(20))  # null = sem fase 2

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationship
    created_by_user = relationship("User", back_populates="accounts_created")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'in_copy', 'expired', 'suspended')",
            name="valid_status"
        ),
        CheckConstraint(
            "phase1_status IS NULL OR phase1_status IN ('not_started', 'in_progress', 'passed', 'failed')",
            name="valid_phase1_status"
        ),
        CheckConstraint(
            "phase2_status IS NULL OR phase2_status IN ('not_started', 'in_progress', 'passed', 'failed')",
            name="valid_phase2_status"
        ),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    csrf_token = Column(String(128), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_ip = Column(String(64), nullable=True)
    created_user_agent = Column(String(255), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    target_type = Column(String(64), nullable=True, index=True)
    target_id = Column(String(64), nullable=True, index=True)
    success = Column(Boolean, nullable=False, default=False, index=True)
    reason = Column(Text, nullable=True)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="security_logs")
