"""Main FastMCP server application.

This is the entry point for the Body Fat Tracker MCP server.
It initializes the server, registers tools, and sets up routes.
"""

import sys
import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from database import init_db
from api.uploads import router as upload_router
import tools


# Initialize FastMCP server
mcp = FastMCP(settings.mcp_server_name)

# Get the underlying FastAPI app
app = mcp.get_app()


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API router for file uploads
app.include_router(upload_router)


# ============================================================================
# MCP Tool Registrations
# ============================================================================

@mcp.tool()
async def start_analysis() -> dict:
    """Start a new body composition analysis.
    
    Returns an upload widget where you can drag and drop a photo.
    For best results, use good lighting and stand 6-8 feet from the camera.
    Your face will be automatically blurred for privacy.
    """
    return await tools.start_analysis_tool(mcp.request_context.get().meta)


@mcp.tool()
async def process_photo(photo_id: str) -> dict:
    """Process an uploaded photo and run AI body composition analysis.
    
    Args:
        photo_id: The ID of the uploaded photo to analyze
    
    This tool is automatically called after you upload a photo via the widget.
    """
    return await tools.process_photo_tool(photo_id, mcp.request_context.get().meta)


@mcp.tool(readOnlyHint=True)
async def view_latest_results() -> dict:
    """View your most recent body composition analysis results.
    
    Shows your latest body fat percentage estimate with confidence level
    and reasoning from the AI analysis.
    """
    return await tools.view_latest_results_tool(mcp.request_context.get().meta)


@mcp.tool(readOnlyHint=True)
async def view_history(limit: int = 10) -> dict:
    """View your body composition analysis history.
    
    Args:
        limit: Number of analyses to show (default: 10)
    
    See your progress over time with statistics and trends.
    Note: This feature is in Phase 3 and may have limited functionality in MVP.
    """
    return await tools.view_history_tool(limit, mcp.request_context.get().meta)


@mcp.tool()
async def delete_my_data() -> dict:
    """Delete all your data from the Body Fat Tracker.
    
    This will permanently delete:
    - All your uploaded photos
    - All analysis results
    - Your user profile
    
    This action cannot be undone.
    """
    return await tools.delete_user_data_tool(mcp.request_context.get().meta)


# ============================================================================
# Resource Registrations (Widget HTML)
# ============================================================================

@mcp.resource("ui://widget/photo-upload.html")
async def get_upload_widget() -> str:
    """Return the photo upload widget HTML."""
    # In production, this would load the actual built widget
    # For now, return placeholder
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Photo Upload</title>
    </head>
    <body>
        <div id="root"></div>
        <script>
            // Widget will be implemented in React
            console.log('Upload widget loaded');
        </script>
    </body>
    </html>
    """


@mcp.resource("ui://widget/results.html")
async def get_results_widget() -> str:
    """Return the results display widget HTML."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Analysis Results</title>
    </head>
    <body>
        <div id="root"></div>
        <script>
            // Widget will be implemented in React
            console.log('Results widget loaded');
        </script>
    </body>
    </html>
    """


@mcp.resource("ui://widget/timeline.html")
async def get_timeline_widget() -> str:
    """Return the timeline/history widget HTML."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Progress Timeline</title>
    </head>
    <body>
        <div id="root"></div>
        <script>
            // Widget will be implemented in React (Phase 3)
            console.log('Timeline widget loaded');
        </script>
    </body>
    </html>
    """


# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize application on startup."""
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📊 AI Provider: {settings.ai_provider}")
    print(f"💾 Database: {settings.database_url}")
    
    # Initialize database
    init_db()
    
    print(f"✅ Server ready on {settings.host}:{settings.port}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    print("👋 Shutting down server...")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info" if settings.debug else "warning",
    )
