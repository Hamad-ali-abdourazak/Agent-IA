from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.orchestrator import CyberAwarenessAgent

app = FastAPI(title="CyberGuard API", version="1.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent lazily
db_path = Path(__file__).parent.parent / "conversations.db"
agent = None

def get_agent():
    global agent
    if agent is None:
        agent = CyberAwarenessAgent(db_path=str(db_path))
    return agent

# ============================================================================
# Models
# ============================================================================
class MessageRequest(BaseModel):
    message: str
    user_id: str = None
    session: dict = None

class MessageResponse(BaseModel):
    id: str
    response: str
    steps: list = []
    suggestions: list = []
    tip: str = ""
    follow_up: str = ""

# ============================================================================
# Routes
# ============================================================================
@app.get("/")
async def root():
    return {"status": "online", "service": "CyberGuard API"}

@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """Process user message and return response."""
    try:
        user_id = request.user_id or "anonymous"
        session = request.session or {}
        
        # Get response from agent
        agent_instance = get_agent()
        resp = agent_instance.respond(request.message, session, user_id=user_id)
        
        return MessageResponse(
            id=user_id,
            response=resp.message,
            steps=resp.steps or [],
            suggestions=[(q, float(s)) for q, s in (resp.suggestions or [])] if resp.suggestions else [],
            tip=resp.tip or "",
            follow_up=resp.follow_up or ""
        )
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
