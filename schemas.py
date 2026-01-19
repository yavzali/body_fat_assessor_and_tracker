"""Pydantic schemas for request/response validation.

These schemas define the contracts between different layers of the application
and ensure type safety and validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from models import PhotoType, ConfidenceLevel, PhotoQuality


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    openai_subject: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserResponse(UserBase):
    """Schema for user responses."""
    id: str
    created_at: datetime
    last_analysis_at: Optional[datetime] = None
    total_analyses: int
    is_premium: bool
    
    model_config = {"from_attributes": True}


# ============================================================================
# Photo Schemas
# ============================================================================

class PhotoBase(BaseModel):
    """Base photo schema."""
    photo_type: PhotoType = PhotoType.FRONT


class PhotoUploadResponse(BaseModel):
    """Response after photo upload."""
    photo_id: str
    filename: str
    size: int
    faces_detected: int
    is_anonymized: bool
    message: str


class PhotoResponse(PhotoBase):
    """Schema for photo responses."""
    id: str
    user_id: str
    file_path: str
    original_filename: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    faces_detected: int
    is_anonymized: bool
    uploaded_at: datetime
    
    model_config = {"from_attributes": True}


# ============================================================================
# Analysis Schemas
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to analyze a photo."""
    user_id: str = Field(..., min_length=1)
    photo_id: str = Field(..., min_length=1)
    
    @field_validator('user_id', 'photo_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate that IDs are not empty."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()


class AIAnalysisResult(BaseModel):
    """Raw result from AI analysis."""
    body_fat_percentage: float = Field(..., ge=5.0, le=50.0)
    confidence: ConfidenceLevel
    reasoning: str = Field(..., min_length=10)
    photo_quality: PhotoQuality
    
    @field_validator('body_fat_percentage')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Validate body fat percentage is reasonable."""
        if not 5.0 <= v <= 50.0:
            raise ValueError("Body fat percentage must be between 5 and 50")
        return round(v, 1)


class AnalysisCreate(BaseModel):
    """Schema for creating an analysis record."""
    user_id: str
    photo_id: str
    body_fat_percentage: float
    confidence: ConfidenceLevel
    photo_quality: PhotoQuality
    reasoning: str
    ai_provider: str
    ai_model: str
    processing_time_ms: Optional[int] = None


class AnalysisResponse(BaseModel):
    """Schema for analysis responses."""
    id: str
    user_id: str
    photo_id: str
    body_fat_percentage: float
    confidence: ConfidenceLevel
    photo_quality: PhotoQuality
    reasoning: str
    ai_provider: str
    ai_model: str
    created_at: datetime
    processing_time_ms: Optional[int] = None
    
    model_config = {"from_attributes": True}


class AnalysisWithPhoto(AnalysisResponse):
    """Analysis response with photo information."""
    photo: PhotoResponse


# ============================================================================
# Widget State Schemas
# ============================================================================

class UploadWidgetState(BaseModel):
    """State for the upload widget."""
    user_id: str
    session_id: Optional[str] = None
    max_files: int = 1
    accepted_types: list[str] = [".jpg", ".jpeg", ".png", ".webp"]


class ResultsWidgetState(BaseModel):
    """State for the results widget."""
    analysis_id: str
    show_details: bool = True


class TimelineWidgetState(BaseModel):
    """State for the timeline widget (Phase 3)."""
    user_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 10


# ============================================================================
# MCP Tool Schemas
# ============================================================================

class ToolResponse(BaseModel):
    """Base schema for MCP tool responses."""
    content: list[dict]
    structuredContent: Optional[dict] = None
    _meta: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Historical Analysis Schemas (Phase 3)
# ============================================================================

class AnalysisHistory(BaseModel):
    """Schema for historical analysis data."""
    analyses: list[AnalysisResponse]
    total_count: int
    date_range: tuple[datetime, datetime]
    average_body_fat: float
    trend: str  # "increasing", "decreasing", "stable"


class ComparisonRequest(BaseModel):
    """Request to compare two analyses."""
    analysis_id_1: str
    analysis_id_2: str
    user_id: str


class ComparisonResponse(BaseModel):
    """Response for analysis comparison."""
    analysis_1: AnalysisWithPhoto
    analysis_2: AnalysisWithPhoto
    difference: float  # Percentage point difference
    time_between_days: int
    progress_direction: str  # "improvement", "regression", "stable"
