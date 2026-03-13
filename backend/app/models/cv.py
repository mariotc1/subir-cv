"""
Modelo de CV.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CV(Base):
    __tablename__ = "cvs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Un usuario solo puede tener un CV
        index=True
    )
    filename = Column(
        String(255),
        nullable=False
    )
    original_filename = Column(
        String(255),
        nullable=False
    )
    storage_path = Column(
        String(512),
        nullable=False
    )
    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relación con Usuario
    user = relationship("User", back_populates="cv")

    def __repr__(self):
        return f"<CV {self.id} - User {self.user_id}>"
