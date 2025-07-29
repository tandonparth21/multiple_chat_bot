# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import os
from langchain_utils import process_pdf, query_pdf
from pydantic_models import ChatInput, ChatResponse, PDFUploadResponse

app = FastAPI(title="PDF Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_vectorstores = {}

@app.get("/")
async def root():
    return {"message": "Welcome to PDF Chatbot API"}

@app.post("/upload_pdf/", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        os.makedirs("uploads", exist_ok=True)
        file_location = os.path.join("uploads", file.filename.replace(" ", "_"))
        with open(file_location, "wb") as f:
            f.write(file.file.read())

        session_id = str(uuid4())
        vectorstore = process_pdf(file_location, session_id)
        session_vectorstores[session_id] = vectorstore

        os.remove(file_location)

        return {"message": "PDF processed successfully", "session_id": session_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/chat/", response_model=ChatResponse)
async def chat(request: ChatInput):
    try:
        session_id = request.session_id
        query = request.user_message

        if not session_id or not query:
            raise HTTPException(status_code=400, detail="Missing session_id or user_message")

        vectorstore = session_vectorstores.get(session_id)
        if not vectorstore:
            raise HTTPException(status_code=404, detail="Session not found. Please upload a PDF first.")

        bot_reply = query_pdf(vectorstore, query)

        if not bot_reply or len(bot_reply.strip()) < 10:
            bot_reply = "I couldn't find relevant information. Try rephrasing your question."

        return {"bot_response": bot_reply, "session_id": session_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in session_vectorstores:
        del session_vectorstores[session_id]
        index_path = f"uploads/faiss_index_{session_id}"
        if os.path.exists(index_path):
            import shutil
            shutil.rmtree(index_path)
        return {"message": "Session cleared successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")
