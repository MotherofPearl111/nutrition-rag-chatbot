from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Nutrition RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude with the new working version
try:
    claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    print("✅ Claude initialized successfully!")
except Exception as e:
    print(f"❌ Claude initialization failed: {e}")
    claude = None

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Nutrition RAG API is running! 🚀"}

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "claude": claude is not None,
        "message": "All services working!" if claude else "Claude failed - check logs"
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not claude:
        raise HTTPException(503, "Claude not available")
    
    try:
        response = claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            messages=[{
                "role": "user", 
                "content": f"You are a nutrition expert. Provide helpful advice about: {request.message}"
            }]
        )
        
        return {
            "response": response.content[0].text,
            "sources": ["Claude AI Nutrition Knowledge"]
        }
        
    except Exception as e:
        raise HTTPException(500, f"Claude error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)