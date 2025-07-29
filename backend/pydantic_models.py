from pydantic import BaseModel
from typing import Optional

class ChatInput(BaseModel):
    session_id: str
    user_message: str

class ChatResponse(BaseModel):
    bot_response: str
    session_id: str

class PDFUploadResponse(BaseModel):
    message: str
    session_id: str