cat > main.py << 'EOF'
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import anthropic
import pinecone
import uuid
from typing import List, Dict
from dotenv import load_dotenv
import PyPDF2
import docx

load_dotenv()

app = FastAPI(title="Nutrition RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))
    
    index_name = "nutrition-docs"
    index = pinecone.Index(index_name)
    
    print("✅ All services initialized!")
except Exception as e:
    print(f"❌ Service initialization failed: {e}")
    claude = index = None

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
        "pinecone": index is not None
    }

def extract_text(file_path: str, filename: str) -> str:
    if filename.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return "".join([page.extract_text() for page in reader.pages])
    elif filename.endswith('.docx'):
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def chunk_text(text: str) -> List[str]:
    chunks = []
    words = text.split()
    chunk_size = 150  # Smaller chunks for better embedding
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return [c for c in chunks if len(c.strip()) > 50]

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(400, "Only PDF, DOCX, TXT files supported")
    
    if not all([claude, index]):
        raise HTTPException(503, "Services not initialized")
    
    file_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        text = extract_text(file_path, file.filename)
        chunks = chunk_text(text)
        
        # Upsert with text - Pinecone will handle embeddings automatically
        upsert_data = []
        for i, chunk in enumerate(chunks):
            upsert_data.append({
                "id": f"{file.filename}_{i}_{uuid.uuid4().hex[:8]}",
                "metadata": {
                    "text": chunk, 
                    "filename": file.filename
                }
            })
        
        # For hosted embeddings, we pass the text in metadata and let Pinecone embed
        index.upsert(vectors=upsert_data, async_req=False)
        os.remove(file_path)
        
        return {
            "filename": file.filename,
            "chunks_processed": len(chunks),
            "status": "success"
        }
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(500, str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not all([claude, index]):
        raise HTTPException(503, "Services not initialized")
    
    try:
        # Query using text - Pinecone will embed the query automatically
        results = index.query(
            vector=request.message,
            top_k=3,
            include_metadata=True
        )
        
        if not results.matches:
            return {
                "response": "I don't have information about that. Please upload nutrition documents first!",
                "sources": []
            }
        
        context = "\n\n".join([
            f"Source: {match.metadata['filename']}\nContent: {match.metadata['text']}"
            for match in results.matches
        ])
        
        prompt = f"""You are a nutrition expert. Answer the question using only the provided context.

Context:
{context}

Question: {request.message}

Provide a helpful answer based on the context."""

        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        sources = list(set([match.metadata['filename'] for match in results.matches]))
        
        return {
            "response": response.content[0].text,
            "sources": sources,
            "relevant_chunks": len(results.matches)
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF