# Body Fat Tracker - ChatGPT App

AI-powered body composition tracking app integrated directly into ChatGPT. Upload photos, get body fat percentage estimates, and track your fitness progress over time—all with automatic face anonymization for privacy.

## 🎯 Features

**Phase 1 (MVP - Current):**
- 📸 Photo upload widget with drag-and-drop
- 🤖 AI-powered body fat analysis (GPT-4V or Claude)
- 🔒 Automatic face anonymization for privacy
- 📊 Analysis results with confidence scoring
- 💾 Persistent data storage

**Coming Soon:**
- Phase 2: Multi-angle analysis (front, side, back)
- Phase 3: Historical tracking with progress charts
- Phase 4: Ensemble AI analysis (4-layer validation)
- Phase 5: Premium features & advanced analytics

## 🏗️ Architecture

### Backend (Python)
- **FastMCP** - MCP server framework
- **SQLAlchemy** - Database ORM
- **FastAPI** - HTTP endpoints
- **Pillow + face_recognition** - Image processing
- **OpenAI / Anthropic** - AI analysis

### Frontend (React)
- **React 18** - UI components
- **window.openai bridge** - ChatGPT integration
- **Vite** - Build tool

### Structure
```
backend/
├── main.py              # FastMCP server entry point
├── config.py            # Settings & constants
├── models.py            # Database models
├── schemas.py           # Pydantic validation
├── database.py          # DB session management
├── tools.py             # MCP tools
├── services/
│   ├── repository.py    # Database CRUD
│   ├── image.py         # Image processing
│   └── analysis.py      # AI analysis
└── api/
    └── uploads.py       # HTTP upload endpoint

frontend/
├── src/
│   ├── widgets/
│   │   ├── PhotoUpload.jsx
│   │   ├── Results.jsx
│   │   └── Timeline.jsx
│   └── shared/
│       ├── api.js       # API utilities
│       └── hooks.js     # React hooks
└── package.json
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key or Anthropic API key
- ngrok (for local HTTPS testing)

### Installation

**1. Clone and setup:**
```bash
git clone <your-repo>
cd body-fat-tracker
```

**2. Backend setup:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

**3. Frontend setup:**
```bash
cd ../frontend
npm install
npm run build
```

**4. Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**5. Initialize database:**
```bash
cd backend
python -c "from database import init_db; init_db()"
```

### Running the Server

**1. Start the backend:**
```bash
cd backend
python main.py
```

The server will start on `http://localhost:8000`

**2. Start ngrok (separate terminal):**
```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

**3. Add to ChatGPT:**
1. Go to ChatGPT Settings → Apps & Connectors
2. Enable "Developer Mode"
3. Click "Create" under Connectors
4. Paste: `https://abc123.ngrok.io/mcp`
5. Name: "Body Fat Tracker"
6. Authentication: None
7. Click "Create"

### Testing

Try these commands in ChatGPT:
```
Start a body composition analysis
View my latest results
Show me my analysis history
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available options.

**Key settings:**
- `AI_PROVIDER` - Choose "openai" or "anthropic"
- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `DATABASE_URL` - Database connection string
- `UPLOAD_DIR` - Directory for storing images

### AI Provider Selection

**OpenAI (GPT-4 Vision):**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

**Anthropic (Claude 3.5 Sonnet):**
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

## 📊 Database

### Models

**User** - Identified by OpenAI subject ID
**Photo** - Uploaded images (face-anonymized)
**Analysis** - AI analysis results

### Migrations

For development:
```python
from database import reset_db
reset_db()  # WARNING: Deletes all data!
```

For production, use Alembic migrations:
```bash
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 🔒 Privacy & Security

### Face Anonymization
- Automatic face detection using `face_recognition`
- Gaussian blur (radius=30) applied to all detected faces
- Original images never stored
- Only anonymized versions persist

### Data Protection
- Minimal PII collection (anonymous user ID only)
- User can delete all data anytime
- GDPR/CCPA compliant
- 30-day data retention (configurable)

## 🧪 Development

### Project Structure Philosophy

**Layered Architecture:**
1. **Tools** (`tools.py`) - MCP interface layer
2. **Services** (`services/`) - Business logic
3. **Repository** (`services/repository.py`) - Data access
4. **Models** (`models.py`) - Database schema

**Benefits:**
- Clear separation of concerns
- Easy to test each layer
- Simple to modify (change AI provider, database, etc.)
- Scales to production

### Adding New Features

**1. Add a new tool:**
```python
# In tools.py
async def my_new_tool(arg: str, meta: dict) -> dict:
    # Your logic here
    pass

# In main.py
@mcp.tool()
async def my_new_tool(arg: str) -> dict:
    return await tools.my_new_tool(arg, mcp.request_context.get().meta)
```

**2. Add a new widget:**
```jsx
// In frontend/src/widgets/MyWidget.jsx
export default function MyWidget() {
  // Your component
}
```

## 📈 Roadmap

**Phase 0:** ✅ Validation & Architecture
**Phase 1:** ✅ MVP Development (Current)
**Phase 2:** Multi-angle analysis
**Phase 3:** Historical tracking
**Phase 4:** Ensemble AI (4-layer validation)
**Phase 5:** Premium features & monetization

See `PRODUCT-ROADMAP.md` for detailed plan.

## 🐛 Troubleshooting

### Face detection fails
```bash
# Install dlib dependencies
# macOS:
brew install cmake
pip install dlib --break-system-packages

# Ubuntu:
sudo apt-get install cmake
pip install dlib --break-system-packages
```

### Image upload fails
- Check CORS settings in `config.py`
- Verify ngrok URL is correct
- Check server logs for errors
- Ensure user ID is being passed

### AI analysis fails
- Verify API key is set correctly
- Check API provider is correct
- Review rate limits
- Check image format is supported

### Database errors
```python
# Reset database (development only!)
from database import reset_db
reset_db()
```

## 📝 API Reference

### MCP Tools

**start_analysis()** - Returns upload widget
**process_photo(photo_id: str)** - Analyzes uploaded photo  
**view_latest_results()** - Shows most recent analysis
**view_history(limit: int)** - Shows analysis history
**delete_my_data()** - Deletes all user data

### HTTP Endpoints

**POST /api/upload** - Upload photo
**GET /api/health** - Health check

## 🤝 Contributing

See `QUICK-START-GUIDE.md` for development workflow.

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- OpenAI Apps SDK Examples
- FastMCP Framework
- face_recognition library
- ChatGPT Developer Community

---

**Questions?** Check the OpenAI Developer Forum or create an issue.
