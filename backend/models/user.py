import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    google_id = Column(String(255), unique=True, nullable=True)
    mode = Column(String(20), nullable=False, default="demo")

    kis_paper_key_enc = Column(Text, nullable=True)
    kis_paper_secret_enc = Column(Text, nullable=True)
    kis_paper_account_no = Column(String(20), nullable=True)
    kis_real_key_enc = Column(Text, nullable=True)
    kis_real_secret_enc = Column(Text, nullable=True)
    kis_real_account_no = Column(String(20), nullable=True)

    dark_mode = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("mode IN ('demo', 'paper', 'real')", name="ck_users_mode"),
    )

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_refresh_tokens_user_active", "user_id", "revoked", "expires_at"),
    )

    user = relationship("User", back_populates="refresh_tokens")
