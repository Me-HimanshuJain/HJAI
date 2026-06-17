import uuid
from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from database.database import Base
import enum

class UserRole(str, enum.Enum):
    guest = "guest"
    user = "user"
    admin = "admin"

class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    banned = "banned"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user)
    status = Column(Enum(UserStatus), default=UserStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
