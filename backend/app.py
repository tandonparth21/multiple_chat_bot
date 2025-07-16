import os
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# CHANGE MADE HERE: Changed relative import to absolute import
# Assuming pdf_util.py is in the same directory as app.py
from pdf_utils import extract_text_from_pdf, embed_and_store, get_combined_vectorstore, query_documents, FAISS_DIR

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Explicitly allow your frontend origins
    # For production, replace with your actual frontend domain:
    # allow_origins=["https://your-production-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Request models
class ChatRequest(BaseModel):
    question: str
    pdf_ids: List[str] # List of unique IDs for the PDFs to chat with

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

# Create necessary directories
# Ensure the FAISS_DIR is created based on the path defined in pdf_util.py
os.makedirs(FAISS_DIR, exist_ok=True)
os.makedirs("temp", exist_ok=True) # temp directory for temporary file uploads

@app.get("/")
async def root():
    return {"message": "PDF Chat API is running"}

@app.post("/upload/") # Corrected endpoint name to match frontend
async def upload_pdf(file: UploadFile = File(...)):
    temp_path = None # Initialize to None for cleanup in case of early error
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save temporarily
        file_ext = file.filename.split(".")[-1]
        temp_path = f"temp/temp_upload_{uuid.uuid4()}.{file_ext}"

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Generate unique PDF ID
        pdf_id = str(uuid.uuid4())[:8]

        # Extract text
        text = extract_text_from_pdf(temp_path)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF. It might be empty or scanned.")

        # Embed and store
        chunk_count = embed_and_store(pdf_id, text)

        return {
            "pdf_id": pdf_id, 
            "chunks": chunk_count,
            "filename": file.filename,
            "message": "PDF uploaded and processed successfully"
        }
    
    except HTTPException as e:
        # Re-raise HTTPExceptions as they are already formatted
        raise e
    except Exception as e:
        print(f"Error during PDF upload and processing: {str(e)}") # Log internal server errors
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Clean up temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/chat/", response_model=ChatResponse)
async def chat_with_pdfs(request: ChatRequest):
    try:
        if not request.pdf_ids:
            raise HTTPException(status_code=400, detail="No PDF IDs provided. Please upload a PDF first.")
        
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
        # Query the documents
        answer, sources = query_documents(request.question, request.pdf_ids)
        
        return ChatResponse(answer=answer, sources=sources)
    
    except ValueError as e: # Catch specific errors like "No valid vector stores found"
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error during chat processing: {str(e)}") # Log internal server errors
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)