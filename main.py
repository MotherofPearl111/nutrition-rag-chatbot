from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
from anthropic import Anthropic
from dotenv import load_dotenv
import logging
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nutrition RAG API with USDA Database",
    description="A nutrition advice chatbot powered by Claude AI and USDA food database",
    version="2.0.0"
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

# USDA API configuration
USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Request models
class ChatRequest(BaseModel):
    message: str

class HealthResponse(BaseModel):
    status: str
    claude_available: bool
    usda_available: bool
    message: str

# USDA API functions
async def search_usda_food(query: str, max_results: int = 5):
    """Search for food in USDA database"""
    if not USDA_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USDA_BASE_URL}/foods/search",
                params={
                    "query": query,
                    "dataType": ["Foundation", "SR Legacy"],
                    "pageSize": max_results,
                    "api_key": USDA_API_KEY
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("foods", [])
            else:
                logger.warning(f"USDA API error: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"USDA search error: {e}")
        return None

async def get_usda_food_details(fdc_id: int):
    """Get detailed nutrition info for a specific food"""
    if not USDA_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USDA_BASE_URL}/food/{fdc_id}",
                params={"api_key": USDA_API_KEY},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"USDA details error: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"USDA details error: {e}")
        return None

def format_nutrition_data(food_data):
    """Format USDA nutrition data for Claude"""
    if not food_data:
        return ""
    
    try:
        food_name = food_data.get("description", "Unknown food")
        nutrients = food_data.get("foodNutrients", [])
        
        # Key nutrients to highlight
        key_nutrients = {
            "Energy": "calories",
            "Protein": "protein",
            "Total lipid (fat)": "fat",
            "Carbohydrate, by difference": "carbs",
            "Fiber, total dietary": "fiber",
            "Sugars, total including NLEA": "sugar",
            "Sodium, Na": "sodium",
            "Calcium, Ca": "calcium",
            "Iron, Fe": "iron",
            "Vitamin C, total ascorbic acid": "vitamin C"
        }
        
        nutrition_info = f"\n**USDA Nutrition Data for {food_name}** (per 100g):\n"
        
        for nutrient in nutrients:
            nutrient_name = nutrient.get("nutrient", {}).get("name", "")
            if nutrient_name in key_nutrients:
                value = nutrient.get("amount", 0)
                unit = nutrient.get("nutrient", {}).get("unitName", "")
                nutrition_info += f"• {key_nutrients[nutrient_name].title()}: {value}{unit}\n"
        
        return nutrition_info
        
    except Exception as e:
        logger.error(f"Error formatting nutrition data: {e}")
        return ""

# Health check endpoint
@app.get("/", response_model=dict)
async def root():
    return {"message": "Enhanced Nutrition RAG API is running! 🚀🥗"}

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        claude_available=claude is not None,
        usda_available=USDA_API_KEY is not None,
        message=f"Claude: {'✅' if claude else '❌'} | USDA: {'✅' if USDA_API_KEY else '❌'}"
    )

# Enhanced chat endpoint with USDA integration
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
        logger.info(f"Processing enhanced chat request: {request.message[:50]}...")
        
        # Try to extract food names from the question for USDA lookup
        usda_context = ""
        
        # Simple food detection (you can make this more sophisticated)
        food_keywords = ["calories", "protein", "nutrition", "nutrients", "vitamin", "mineral"]
        if any(keyword in request.message.lower() for keyword in food_keywords):
            
            # Extract potential food names (basic implementation)
            words = request.message.lower().split()
            potential_foods = []
            
            # Common food words to search for
            food_indicators = ["chicken", "beef", "apple", "banana", "rice", "bread", "milk", "egg", "fish", "salmon", "broccoli", "spinach", "cheese", "yogurt", "oats", "quinoa", "almonds", "avocado"]
            
            for food in food_indicators:
                if food in request.message.lower():
                    potential_foods.append(food)
            
            # Search USDA for the first found food
            if potential_foods:
                logger.info(f"Searching USDA for: {potential_foods[0]}")
                usda_foods = await search_usda_food(potential_foods[0], max_results=1)
                
                if usda_foods and len(usda_foods) > 0:
                    # Get detailed nutrition info
                    fdc_id = usda_foods[0].get("fdcId")
                    if fdc_id:
                        food_details = await get_usda_food_details(fdc_id)
                        if food_details:
                            usda_context = format_nutrition_data(food_details)
                            logger.info("✅ Retrieved USDA nutrition data")

        # Create enhanced nutrition-focused prompt
        nutrition_prompt = f"""You are a knowledgeable and helpful nutrition expert with access to USDA nutrition database information.

User Question: {request.message}

{usda_context}

Please provide:
1. A clear, informative answer to the user's question
2. Use the USDA nutrition data above if it's relevant to the question
3. Practical advice when applicable
4. Any important disclaimers about consulting healthcare professionals for medical conditions

Keep your response conversational and easy to understand. If USDA data is provided, reference it as "According to USDA data" or similar."""

        # Call Claude API
        response = claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": nutrition_prompt
            }]
        )
        
        # Extract response text
        response_text = response.content[0].text
        logger.info("✅ Successfully generated enhanced Claude response")
        
        return {
            "response": response_text,
            "sources": ["Claude AI", "USDA FoodData Central"] if usda_context else ["Claude AI"],
            "usda_data_used": bool(usda_context),
            "model": "claude-3-5-sonnet-20241022"
        }
        
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"❌ Enhanced chat error: {str(e)}")
        
        # Return user-friendly error
        raise HTTPException(
            status_code=500,
            detail=f"Sorry, I encountered an error processing your nutrition question. Please try again."
        )

# Test endpoint for USDA API
@app.get("/api/test-usda/{food_name}")
async def test_usda(food_name: str):
    """Test endpoint to check USDA API integration"""
    if not USDA_API_KEY:
        raise HTTPException(500, "USDA API key not configured")
    
    foods = await search_usda_food(food_name, max_results=3)
    return {"query": food_name, "results": foods}

# Run the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Starting Enhanced Nutrition RAG API on port {port}")
    logger.info(f"📋 Claude status: {'✅ Ready' if claude else '❌ Not available'}")
    logger.info(f"🥗 USDA status: {'✅ Ready' if USDA_API_KEY else '❌ Not available'}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )