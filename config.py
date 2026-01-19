"""Application configuration and settings.

This module centralizes all configuration including environment variables,
constants, and application settings.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Body Composition Tracker"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./bodyfat_tracker.db"
    
    # Storage
    upload_dir: Path = Path("./uploads")
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    
    # AI Configuration
    ai_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_model: str = "gpt-4o"  # GPT-4 with vision
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    ai_max_tokens: int = 1000
    ai_temperature: float = 0.7
    
    # Image Processing
    face_blur_radius: int = 30
    image_quality: int = 85
    max_image_dimension: int = 2048
    
    # Rate Limiting (Future)
    rate_limit_free: int = 1  # analyses per week
    rate_limit_premium: int = 999  # effectively unlimited
    
    # Data Retention
    data_retention_days: int = 30
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    # MCP
    mcp_server_name: str = "bodyfat-tracker"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


# Constants
class ErrorMessages:
    """Centralized error messages."""
    
    INVALID_IMAGE_FORMAT = "Invalid image format. Allowed: JPG, PNG, WEBP"
    IMAGE_TOO_LARGE = f"Image exceeds maximum size of {settings.max_upload_size / 1024 / 1024}MB"
    USER_NOT_FOUND = "User not found"
    PHOTO_NOT_FOUND = "Photo not found"
    ANALYSIS_NOT_FOUND = "Analysis not found"
    UPLOAD_FAILED = "Failed to upload image"
    PROCESSING_FAILED = "Failed to process image"
    AI_ANALYSIS_FAILED = "AI analysis failed"
    INVALID_USER_ID = "Invalid user identifier"
    DATABASE_ERROR = "Database operation failed"


class SuccessMessages:
    """Centralized success messages."""
    
    PHOTO_UPLOADED = "Photo uploaded successfully"
    ANALYSIS_COMPLETE = "Analysis completed successfully"
    FACE_ANONYMIZED = "Face anonymized for privacy"
    DATA_DELETED = "All user data deleted successfully"


class AnalysisPrompts:
    """AI prompts for body composition analysis."""
    
    BASE_PROMPT = """You are an expert body composition analyst. Analyze this photo and provide:

1. Estimated body fat percentage (as a number between 5-50)
2. Confidence level in your estimate (low/medium/high)
3. Brief explanation of your reasoning (2-3 sentences)

Important:
- This is for informational purposes only, not medical advice
- Focus on visible indicators: muscle definition, body proportions, overall physique
- Be objective and professional
- If the photo quality is poor or angle is bad, note this in confidence level

Return ONLY a JSON object with this exact structure:
{
    "body_fat_percentage": <number>,
    "confidence": "<low/medium/high>",
    "reasoning": "<your explanation>",
    "photo_quality": "<poor/fair/good/excellent>"
}"""

    MULTI_ANGLE_PROMPT = """You are analyzing multiple photos of the same person from different angles.
    
Photos provided:
- Front view
- Side view
- Back view

Provide a comprehensive body composition analysis considering all angles.

Return ONLY a JSON object with this exact structure:
{
    "body_fat_percentage": <number>,
    "confidence": "<low/medium/high>",
    "reasoning": "<your explanation considering all angles>",
    "photo_quality": "<poor/fair/good/excellent>",
    "consistency_check": "<are the photos consistent with each other?>"
}"""


class WidgetTemplates:
    """Widget HTML template URIs."""
    
    UPLOAD = "ui://widget/photo-upload.html"
    RESULTS = "ui://widget/results.html"
    TIMELINE = "ui://widget/timeline.html"
    COMPARISON = "ui://widget/comparison.html"
