# Development Guide

This guide explains the architecture, design decisions, and development workflow for the Body Fat Tracker.

## Architecture Overview

### Layered Design

The backend follows a strict layered architecture:

```
┌─────────────────┐
│   MCP Tools     │  ← ChatGPT interface (tools.py)
├─────────────────┤
│   Services      │  ← Business logic (services/)
├─────────────────┤
│   Repository    │  ← Data access (repository.py)
├─────────────────┤
│   Models        │  ← Database schema (models.py)
└─────────────────┘
```

**Key Principle:** Each layer only knows about the layer below it.

### Why This Structure?

**1. Separation of Concerns**
- Tools handle MCP protocol details
- Services contain business logic
- Repository handles all database operations
- Models define data structure

**2. Testability**
- Each layer can be tested independently
- Mock lower layers to test higher layers
- Clear interfaces make testing straightforward

**3. Maintainability**
- Changes to one layer don't affect others
- Easy to understand what each file does
- Clear boundaries prevent "spaghetti code"

**4. Extensibility**
- Want to add Claude as AI provider? → Change `services/analysis.py`
- Want to switch to PostgreSQL? → Change `database.py` and `repository.py`
- Want to add new analysis type? → Add method in `services/analysis.py` and new tool in `tools.py`

## File Responsibilities

### Backend Files

**main.py**
- FastMCP server initialization
- Tool registration
- App startup/shutdown
- Widgets resource serving

**config.py**
- All settings and constants
- Environment variable loading
- Centralized configuration

**models.py**
- SQLAlchemy database models
- User, Photo, Analysis entities
- Database schema definition

**schemas.py**
- Pydantic validation schemas
- Request/response contracts
- Data validation rules

**database.py**
- Database connection management
- Session handling
- Database initialization

**tools.py**
- MCP tool implementations
- Thin wrappers around services
- Response formatting for ChatGPT

**services/repository.py**
- ALL database CRUD operations
- Single source of truth for data access
- Handles transactions and errors

**services/image.py**
- Image upload and processing
- Face detection and anonymization
- File storage management

**services/analysis.py**
- AI analysis orchestration
- OpenAI/Anthropic API calls
- Response parsing and validation

**api/uploads.py**
- HTTP endpoint for image uploads
- Called by frontend widgets
- REST API layer

### Frontend Files

**PhotoUpload.jsx**
- Drag-and-drop upload interface
- File validation
- Calls backend upload endpoint
- Triggers analysis via MCP tool call

**Results.jsx**
- Displays analysis results
- Reads from toolOutput
- Theme-aware styling

**Timeline.jsx**
- Historical progress view (Phase 3)
- Statistics and charts
- Timeline visualization

**shared/api.js**
- API communication utilities
- Upload helper functions
- Tool call wrappers

**shared/hooks.js**
- React hooks for common patterns
- Host state management
- Widget state synchronization

## Development Workflow

### Adding a New Feature

**Example: Add "Export Data" feature**

**1. Define Data Contract (schemas.py)**
```python
class ExportRequest(BaseModel):
    user_id: str
    format: Literal["csv", "json"]
    
class ExportResponse(BaseModel):
    download_url: str
    file_size: int
```

**2. Add Repository Method (repository.py)**
```python
@staticmethod
def export_user_data(session: Session, user_id: str) -> dict:
    user = UserRepository.get_by_id(session, user_id)
    analyses = AnalysisRepository.get_user_history(session, user_id)
    return {"user": user, "analyses": analyses}
```

**3. Add Service Logic (new file or existing service)**
```python
class ExportService:
    def export_to_csv(self, user_id: str) -> str:
        # Business logic here
        pass
```

**4. Add Tool (tools.py)**
```python
async def export_data_tool(format: str, meta: dict) -> dict:
    user_id = get_user_from_meta(meta)
    # Call service
    # Return response
```

**5. Register Tool (main.py)**
```python
@mcp.tool()
async def export_data(format: str = "csv") -> dict:
    return await tools.export_data_tool(format, mcp.request_context.get().meta)
```

### Testing Strategy

**Unit Tests** (each layer separately)
```python
# Test repository
def test_create_user():
    with get_session_context() as session:
        user = UserRepository.create(session, UserCreate(openai_subject="test"))
        assert user.id is not None

# Test service (with mocked repository)
def test_analysis_service():
    # Mock AI API call
    # Test result parsing
    pass

# Test tool (with mocked service)
def test_start_analysis_tool():
    # Mock user creation
    # Verify widget state
    pass
```

**Integration Tests** (end-to-end)
```python
def test_full_analysis_flow():
    # Upload image
    # Trigger analysis
    # Verify results
    pass
```

### Code Style Guidelines

**1. Use Type Hints**
```python
def process_image(data: bytes, user_id: str) -> tuple[str, int]:
    # Good: Clear types
    pass

def process_image(data, user_id):  # Bad: No types
    pass
```

**2. Document Functions**
```python
def analyze_body_composition(image_data: bytes) -> AIAnalysisResult:
    """Analyze body composition from image.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Analysis result with body fat percentage
        
    Raises:
        AIAnalysisError: If analysis fails
    """
```

**3. Handle Errors Properly**
```python
# Good: Specific exceptions
try:
    result = some_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise ServiceError("Friendly message")

# Bad: Bare except
try:
    result = some_operation()
except:
    pass
```

**4. Keep Functions Small**
- Single responsibility
- <50 lines ideally
- Extract helpers if needed

## Common Patterns

### Database Operations
```python
with get_session_context() as session:
    user = UserRepository.get_or_create(session, openai_subject)
    # Do work
    # Automatic commit on success, rollback on error
```

### AI Analysis
```python
analysis_service = AnalysisService()
result, time_ms = await analysis_service.analyze_body_composition(image_data)
```

### Error Handling
```python
try:
    # Operation
except RepositoryError as e:
    # Handle data errors
except ServiceError as e:
    # Handle business logic errors
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
```

## Performance Considerations

### Database
- Use connection pooling (already configured)
- Index frequently queried fields (openai_subject, user_id)
- Use `limit` for large result sets
- Consider pagination for history

### Image Processing
- Resize large images before processing
- Cache processed images (future optimization)
- Async file operations where possible

### AI API Calls
- Set reasonable timeouts
- Cache common analyses (future)
- Rate limit appropriately
- Consider batch processing

## Security Checklist

- [ ] Validate all user input (Pydantic schemas)
- [ ] Sanitize file uploads
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted origins (production)
- [ ] Anonymize faces before storage
- [ ] Implement rate limiting
- [ ] Add authentication (future)
- [ ] Use HTTPS in production
- [ ] Log security events
- [ ] Regular dependency updates

## Debugging Tips

**1. Enable Debug Mode**
```env
DEBUG=true
```

**2. Check Logs**
```python
print(f"Debug: {variable}")  # Simple debugging
logger.debug("Detailed message")  # Production logging
```

**3. Use Breakpoints**
```python
import pdb; pdb.set_trace()  # Python debugger
```

**4. Test MCP Tools Directly**
```python
# In Python REPL
from tools import start_analysis_tool
result = await start_analysis_tool({"openai/subject": "test123"})
print(result)
```

**5. Inspect Database**
```bash
sqlite3 bodyfat_tracker.db
.tables
SELECT * FROM users;
```

## Production Deployment

See `PRODUCT-ROADMAP.md` for full deployment strategy.

**Key changes for production:**
1. Switch to PostgreSQL
2. Use proper secret management
3. Enable rate limiting
4. Set up monitoring (Sentry, etc.)
5. Use reverse proxy (nginx)
6. Enable HTTPS
7. Set up CI/CD
8. Configure backups
9. Update CORS origins
10. Enable caching

## Questions?

- Check README.md for general info
- Check QUICK-START-GUIDE.md for getting started
- Check PRODUCT-ROADMAP.md for feature plans
- Ask in OpenAI Developer Forum
