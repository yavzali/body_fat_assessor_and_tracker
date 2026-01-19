"""Database models.

All SQLAlchemy models are defined here to maintain a single source of truth
for the database schema.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class PhotoType(str, enum.Enum):
    """Types of photos users can upload."""
    FRONT = "front"
    SIDE = "side"
    BACK = "back"
    OTHER = "other"


class ConfidenceLevel(str, enum.Enum):
    """Confidence levels for AI analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PhotoQuality(str, enum.Enum):
    """Photo quality assessment."""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class User(Base):
    """User model.
    
    Represents a user identified by their OpenAI subject ID.
    Stores minimal information for privacy.
    """
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    openai_subject: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    last_analysis_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    total_analyses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    is_premium: Mapped[bool] = mapped_column(
        Integer,  # SQLite doesn't have boolean
        default=0,
        nullable=False,
    )
    
    # Relationships
    photos: Mapped[list["Photo"]] = relationship(
        "Photo",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, openai_subject={self.openai_subject[:8]}...)>"


class Photo(Base):
    """Photo model.
    
    Stores uploaded photos with face anonymization applied.
    """
    
    __tablename__ = "photos"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    photo_type: Mapped[PhotoType] = mapped_column(
        SQLEnum(PhotoType),
        default=PhotoType.FRONT,
        nullable=False,
    )
    
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    faces_detected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    is_anonymized: Mapped[bool] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="photos")
    analysis: Mapped[Optional["Analysis"]] = relationship(
        "Analysis",
        back_populates="photo",
    )
    
    def __repr__(self) -> str:
        return f"<Photo(id={self.id}, user_id={self.user_id}, type={self.photo_type})>"


class Analysis(Base):
    """Analysis model.
    
    Stores AI-generated body composition analysis results.
    """
    
    __tablename__ = "analyses"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    
    photo_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("photos.id"),
        nullable=False,
        unique=True,  # One analysis per photo
    )
    
    body_fat_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        SQLEnum(ConfidenceLevel),
        nullable=False,
    )
    
    photo_quality: Mapped[PhotoQuality] = mapped_column(
        SQLEnum(PhotoQuality),
        nullable=False,
    )
    
    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    ai_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    ai_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="analyses")
    photo: Mapped["Photo"] = relationship("Photo", back_populates="analysis")
    
    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, bf%={self.body_fat_percentage}, confidence={self.confidence})>"
