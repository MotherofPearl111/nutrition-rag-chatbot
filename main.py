from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from anthropic import Anthropic
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nutrition RAG API",
    description="A nutrition advice chatbot powered by Claude AI",
    version="1.0.0"
)

# CORS middleware - allows requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude client
claude = None
try:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("❌ ANTHROPIC_API_KEY not found in environment variables")
        raise ValueError("Missing ANTHROPIC_API_KEY")
    
    claude = Anthropic(api_key=api_key)
    logger.info("✅ Claude initialized successfully!")
    
except Exception as e:
    logger.error(f"❌ Claude initialization failed: {e}")
    claude = None

# Request models
class ChatRequest(BaseModel):
    message: str

class HealthResponse(BaseModel):
    status: str
    claude_available: bool
    message: str

# Health check endpoint
@app.get("/", response_model=dict)
async def root():
    return {"message": "Nutrition RAG API is running! 🚀"}

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        claude_available=claude is not None,
        message="All services working!" if claude else "Claude not available - check API key"
    )

# Main chat endpoint
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Validate Claude is available
    if not claude:
        logger.error("Claude not initialized - API key issue")
        raise HTTPException(
            status_code=503, 
            detail="Claude AI service not available. Please check API key configuration."
        )
    
    # Validate request
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")
        
        # Create nutrition-focused prompt
        nutrition_prompt = f"""You are a knowledgeable and helpful nutrition expert. Please provide accurate, helpful advice about the following nutrition question:

Question: {request.message}

Please provide:
1. A clear, informative answer
2. Practical advice when applicable
3. Any important disclaimers about consulting healthcare professionals for medical conditions

Keep your response conversational and easy to understand."""

        # Call Claude API
        response = claude.messages.create(
            model="claude-3-sonnet-20240229",  # Using stable model name
            max_tokens=800,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": nutrition_prompt
            }]
        )
        
        # Extract response text
        response_text = response.content[0].text
        logger.info("✅ Successfully generated Claude response")
        
        return {
            "response": response_text,
            "sources": ["Claude AI Nutrition Knowledge"],
            "model": "claude-3-sonnet-20240229"
        }
        
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"❌ Claude API error: {str(e)}")
        
        # Return user-friendly error
        raise HTTPException(
            status_code=500,
            detail=f"Sorry, I encountered an error processing your nutrition question. Please try again. Error: {str(e)}"
        )

# Optional: Upload endpoint for future RAG functionality
@app.post("/api/upload")
async def upload():
    return {
        "message": "Document upload feature coming soon!",
        "status": "placeholder"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "message": "Please check the API documentation"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "message": "Something went wrong on our end"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Starting Nutrition RAG API on port {port}")
    logger.info(f"📋 Claude status: {'✅ Ready' if claude else '❌ Not available'}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )