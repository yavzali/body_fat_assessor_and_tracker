"""Database repository layer.

This module provides a single source of truth for all database operations.
All CRUD operations are centralized here to maintain consistency and
enable easier testing and modification.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from config import ErrorMessages
from models import User, Photo, Analysis, PhotoType
from schemas import UserCreate, AnalysisCreate


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class UserRepository:
    """Repository for User operations."""
    
    @staticmethod
    def get_by_id(session: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return session.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_openai_subject(session: Session, openai_subject: str) -> Optional[User]:
        """Get user by OpenAI subject ID."""
        return session.query(User).filter(User.openai_subject == openai_subject).first()
    
    @staticmethod
    def create(session: Session, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            user = User(openai_subject=user_data.openai_subject)
            session.add(user)
            session.flush()
            return user
        except IntegrityError:
            session.rollback()
            raise RepositoryError("User with this OpenAI subject already exists")
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"{ErrorMessages.DATABASE_ERROR}: {str(e)}")
    
    @staticmethod
    def get_or_create(session: Session, openai_subject: str) -> User:
        """Get existing user or create new one."""
        user = UserRepository.get_by_openai_subject(session, openai_subject)
        if not user:
            user = UserRepository.create(session, UserCreate(openai_subject=openai_subject))
        return user
    
    @staticmethod
    def update_last_analysis(session: Session, user_id: str) -> None:
        """Update user's last analysis timestamp and increment count."""
        try:
            user = UserRepository.get_by_id(session, user_id)
            if user:
                user.last_analysis_at = datetime.now(timezone.utc)
                user.total_analyses += 1
                session.flush()
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"{ErrorMessages.DATABASE_ERROR}: {str(e)}")
    
    @staticmethod
    def delete(session: Session, user_id: str) -> bool:
        """Delete user and all associated data (cascade)."""
        try:
            user = UserRepository.get_by_id(session, user_id)
            if user:
                session.delete(user)
                session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"{ErrorMessages.DATABASE_ERROR}: {str(e)}")
    
    @staticmethod
    def check_rate_limit(session: Session, user_id: str) -> tuple[bool, Optional[datetime]]:
        """Check if user has exceeded rate limit.
        
        Returns:
            Tuple of (is_allowed, next_allowed_time)
        """
        user = UserRepository.get_by_id(session, user_id)
        if not user:
            return False, None
        
        # Premium users have no limit
        if user.is_premium:
            return True, None
        
        # Check last analysis time
        if not user.last_analysis_at:
            return True, None
        
        # Free users: 1 per week
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        if user.last_analysis_at < week_ago:
            return True, None
        
        # Calculate when next analysis is allowed
        next_allowed = user.last_analysis_at + timedelta(days=7)
        return False, next_allowed


class PhotoRepository:
    """Repository for Photo operations."""
    
    @staticmethod
    def get_by_id(session: Session, photo_id: str) -> Optional[Photo]:
        """Get photo by ID."""
        return session.query(Photo).filter(Photo.id == photo_id).first()
    
    @staticmethod
    def create(
        session: Session,
        user_id: str,
        file_path: str,
        original_filename: str,
        file_size: int,
        photo_type: PhotoType = PhotoType.FRONT,
        width: Optional[int] = None,
        height: Optional[int] = None,
        faces_detected: int = 0,
        is_anonymized: bool = False,
    ) -> Photo:
        """Create a new photo record."""
        try:
            photo = Photo(
                user_id=user_id,
                file_path=file_path,
                original_filename=original_filename,
                file_size=file_size,
                photo_type=photo_type,
                width=width,
                height=height,
                faces_detected=faces_detected,
                is_anonymized=is_anonymized,
            )
            session.add(photo)
            session.flush()
            return photo
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"{ErrorMessages.DATABASE_ERROR}: {str(e)}")
    
    @staticmethod
    def get_user_photos(
        session: Session,
        user_id: str,
        limit: Optional[int] = None,
    ) -> list[Photo]:
        """Get all photos for a user, ordered by most recent first."""
        query = (
            session.query(Photo)
            .filter(Photo.user_id == user_id)
            .order_by(desc(Photo.uploaded_at))
        )
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def delete(session: Session, photo_id: str) -> bool:
        """Delete a photo."""
        try:
            photo = PhotoRepository.get_by_id(session, photo_id)
            if photo:
                session.delete(photo)
                session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"{ErrorMessages.DATABASE_ERROR}: {str(e)}")


class AnalysisRepository:
    """Repository for Analysis operations."""
    
    @staticmethod
    def get_by_id(session: Session, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID."""
        return session.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    @staticmethod
    def get_by_photo_id(session: Session, photo_id: str) -> Optional[Analysis]:
        """Get analysis for a specific photo."""
        return session.query(Analysis).filter(Analysis.photo_id == photo_id).first()
    
    @staticmethod
    def create(session: Session, analysis_data: AnalysisCreate) -> Analysis:
        """Create a new analysis record."""
        try:
            analysis = Analysis(
                user_id=analysis_data.user_id,
                photo_id=analysis_data.photo_id,
                body_fat_percentage=analysis_data.body_fat_percentage,
                confidence=analysis_data.confidence,
                photo_quality=analysis_data.photo_quality,
                reasoning=analysis_data.reasoning,
                ai_provider=analysis_data.ai_provider,
                ai_model=analysis_data.ai_model,
                processing_time_ms=analysis_data.processing_time_ms,
            )
            session.add(analysis)
            session.flush()
            return analysis
        except IntegrityError:
            session.rollback()
            raise RepositoryError("Analysis already exists for this photo")
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"{ErrorMessages.DATABASE_ERROR}: {str(e)}")
    
    @staticmethod
    def get_latest_for_user(session: Session, user_id: str) -> Optional[Analysis]:
        """Get the most recent analysis for a user."""
        return (
            session.query(Analysis)
            .filter(Analysis.user_id == user_id)
            .order_by(desc(Analysis.created_at))
            .first()
        )
    
    @staticmethod
    def get_user_history(
        session: Session,
        user_id: str,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[Analysis]:
        """Get analysis history for a user with optional filtering."""
        query = (
            session.query(Analysis)
            .filter(Analysis.user_id == user_id)
        )
        
        if start_date:
            query = query.filter(Analysis.created_at >= start_date)
        if end_date:
            query = query.filter(Analysis.created_at <= end_date)
        
        query = query.order_by(desc(Analysis.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_statistics(session: Session, user_id: str) -> dict:
        """Get statistical summary of user's analyses."""
        analyses = AnalysisRepository.get_user_history(session, user_id)
        
        if not analyses:
            return {
                "total_count": 0,
                "average_body_fat": None,
                "min_body_fat": None,
                "max_body_fat": None,
                "latest_body_fat": None,
            }
        
        body_fat_values = [a.body_fat_percentage for a in analyses]
        
        return {
            "total_count": len(analyses),
            "average_body_fat": round(sum(body_fat_values) / len(body_fat_values), 1),
            "min_body_fat": min(body_fat_values),
            "max_body_fat": max(body_fat_values),
            "latest_body_fat": analyses[0].body_fat_percentage,
            "first_analysis_date": analyses[-1].created_at,
            "latest_analysis_date": analyses[0].created_at,
        }
    
    @staticmethod
    def delete(session: Session, analysis_id: str) -> bool:
        """Delete an analysis."""
        try:
            analysis = AnalysisRepository.get_by_id(session, analysis_id)
            if analysis:
                session.delete(analysis)
                session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"{ErrorMessages.DATABASE_ERROR}: {str(e)}")
