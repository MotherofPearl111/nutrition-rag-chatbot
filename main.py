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

# Initialize only Claude for now
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
        "message": "Backend is working! Pinecone temporarily disabled for testing."
    }

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    # Temporary placeholder - we'll add back document processing once basic version works
    return {
        "message": "Upload temporarily disabled - testing basic functionality first",
        "filename": file.filename,
        "status": "placeholder"
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not claude:
        raise HTTPException(503, "Claude service not initialized")
    
    try:
        # Simple nutrition responses without vector search for now
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user", 
                "content": f"You are a nutrition expert. Provide helpful advice about: {request.message}"
            }]
        )
        
        return {
            "response": response.content[0].text,
            "sources": ["Claude AI Nutrition Knowledge"],
            "relevant_chunks": 1
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)