# AI-README.md - Guide for AI Assistants

> **Purpose:** This document is specifically written for AI assistants (Claude, Cursor, Copilot, etc.) to understand how to work with this codebase. Human developers should read README.md and DEVELOPMENT.md instead.

---

## 🤖 For AI Assistants: Read This First

This codebase follows an **AI-first design philosophy**. Every architectural decision prioritizes:

1. **AI Editability** - Files sized for AI context windows
2. **Clear Boundaries** - Know exactly where to make changes
3. **Extensibility** - Add features without breaking existing code
4. **Encapsulation** - Change one layer without touching others
5. **Isolated Failures** - Bugs stay contained to single files

**Your job:** Maintain these principles when making ANY changes.

---

## 📏 Critical Constraint: File Size Limits

### **RULE: No file should exceed 400 lines**

**Why this matters:**
- AI context windows are limited
- Smaller files = better comprehension
- Easier to edit specific functionality
- Faster to locate and fix bugs
- Reduces risk of breaking unrelated code

### What to do when approaching limit:

**❌ DON'T:** Keep adding to an oversized file
**✅ DO:** Extract related functions to a new file

**Example:**
```python
# services/analysis.py approaching 400 lines?
# Extract ensemble features:

# Create: services/ensemble.py
class EnsembleAnalyzer:
    def four_layer_analysis(...):
        # Layer 1, 2, 3, 4 logic here
        
# Update: services/analysis.py
from services.ensemble import EnsembleAnalyzer

class AnalysisService:
    def __init__(self):
        self.ensemble = EnsembleAnalyzer()
```

**Key principle:** Split by FUNCTIONALITY, not arbitrarily.

---

## 🏗️ Architecture: The Sacred Layers

This codebase uses **strict layered architecture**. Never violate these boundaries.

```
┌─────────────────────────────────────┐
│  Layer 1: MCP Tools (tools.py)     │  ← ChatGPT talks to this layer
│  - Thin wrappers                    │
│  - No business logic               │
│  - Format responses for ChatGPT     │
└────────────┬────────────────────────┘
             │ calls ↓
┌────────────▼────────────────────────┐
│  Layer 2: Services (services/)     │  ← Business logic lives here
│  - AnalysisService                  │
│  - ImageService                     │
│  - Orchestrates workflows           │
└────────────┬────────────────────────┘
             │ calls ↓
┌────────────▼────────────────────────┐
│  Layer 3: Repository                │  ← ALL database operations
│  - Single source of truth           │
│  - UserRepository, PhotoRepository  │
│  - AnalysisRepository               │
└────────────┬────────────────────────┘
             │ uses ↓
┌────────────▼────────────────────────┐
│  Layer 4: Models (models.py)       │  ← Database schema
│  - User, Photo, Analysis            │
│  - SQLAlchemy ORM models            │
└─────────────────────────────────────┘
```

### Layer Rules (NEVER VIOLATE):

**Layer 1 (Tools):**
- ✅ Can call Services
- ❌ Cannot access Repository directly
- ❌ Cannot access Database directly
- Purpose: Translate between MCP protocol and business logic

**Layer 2 (Services):**
- ✅ Can call Repository
- ✅ Can call other Services
- ❌ Cannot access Database directly (use Repository)
- Purpose: Implement business logic and workflows

**Layer 3 (Repository):**
- ✅ Can access Database
- ✅ Can use Models
- ❌ Cannot call Services
- Purpose: Centralize ALL database operations

**Layer 4 (Models):**
- ✅ Pure data definitions
- ❌ No business logic
- Purpose: Define database schema

### Why These Rules Matter:

**Example violation:**
```python
# ❌ BAD: Tool directly accessing database
@mcp.tool()
async def get_user_data() -> dict:
    session = SessionLocal()
    user = session.query(User).first()  # WRONG!
```

**Correct approach:**
```python
# ✅ GOOD: Tool → Service → Repository → Database
@mcp.tool()
async def get_user_data() -> dict:
    return await tools.get_user_data_tool(...)

# tools.py
async def get_user_data_tool(meta):
    with get_session_context() as session:
        user = UserRepository.get_by_openai_subject(session, subject)
    return format_response(user)
```

**Benefits:**
- Want to change database? Only touch Repository
- Want to add caching? Insert between Service and Repository
- Want to change AI provider? Only touch AnalysisService
- Everything else stays unchanged

---

## 🎯 How to Add Features (Step-by-Step)

When the user asks you to add a feature, **ALWAYS follow this exact sequence:**

### Step 1: Define Data Contract (schemas.py)

```python
# Add Pydantic schemas for request/response
class NewFeatureRequest(BaseModel):
    user_id: str
    parameter: str
    
class NewFeatureResponse(BaseModel):
    result: str
    metadata: dict
```

**Why first:** Defines the "contract" between layers. Everything else implements this contract.

### Step 2: Update Database (if needed)

**Add to models.py:**
```python
class NewModel(Base):
    __tablename__ = "new_table"
    id: Mapped[str] = mapped_column(...)
    # Fields
```

**Create migration (production):**
```bash
alembic revision --autogenerate -m "Add new feature"
alembic upgrade head
```

### Step 3: Add Repository Methods (services/repository.py)

```python
class NewRepository:
    @staticmethod
    def create(session: Session, data: NewFeatureRequest) -> NewModel:
        try:
            obj = NewModel(...)
            session.add(obj)
            session.flush()
            return obj
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"Failed: {e}")
```

**Why:** Centralizes all database access. Other code calls this, never touches DB directly.

### Step 4: Add Service Logic (services/)

**Option A - Add to existing service:**
```python
# services/analysis.py
class AnalysisService:
    def new_feature_method(self, data):
        # Business logic here
        pass
```

**Option B - Create new service (if >350 lines or different concern):**
```python
# services/new_service.py
class NewService:
    def __init__(self):
        pass
        
    def process(self, data):
        # Business logic
        pass
```

### Step 5: Add Tool (tools.py)

```python
async def new_feature_tool(param: str, meta: dict) -> dict:
    """Tool implementation."""
    try:
        user_id = get_user_from_meta(meta)
        
        with get_session_context() as session:
            # Call service
            service = NewService()
            result = service.process(param)
            
            # Store in database
            NewRepository.create(session, result)
        
        return {
            "content": [{
                "type": "text",
                "text": "Success message"
            }],
            "structuredContent": result.model_dump()
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text", 
                "text": f"Error: {e}"
            }]
        }
```

### Step 6: Register Tool (main.py)

```python
@mcp.tool()
async def new_feature(param: str) -> dict:
    """Description for ChatGPT.
    
    Args:
        param: Parameter description
    """
    return await tools.new_feature_tool(param, mcp.request_context.get().meta)
```

### Step 7: Add Widget (if needed)

```jsx
// frontend/src/widgets/NewFeature.jsx
export default function NewFeature() {
    const { toolOutput } = useHostState();
    // React component
}
```

**Always follow this order.** Skipping steps breaks encapsulation.

---

## 🚫 Common Mistakes to AVOID

### Mistake 1: Violating Layer Boundaries

```python
# ❌ BAD: Tool accessing database directly
@mcp.tool()
async def bad_tool():
    session = SessionLocal()
    user = session.query(User).first()  # WRONG!

# ✅ GOOD: Tool → Service → Repository
@mcp.tool() 
async def good_tool():
    return await tools.good_tool_impl(meta)

async def good_tool_impl(meta):
    with get_session_context() as session:
        user = UserRepository.get_by_id(session, user_id)
```

### Mistake 2: Business Logic in Tools

```python
# ❌ BAD: Logic in tool layer
async def analyze_tool(photo_id, meta):
    # Complex AI analysis logic here  # WRONG!
    # Image processing here  # WRONG!
    # Database operations here  # WRONG!

# ✅ GOOD: Tool orchestrates, Services implement
async def analyze_tool(photo_id, meta):
    with get_session_context() as session:
        photo = PhotoRepository.get_by_id(session, photo_id)
        
        # Service handles logic
        image_service = ImageService()
        image_data = await image_service.get_image_for_analysis(photo.file_path)
        
        analysis_service = AnalysisService()
        result, time = await analysis_service.analyze_body_composition(image_data)
        
        # Store result
        AnalysisRepository.create(session, result)
```

### Mistake 3: Not Using Schemas for Validation

```python
# ❌ BAD: Manual validation
def process(user_id, data):
    if not user_id or len(user_id) < 1:  # WRONG!
        raise ValueError("Invalid")

# ✅ GOOD: Pydantic schema
class ProcessRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    data: str

def process(request: ProcessRequest):
    # Already validated!
```

### Mistake 4: Creating Huge Files

```python
# ❌ BAD: Adding everything to one file
# services/analysis.py (800 lines)
class AnalysisService:
    # 50 methods here  # WRONG!

# ✅ GOOD: Split by concern
# services/analysis.py (300 lines)
# services/ensemble.py (200 lines)
# services/validation.py (150 lines)
```

### Mistake 5: Inconsistent Error Handling

```python
# ❌ BAD: Bare except
try:
    operation()
except:  # WRONG!
    pass

# ❌ BAD: Generic errors
except Exception as e:
    return "Error"  # Not helpful!

# ✅ GOOD: Specific exceptions with context
try:
    operation()
except RepositoryError as e:
    logger.error(f"Database error: {e}")
    return error_response(ErrorMessages.DATABASE_ERROR)
except ServiceError as e:
    logger.error(f"Service error: {e}")
    return error_response(str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return error_response("Internal error")
```

---

## 🎨 Code Style Requirements

### 1. Type Hints (MANDATORY)

```python
# ✅ ALWAYS include type hints
def process_image(
    data: bytes,
    user_id: str,
) -> tuple[str, int, int]:
    """Process image and return path, width, height."""
    pass

# ❌ NEVER omit types
def process_image(data, user_id):  # WRONG!
    pass
```

### 2. Docstrings (MANDATORY for public functions)

```python
def analyze_body_composition(image_data: bytes) -> AIAnalysisResult:
    """Analyze body composition from image.
    
    Args:
        image_data: Raw image bytes in JPEG format
        
    Returns:
        Analysis result with body fat percentage and confidence
        
    Raises:
        AIAnalysisError: If AI analysis fails
        ImageProcessingError: If image is invalid
        
    Example:
        >>> result = analyze_body_composition(image_bytes)
        >>> print(f"Body fat: {result.body_fat_percentage}%")
    """
```

### 3. Error Messages (Use constants)

```python
# ✅ GOOD: Use constants from config
from config import ErrorMessages

raise ValueError(ErrorMessages.INVALID_IMAGE_FORMAT)

# ❌ BAD: Hardcoded strings
raise ValueError("Invalid image format")  # WRONG!
```

### 4. Consistent Patterns

**Database operations:**
```python
# ALWAYS use this pattern
with get_session_context() as session:
    result = Repository.operation(session, args)
    # Auto-commit on success, rollback on error
```

**Service calls:**
```python
# ALWAYS instantiate then call
service = ServiceClass()
result = await service.method(args)
```

**Tool responses:**
```python
# ALWAYS return this structure
return {
    "content": [{
        "type": "text",
        "text": "Human-readable message"
    }],
    "structuredContent": data_dict,
    "_meta": metadata_dict  # Optional
}
```

---

## 🔧 Extending the System

### Adding a New AI Provider (e.g., Gemini)

**Files to modify:**

1. **config.py**
```python
ai_provider: Literal["openai", "anthropic", "gemini"] = "openai"
gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
gemini_model: str = "gemini-pro-vision"
```

2. **services/analysis.py** (add method)
```python
async def _analyze_with_gemini(self, image_data, prompt):
    # Implementation
    pass

# Update analyze_body_composition to handle "gemini"
if self.provider == "gemini":
    result = await self._analyze_with_gemini(image_data, prompt)
```

3. **requirements.txt**
```
google-generativeai==0.3.0
```

**That's it!** No other files need to change. This is extensibility.

### Adding Multi-Photo Analysis (Phase 2)

**Files to modify:**

1. **models.py** (already has photo_type field, no changes needed)

2. **schemas.py**
```python
class MultiPhotoAnalysisRequest(BaseModel):
    front_photo_id: str
    side_photo_id: Optional[str] = None
    back_photo_id: Optional[str] = None
```

3. **services/analysis.py**
```python
async def analyze_multi_angle(
    self,
    front_image: bytes,
    side_image: Optional[bytes] = None,
    back_image: Optional[bytes] = None,
) -> tuple[AIAnalysisResult, int]:
    # Use AnalysisPrompts.MULTI_ANGLE_PROMPT
    # Combine images in single API call
    pass
```

4. **tools.py**
```python
async def process_multi_photo_tool(photo_ids: dict, meta: dict):
    # Get all photos
    # Call analysis_service.analyze_multi_angle()
    pass
```

5. **main.py**
```python
@mcp.tool()
async def process_multi_photo(
    front_id: str,
    side_id: str = None,
    back_id: str = None,
) -> dict:
    return await tools.process_multi_photo_tool(...)
```

**Layer boundaries preserved. Extensibility demonstrated.**

### Adding Premium Features (Phase 5)

**Files to modify:**

1. **models.py** (already has is_premium field!)

2. **services/repository.py**
```python
@staticmethod
def check_feature_access(session, user_id, feature):
    user = UserRepository.get_by_id(session, user_id)
    if not user.is_premium and feature in PREMIUM_FEATURES:
        return False, "Upgrade to premium"
    return True, None
```

3. **tools.py** (add checks)
```python
async def premium_feature_tool(meta):
    with get_session_context() as session:
        allowed, msg = UserRepository.check_feature_access(
            session, user_id, "advanced_analytics"
        )
        if not allowed:
            return error_response(msg)
```

**Again, extensibility without breaking existing code.**

---

## 🧪 Testing Guidelines

### Unit Test Pattern

```python
def test_repository_operation():
    """Test database operation in isolation."""
    with get_session_context() as session:
        # Create test data
        user = UserRepository.create(
            session, 
            UserCreate(openai_subject="test")
        )
        
        # Test operation
        assert user.id is not None
        assert user.openai_subject == "test"
        
        # Cleanup
        UserRepository.delete(session, user.id)

def test_service_with_mock():
    """Test service with mocked dependencies."""
    # Mock repository
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = test_user
    
    # Test service
    service = AnalysisService()
    result = service.process(test_data)
    
    assert result.body_fat_percentage > 0
```

### Integration Test Pattern

```python
async def test_full_analysis_flow():
    """Test complete workflow end-to-end."""
    # Upload image
    photo = await upload_test_image()
    
    # Trigger analysis
    result = await tools.process_photo_tool(photo.id, test_meta)
    
    # Verify results
    assert "body_fat_percentage" in result["structuredContent"]
    
    # Cleanup
    cleanup_test_data()
```

---

## 📊 File Size Monitoring

### When a File Approaches 350 Lines

**Step 1: Analyze**
- What are the major concerns?
- Can you group related functions?
- Is there a natural split point?

**Step 2: Extract**
- Create new file with related functionality
- Update imports
- Maintain layer boundaries

**Step 3: Verify**
- All tests still pass
- No circular dependencies
- Clear separation of concerns

### Example Split

```python
# services/analysis.py (380 lines → 250 lines)
from services.ensemble import EnsembleAnalyzer

class AnalysisService:
    def __init__(self):
        self.ensemble = EnsembleAnalyzer()
    
    # Keep core analysis methods
    # Delegate ensemble to new service

# NEW FILE: services/ensemble.py (200 lines)
class EnsembleAnalyzer:
    def four_layer_analysis(...):
        # Layer 1, 2, 3, 4 logic
        pass
```

---

## 🎯 Decision Tree for Changes

When the user asks you to make a change, follow this decision tree:

```
┌─────────────────────────┐
│ What type of change?    │
└──────────┬──────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────┐
│Add Data │  │Add Logic │
└────┬────┘  └────┬─────┘
     │            │
     ▼            ▼
1. Models     1. Service
2. Schemas    2. Tool
3. Repository 3. Widget
4. Service    4. Register
5. Tool
6. Widget

Does file exceed 350 lines after change?
├─ Yes → Extract to new file
└─ No  → Proceed

Does change break layer boundaries?
├─ Yes → Redesign to respect layers
└─ No  → Proceed

Are all types and docs updated?
├─ Yes → Implement
└─ No  → Add types/docs first
```

---

## 🚨 Critical Reminders

### Before Making ANY Change:

1. **Check file size** - Will this push over 400 lines?
2. **Check layer** - Am I in the right layer for this change?
3. **Check boundaries** - Am I accessing only the layer below?
4. **Check types** - Are all parameters and returns typed?
5. **Check docs** - Is the function documented?
6. **Check errors** - Am I handling all exceptions?
7. **Check patterns** - Am I following existing patterns?

### Red Flags:

- 🚩 Tool accessing database directly
- 🚩 Service importing from tools
- 🚩 Repository containing business logic
- 🚩 File over 400 lines
- 🚩 Hardcoded error messages
- 🚩 Missing type hints
- 🚩 Bare `except:` clauses
- 🚩 Circular imports

### When in Doubt:

1. **Look at existing code** - Follow established patterns
2. **Check layer boundaries** - Where should this logic live?
3. **Keep it simple** - Don't over-engineer
4. **Ask the user** - Clarify requirements if unclear

---

## 📝 Change Checklist

Before submitting code changes, verify:

- [ ] File size under 400 lines
- [ ] Layer boundaries respected
- [ ] All functions have type hints
- [ ] Public functions have docstrings
- [ ] Error handling is specific and comprehensive
- [ ] Following existing code patterns
- [ ] No hardcoded strings (use config constants)
- [ ] Database operations use Repository
- [ ] Tests updated (if applicable)
- [ ] No circular dependencies

---

## 🎓 Philosophy Summary

**This codebase prioritizes:**

1. **AI Editability** - Small files, clear boundaries
2. **Maintainability** - Each file has one clear purpose
3. **Extensibility** - Add features without breaking existing code
4. **Encapsulation** - Layers only depend on layers below
5. **Quality** - Type safety, validation, error handling

**Every decision serves these goals.**

When you (AI assistant) make changes:
- Preserve these principles
- Follow established patterns
- Maintain layer boundaries
- Keep files small
- Write quality code

**The user chose this architecture intentionally. Respect it.**

---

## 🤝 Working with Humans

When the user asks you to add features:

1. **Clarify requirements** first
2. **Explain your approach** before coding
3. **Show where changes will go** (which files/layers)
4. **Highlight any concerns** (file size, complexity, etc.)
5. **Implement following patterns**
6. **Explain what you did** after

**Communication is key.** The user may not know technical details, but they trust you to maintain code quality.

---

## 🏁 Final Notes

This AI-README exists because **code quality matters**, even (especially!) when AI is writing code.

**Your responsibility:**
- Maintain architectural integrity
- Follow established patterns
- Keep files small and focused
- Preserve extensibility
- Write production-quality code

**This is not "move fast and break things."**
**This is "move fast and build things right."**

The user is building a real product. Help them build it professionally.

---

**Questions or concerns about a change?**
- Check this document
- Check DEVELOPMENT.md
- Look at existing code for patterns
- Ask the user if still unclear

**Remember: You're not just writing code. You're maintaining a well-architected system.**

🤖 Happy coding!
