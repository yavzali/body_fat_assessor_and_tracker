"""HTTP API endpoints for file uploads.

Provides REST endpoints for widgets to upload images.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from typing import Optional

from database import get_session_context
from services.repository import UserRepository, PhotoRepository
from services.image import ImageService, ImageProcessingError
from schemas import PhotoUploadResponse
from config import settings, ErrorMessages
from models import PhotoType


router = APIRouter(prefix="/api", tags=["uploads"])


async def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from request headers.
    
    Args:
        x_user_id: User ID from X-User-Id header
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If user ID not provided
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return x_user_id


@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(
    file: UploadFile = File(...),
    photo_type: PhotoType = PhotoType.FRONT,
    user_id: str = Depends(get_user_id),
) -> PhotoUploadResponse:
    """Upload a photo for analysis.
    
    This endpoint is called by the upload widget.
    
    Args:
        file: Uploaded file
        photo_type: Type of photo (front/side/back)
        user_id: User ID from header
        
    Returns:
        Upload response with photo ID
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read file data
        file_data = await file.read()
        
        # Process and save image
        image_service = ImageService()
        file_path, width, height, file_size, faces_detected, is_anonymized = \
            await image_service.save_and_process_image(
                file_data,
                file.filename,
                user_id,
            )
        
        # Create database record
        with get_session_context() as session:
            # Verify user exists
            user = UserRepository.get_by_id(session, user_id)
            if not user:
                raise HTTPException(status_code=404, detail=ErrorMessages.USER_NOT_FOUND)
            
            # Create photo record
            photo = PhotoRepository.create(
                session,
                user_id=user_id,
                file_path=file_path,
                original_filename=file.filename,
                file_size=file_size,
                photo_type=photo_type,
                width=width,
                height=height,
                faces_detected=faces_detected,
                is_anonymized=is_anonymized,
            )
            
            return PhotoUploadResponse(
                photo_id=photo.id,
                filename=file.filename,
                size=file_size,
                faces_detected=faces_detected,
                is_anonymized=is_anonymized,
                message=f"Photo uploaded successfully. {faces_detected} face(s) detected and blurred." if faces_detected > 0 else "Photo uploaded successfully.",
            )
    
    except ImageProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{ErrorMessages.UPLOAD_FAILED}: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "body-fat-tracker-api",
        "version": settings.app_version,
    }
