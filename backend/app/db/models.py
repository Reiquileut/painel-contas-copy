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
    )
