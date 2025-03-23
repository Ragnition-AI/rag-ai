from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from rag.core.ai import AI
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai = AI()

chats = {}
messages = {}

class Message(BaseModel):
    userId: str
    chatId: str
    message: str

class UserIdRequest(BaseModel):
    userId: str

class ChatResponse(BaseModel):
    id: str
    title: str
    lastMessage: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str

class ChatUpdateRequest(BaseModel):
    userId: str
    title: str


@app.post("/chat")
async def send_message(message_data: Message):
    user_id = message_data.userId
    chat_id = message_data.chatId
    user_message = message_data.message
    
    message_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%H:%M")
    
    if chat_id not in messages:
        messages[chat_id] = []
        
    messages[chat_id].append({
        "id": message_id,
        "role": "user",
        "content": user_message,
        "timestamp": timestamp
    })
    
    try:
        ai_response = ai.generate(user_message)
        ai_message_id = str(uuid.uuid4())
        messages[chat_id].append({
            "id": ai_message_id,
            "role": "assistant",
            "content": ai_response,
            "timestamp": timestamp
        })
        return {"response": ai_response, "messageId": ai_message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats")
async def get_chat_history(userId: str):
    user_chats = [chat for chat_id, chat in chats.items() if chat["userId"] == userId]
    return user_chats

@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str, userId: str):
    if chat_id not in messages:
        return []
    return messages[chat_id]

@app.post("/chats")
async def create_new_chat(request: UserIdRequest):
    user_id = request.userId
    chat_id = str(uuid.uuid4())
    chats[chat_id] = {
        "id": chat_id,
        "userId": user_id,
        "title": "New Chat",
        "lastMessage": "Just now"
    }
    messages[chat_id] = []
    return {"id": chat_id}

@app.patch("/chats/{chat_id}")
async def update_chat(chat_id: str, data: ChatUpdateRequest):
    if chat_id not in chats:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    chats[chat_id]["title"] = data.title
    return {"status": "success"}