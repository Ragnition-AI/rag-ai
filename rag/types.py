from typing import Dict, List, Optional, TypedDict
from pydantic import BaseModel
from datetime import datetime



#
# WORKFLOW TYPES
#

class ChatMessage(TypedDict):
    role: str  # "human" or "assistant"
    content: str
    timestamp: datetime

class ChatSession(TypedDict):
    chatId: str
    title: str  # Chat title or identifier
    messages: List[ChatMessage]
    lastUpdated: datetime

class UserSession(TypedDict):
    userId: str
    chats: Dict[str, ChatSession]  # Mapping of chatId to ChatSession

class GraphState(TypedDict):
    question: str
    generation: Optional[str]
    web_search: Optional[str]
    max_retries: int
    answers: int
    loop_step: int
    documents: List[str]  # Store document content as strings
    chat_history: List[ChatMessage]
    user_id: str
    chat_id: str


#
# API TYPES
#

# Auth Models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    is_admin: bool = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Chat Models
class MessageRequest(BaseModel):
    userId: str
    chatId: Optional[str] = None
    message: str

class MessageResponse(BaseModel):
    response: str
    chatId: str

class ChatCreateRequest(BaseModel):
    userId: str

class ChatUpdateRequest(BaseModel):
    userId: str
    title: str

class Message(BaseModel):
    id: Optional[str] = None
    chatId: str
    role: str
    content: str
    timestamp: str

class Chat(BaseModel):
    id: str
    title: str
    username: str
    createdAt: Optional[str] = None
    lastMessage: Optional[str] = None