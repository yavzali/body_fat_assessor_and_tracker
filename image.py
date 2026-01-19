"""Image processing service.

Handles image upload, face detection, anonymization, and storage.
All image-related operations are centralized here.
"""

import io
import uuid
from pathlib import Path
from typing import Optional, Tuple

import face_recognition
from PIL import Image, ImageFilter
import aiofiles

from config import settings, ErrorMessages, SuccessMessages


class ImageProcessingError(Exception):
    """Exception raised for image processing errors."""
    pass


class ImageService:
    """Service for image processing operations."""
    
    def __init__(self, upload_dir: Optional[Path] = None):
        """Initialize image service.
        
        Args:
            upload_dir: Directory for storing uploaded images.
                       Defaults to settings.upload_dir
        """
        self.upload_dir = upload_dir or settings.upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_and_process_image(
        self,
        image_data: bytes,
        original_filename: str,
        user_id: str,
    ) -> Tuple[str, int, int, int, int, bool]:
        """Save image and process it (resize, anonymize).
        
        Args:
            image_data: Raw image bytes
            original_filename: Original filename from upload
            user_id: User ID for organizing files
            
        Returns:
            Tuple of (file_path, width, height, file_size, faces_detected, is_anonymized)
            
        Raises:
            ImageProcessingError: If processing fails
        """
        try:
            # Validate image format
            self._validate_image(image_data, original_filename)
            
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Get original dimensions
            original_width, original_height = image.size
            
            # Resize if too large
            image = self._resize_if_needed(image)
            
            # Detect and blur faces
            faces_detected, image = await self._anonymize_faces(image)
            is_anonymized = faces_detected > 0
            
            # Generate unique filename
            file_extension = Path(original_filename).suffix.lower()
            if file_extension not in settings.allowed_extensions:
                file_extension = ".jpg"
            
            filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
            file_path = self.upload_dir / filename
            
            # Save processed image
            image.save(
                file_path,
                format="JPEG",
                quality=settings.image_quality,
                optimize=True,
            )
            
            # Get final file size
            file_size = file_path.stat().st_size
            width, height = image.size
            
            return str(file_path), width, height, file_size, faces_detected, is_anonymized
            
        except Exception as e:
            raise ImageProcessingError(f"{ErrorMessages.PROCESSING_FAILED}: {str(e)}")
    
    def _validate_image(self, image_data: bytes, filename: str) -> None:
        """Validate image format and size.
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
            
        Raises:
            ImageProcessingError: If validation fails
        """
        # Check file size
        if len(image_data) > settings.max_upload_size:
            raise ImageProcessingError(ErrorMessages.IMAGE_TOO_LARGE)
        
        # Check file extension
        ext = Path(filename).suffix.lower()
        if ext not in settings.allowed_extensions:
            raise ImageProcessingError(ErrorMessages.INVALID_IMAGE_FORMAT)
        
        # Verify it's actually an image
        try:
            image = Image.open(io.BytesIO(image_data))
            image.verify()
        except Exception:
            raise ImageProcessingError("Invalid or corrupted image file")
    
    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """Resize image if dimensions exceed maximum.
        
        Args:
            image: PIL Image object
            
        Returns:
            Resized image or original if no resize needed
        """
        width, height = image.size
        max_dim = settings.max_image_dimension
        
        if width > max_dim or height > max_dim:
            # Calculate new dimensions maintaining aspect ratio
            if width > height:
                new_width = max_dim
                new_height = int(height * (max_dim / width))
            else:
                new_height = max_dim
                new_width = int(width * (max_dim / height))
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    async def _anonymize_faces(self, image: Image.Image) -> Tuple[int, Image.Image]:
        """Detect and blur faces in image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (number_of_faces_detected, processed_image)
        """
        try:
            # Convert PIL image to numpy array for face_recognition
            import numpy as np
            image_array = np.array(image)
            
            # Detect face locations
            face_locations = face_recognition.face_locations(image_array)
            
            if not face_locations:
                return 0, image
            
            # Blur each detected face
            for top, right, bottom, left in face_locations:
                # Extract face region
                face_region = image.crop((left, top, right, bottom))
                
                # Apply strong Gaussian blur
                blurred_face = face_region.filter(
                    ImageFilter.GaussianBlur(radius=settings.face_blur_radius)
                )
                
                # Paste blurred face back
                image.paste(blurred_face, (left, top, right, bottom))
            
            return len(face_locations), image
            
        except Exception as e:
            # If face detection fails, continue without anonymization
            # but log the error
            print(f"⚠️ Face detection failed: {str(e)}")
            return 0, image
    
    async def delete_image(self, file_path: str) -> bool:
        """Delete an image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if deleted, False if file didn't exist
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"⚠️ Error deleting image: {str(e)}")
            return False
    
    async def get_image_bytes(self, file_path: str) -> bytes:
        """Read image file as bytes.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Image data as bytes
            
        Raises:
            ImageProcessingError: If file not found or read fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise ImageProcessingError("Image file not found")
            
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
        except Exception as e:
            raise ImageProcessingError(f"Failed to read image: {str(e)}")
    
    async def get_image_for_analysis(self, file_path: str) -> bytes:
        """Get image in format suitable for AI analysis.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Image data as bytes in JPEG format
        """
        try:
            # Load image
            image = Image.open(file_path)
            
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Save to bytes buffer
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=95)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to prepare image for analysis: {str(e)}")
