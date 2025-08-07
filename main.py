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

# Initialize Claude with proper error handling
try:
    claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    print("✅ Claude initialized successfully!")
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
        "message": "All services working!" if claude else "Claude connection failed - check API key and logs"
    }

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    # Placeholder for document upload - will add back later
    return {
        "message": "Document upload will be added back once Claude is working",
        "filename": file.filename,
        "chunks_processed": 0,
        "status": "placeholder"
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not claude:
        raise HTTPException(503, "Claude service not initialized. Check API key configuration.")
    
    try:
        # Create nutrition-focused prompt
        nutrition_prompt = f"""You are an expert nutritionist and dietitian. Please provide helpful, evidence-based nutrition advice for this question: {request.message}

Please provide practical, accurate information about nutrition, diet, and health. Keep your response informative but accessible."""

        # Call Claude API
        response = claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=600,
            messages=[{
                "role": "user", 
                "content": nutrition_prompt
            }]
        )
        
        return {
            "response": response.content[0].text,
            "sources": ["Claude AI - Nutrition Expert Knowledge"],
            "relevant_chunks": 1
        }
        
    except Exception as e:
        print(f"Claude API error: {e}")
        raise HTTPException(500, f"Failed to get response from Claude: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)