[paste the entire code above]
EOF~
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import anthropic
import uuid
from typing import List, Dict
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

# Initialize Claude - this was missing!
try:
    claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    print("✅ Claude initialized!")
except Exception as e:
    print(f"❌ Claude initialization failed: {e}")
    claude = None

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Nutrition RAG API is running! 🚀", "status": "healthy"}

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "claude": claude is not None,
        "message": "All services working!" if claude else "Claude connection failed - check API key"
    }

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    # Temporary placeholder - will add document processing later
    return {
        "message": "Upload functionality will be added back once basic chat is working",
        "filename": file.filename,
        "status": "placeholder"
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not claude:
        raise HTTPException(503, "Claude service not initialized - check API key")
    
    try:
        # Call Claude API for nutrition advice
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user", 
                "content": f"You are a nutrition expert. Provide helpful, accurate advice about: {request.message}"
            }]
        )
        
        return {
            "response": response.content[0].text,
            "sources": ["Claude AI Nutrition Knowledge"],
            "relevant_chunks": 1
        }
        
    except Exception as e:
        raise HTTPException(500, f"Claude API error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
