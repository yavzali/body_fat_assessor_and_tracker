"""MCP Tools for ChatGPT integration.

This module defines all the tools that ChatGPT can call.
Each tool is a thin wrapper that orchestrates the services layer.
"""

from datetime import datetime
from typing import Any

from database import get_session_context
from services.repository import UserRepository, PhotoRepository, AnalysisRepository
from services.analysis import AnalysisService
from services.image import ImageService
from schemas import AnalysisCreate, UploadWidgetState, ResultsWidgetState
from config import settings, ErrorMessages, SuccessMessages, WidgetTemplates


class ToolError(Exception):
    """Exception for tool execution errors."""
    pass


def get_user_from_meta(meta: dict) -> str:
    """Extract user ID from request metadata.
    
    Args:
        meta: Request metadata containing openai/subject
        
    Returns:
        OpenAI subject ID
        
    Raises:
        ToolError: If user ID not found in metadata
    """
    openai_subject = meta.get("openai/subject")
    if not openai_subject:
        raise ToolError(ErrorMessages.INVALID_USER_ID)
    return openai_subject


async def start_analysis_tool(meta: dict) -> dict:
    """Start a new body composition analysis.
    
    Returns an upload widget for the user to drag and drop their photo.
    
    Args:
        meta: Request metadata
        
    Returns:
        MCP response with upload widget
    """
    try:
        # Get or create user
        openai_subject = get_user_from_meta(meta)
        
        with get_session_context() as session:
            user = UserRepository.get_or_create(session, openai_subject)
            
            # Check rate limit
            is_allowed, next_allowed = UserRepository.check_rate_limit(session, user.id)
            
            if not is_allowed and next_allowed:
                time_until = next_allowed - datetime.now(datetime.timezone.utc)
                hours = int(time_until.total_seconds() / 3600)
                return {
                    "content": [{
                        "type": "text",
                        "text": f"⚠️ Rate limit reached. Free tier allows 1 analysis per week. Next analysis available in {hours} hours. Upgrade to Premium for unlimited analyses!"
                    }],
                    "structuredContent": {
                        "error": "rate_limit_exceeded",
                        "next_allowed": next_allowed.isoformat(),
                    }
                }
        
        # Return upload widget
        widget_state = UploadWidgetState(
            user_id=user.id,
            max_files=1,
            accepted_types=list(settings.allowed_extensions),
        )
        
        return {
            "content": [{
                "type": "text",
                "text": "📸 Ready to analyze your body composition! Upload a photo to get started.\n\nFor best results:\n• Good lighting\n• Stand 6-8 feet from camera\n• Wear fitted clothing\n• Front-facing pose\n\nYour face will be automatically blurred for privacy."
            }],
            "structuredContent": widget_state.model_dump(),
            "_meta": {
                "openai/outputTemplate": WidgetTemplates.UPLOAD,
            }
        }
        
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error starting analysis: {str(e)}"
            }],
            "structuredContent": {"error": str(e)}
        }


async def process_photo_tool(photo_id: str, meta: dict) -> dict:
    """Process an uploaded photo and run AI analysis.
    
    This tool is called after the user uploads a photo via the widget.
    
    Args:
        photo_id: ID of the uploaded photo
        meta: Request metadata
        
    Returns:
        MCP response with analysis results widget
    """
    try:
        openai_subject = get_user_from_meta(meta)
        
        with get_session_context() as session:
            # Get user
            user = UserRepository.get_or_create(session, openai_subject)
            
            # Get photo
            photo = PhotoRepository.get_by_id(session, photo_id)
            if not photo:
                raise ToolError(ErrorMessages.PHOTO_NOT_FOUND)
            
            # Verify photo belongs to user
            if photo.user_id != user.id:
                raise ToolError("Photo does not belong to user")
            
            # Check if already analyzed
            existing_analysis = AnalysisRepository.get_by_photo_id(session, photo_id)
            if existing_analysis:
                # Return existing analysis
                return _format_analysis_response(existing_analysis, photo)
            
            # Get image data for analysis
            image_service = ImageService()
            image_data = await image_service.get_image_for_analysis(photo.file_path)
            
            # Run AI analysis
            analysis_service = AnalysisService()
            ai_result, processing_time = await analysis_service.analyze_body_composition(image_data)
            
            # Validate result
            if not analysis_service.validate_analysis_result(ai_result):
                raise ToolError("AI analysis produced invalid results")
            
            # Create analysis record
            analysis_data = AnalysisCreate(
                user_id=user.id,
                photo_id=photo.id,
                body_fat_percentage=ai_result.body_fat_percentage,
                confidence=ai_result.confidence,
                photo_quality=ai_result.photo_quality,
                reasoning=ai_result.reasoning,
                ai_provider=settings.ai_provider,
                ai_model=settings.openai_model if settings.ai_provider == "openai" else settings.anthropic_model,
                processing_time_ms=processing_time,
            )
            
            analysis = AnalysisRepository.create(session, analysis_data)
            
            # Update user stats
            UserRepository.update_last_analysis(session, user.id)
            
            return _format_analysis_response(analysis, photo)
        
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Analysis failed: {str(e)}"
            }],
            "structuredContent": {"error": str(e)}
        }


async def view_latest_results_tool(meta: dict) -> dict:
    """View the most recent analysis results.
    
    Args:
        meta: Request metadata
        
    Returns:
        MCP response with results widget
    """
    try:
        openai_subject = get_user_from_meta(meta)
        
        with get_session_context() as session:
            user = UserRepository.get_or_create(session, openai_subject)
            
            # Get latest analysis
            analysis = AnalysisRepository.get_latest_for_user(session, user.id)
            
            if not analysis:
                return {
                    "content": [{
                        "type": "text",
                        "text": "📭 No analyses yet! Use the 'start analysis' command to upload your first photo."
                    }],
                    "structuredContent": {"message": "no_analyses"}
                }
            
            # Get photo
            photo = PhotoRepository.get_by_id(session, analysis.photo_id)
            
            return _format_analysis_response(analysis, photo)
        
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error retrieving results: {str(e)}"
            }],
            "structuredContent": {"error": str(e)}
        }


async def view_history_tool(limit: int, meta: dict) -> dict:
    """View analysis history (Phase 3).
    
    Args:
        limit: Number of analyses to return
        meta: Request metadata
        
    Returns:
        MCP response with timeline widget
    """
    try:
        openai_subject = get_user_from_meta(meta)
        
        with get_session_context() as session:
            user = UserRepository.get_or_create(session, openai_subject)
            
            # Get history
            analyses = AnalysisRepository.get_user_history(session, user.id, limit=limit)
            
            if not analyses:
                return {
                    "content": [{
                        "type": "text",
                        "text": "📭 No analysis history yet."
                    }],
                    "structuredContent": {"message": "no_history"}
                }
            
            # Get statistics
            stats = AnalysisRepository.get_statistics(session, user.id)
            
            # Format history data
            history_data = {
                "analyses": [
                    {
                        "id": a.id,
                        "date": a.created_at.isoformat(),
                        "body_fat_percentage": a.body_fat_percentage,
                        "confidence": a.confidence.value,
                    }
                    for a in analyses
                ],
                "statistics": stats,
            }
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"📊 Your Progress:\n\n• Total Analyses: {stats['total_count']}\n• Current: {stats['latest_body_fat']}%\n• Average: {stats['average_body_fat']}%\n• Range: {stats['min_body_fat']}% - {stats['max_body_fat']}%"
                }],
                "structuredContent": history_data,
                "_meta": {
                    "openai/outputTemplate": WidgetTemplates.TIMELINE,
                }
            }
        
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error retrieving history: {str(e)}"
            }],
            "structuredContent": {"error": str(e)}
        }


async def delete_user_data_tool(meta: dict) -> dict:
    """Delete all user data.
    
    Args:
        meta: Request metadata
        
    Returns:
        Confirmation message
    """
    try:
        openai_subject = get_user_from_meta(meta)
        
        with get_session_context() as session:
            user = UserRepository.get_by_openai_subject(session, openai_subject)
            
            if not user:
                return {
                    "content": [{
                        "type": "text",
                        "text": "✅ No data found to delete."
                    }]
                }
            
            # Delete user (cascade deletes photos and analyses)
            UserRepository.delete(session, user.id)
            
            return {
                "content": [{
                    "type": "text",
                    "text": SuccessMessages.DATA_DELETED
                }]
            }
        
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error deleting data: {str(e)}"
            }]
        }


def _format_analysis_response(analysis: Any, photo: Any) -> dict:
    """Format analysis and photo into widget response.
    
    Args:
        analysis: Analysis model instance
        photo: Photo model instance
        
    Returns:
        Formatted MCP response
    """
    # Confidence emoji
    confidence_emoji = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🔴",
    }.get(analysis.confidence.value, "⚪")
    
    # Quality emoji
    quality_emoji = {
        "excellent": "⭐⭐⭐",
        "good": "⭐⭐",
        "fair": "⭐",
        "poor": "❌",
    }.get(analysis.photo_quality.value, "")
    
    text_message = f"""✅ Analysis Complete!

📊 **Body Fat Percentage: {analysis.body_fat_percentage}%**

{confidence_emoji} Confidence: {analysis.confidence.value.title()}
{quality_emoji} Photo Quality: {analysis.photo_quality.value.title()}

💡 Analysis:
{analysis.reasoning}

🔒 Privacy: Your face has been automatically blurred and is not stored.

📅 Analysis Date: {analysis.created_at.strftime('%B %d, %Y at %I:%M %p')}
"""
    
    widget_state = ResultsWidgetState(
        analysis_id=analysis.id,
        show_details=True,
    )
    
    structured_data = {
        "analysis_id": analysis.id,
        "body_fat_percentage": analysis.body_fat_percentage,
        "confidence": analysis.confidence.value,
        "photo_quality": analysis.photo_quality.value,
        "reasoning": analysis.reasoning,
        "created_at": analysis.created_at.isoformat(),
        "faces_anonymized": photo.faces_detected > 0,
    }
    
    return {
        "content": [{
            "type": "text",
            "text": text_message,
        }],
        "structuredContent": structured_data,
        "_meta": {
            "openai/outputTemplate": WidgetTemplates.RESULTS,
        }
    }
