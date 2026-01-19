"""Main FastMCP server application.

This is the entry point for the Body Fat Tracker MCP server.
It initializes the server, registers tools, and sets up routes.
"""

import sys
from pathlib import Path
from functools import lru_cache

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
# Widget HTML Loading
# ============================================================================

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@lru_cache(maxsize=None)
def load_widget_html(widget_name: str) -> str:
    """Load widget HTML from assets directory.
    
    Args:
        widget_name: Name of the widget file (without .html extension)
        
    Returns:
        Widget HTML content
        
    Raises:
        FileNotFoundError: If widget HTML not found
    """
    # Try direct match first
    html_path = ASSETS_DIR / f"{widget_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    
    # Try with hash suffix (e.g., photo-upload-abc123.html)
    candidates = sorted(ASSETS_DIR.glob(f"{widget_name}-*.html"))
    if candidates:
        return candidates[-1].read_text(encoding="utf-8")
    
    # Fallback to placeholder if assets not built yet
    print(f"⚠️  Widget HTML for '{widget_name}' not found in {ASSETS_DIR}")
    print(f"   Run 'npm run build' in the frontend directory to generate widgets")
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{widget_name.replace('-', ' ').title()}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 40px;
            text-align: center;
            background: #f5f5f5;
        }}
        .error {{
            background: #fff;
            padding: 30px;
            border-radius: 12px;
            max-width: 500px;
            margin: 0 auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="error">
        <h2>⚠️ Widget Not Built</h2>
        <p>The {widget_name} widget needs to be built.</p>
        <p>Run: <code>cd frontend && npm run build</code></p>
    </div>
</body>
</html>"""


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
    return load_widget_html("photo-upload")


@mcp.resource("ui://widget/results.html")
async def get_results_widget() -> str:
    """Return the results display widget HTML."""
    return load_widget_html("results")


@mcp.resource("ui://widget/timeline.html")
async def get_timeline_widget() -> str:
    """Return the timeline/history widget HTML."""
    return load_widget_html("timeline")


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
    
    # Check if widgets are built
    if not ASSETS_DIR.exists():
        print(f"\n⚠️  WARNING: Assets directory not found: {ASSETS_DIR}")
        print(f"   Widgets will use placeholder HTML until frontend is built")
        print(f"   Run: cd frontend && npm run build\n")
    
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
