from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

from rag.core.ai import AI
from rag.data_utils.pg_db import pgdb
from rag.types import *

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="RAG Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_instance = AI()

# User functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(username: str):
    async with pgdb.db.acquire() as conn:
        user_data = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
    
    if user_data:
        return UserInDB(
            username=user_data["username"],
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            disabled=user_data.get("disabled", False),
            is_admin=user_data.get("is_admin", False),
            hashed_password=user_data["hashed_password"]
        )

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Auth endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=User)
async def register_user(username: str, password: str, email: Optional[str] = None, full_name: Optional[str] = None):
    # Check if user already exists
    existing_user = await get_user(username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(password)
    
    # Insert new user
    async with pgdb.db.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (username, hashed_password, email, full_name, is_admin)
            VALUES ($1, $2, $3, $4, $5)
        """, username, hashed_password, email, full_name, False)
    
    return User(username=username, email=email, full_name=full_name, disabled=False, is_admin=False)

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.on_event("startup")
async def startup_event():
    await pgdb.connect()

# Updated Chat Endpoints that use authentication
@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest, current_user: User = Depends(get_current_active_user)):
    """Process a chat message and return AI response"""
    try:
        # Ensure the user ID in request matches the authenticated user
        if request.userId != current_user.username:
            raise HTTPException(status_code=403, detail="Access denied: User ID mismatch")
            
        chat_id = request.chatId
        
        # If no chatId provided, create a new chat
        if not chat_id:
            chat = await pgdb.get_or_create_chat(request.userId)
            chat_id = chat['chatId']
        
        response = await ai_instance.generate(
            user_id=request.userId,
            chat_id=chat_id,
            query=request.message
        )
        
        return {"response": response, "chatId": chat_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/chats", response_model=List[Chat])
async def get_chat_history(current_user: User = Depends(get_current_active_user)):
    """Get chat history for a user"""
    try:
        userId = current_user.username
        chats = await pgdb.get_all_chats(userId)
            
        # Transform to response format
        result = []
        for chat in chats:
            last_message = await pgdb.get_last_message(chat['chat_id'])
            
            last_message_content = last_message["content"] if last_message else None
            
            result.append({
                "id": chat["chat_id"],
                "title": chat["title"],
                "username": chat["username"],
                "createdAt": chat["last_updated"].isoformat() if chat["last_updated"] else None,
                "lastMessage": last_message_content[:50] + "..." if last_message_content and len(last_message_content) > 50 else last_message_content
            })
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@app.post("/chats", response_model=Dict[str, str])
async def create_chat(request: ChatCreateRequest, current_user: User = Depends(get_current_active_user)):
    try:
        # Ensure the user ID in request matches the authenticated user
        if request.userId != current_user.username:
            raise HTTPException(status_code=403, detail="Access denied: User ID mismatch")
            
        chat = await pgdb.get_or_create_chat(request.userId)
        return {"id": chat['chatId']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")

@app.get("/chats/{chatId}/messages", response_model=List[Message])
async def get_chat_messages(chatId: str, current_user: User = Depends(get_current_active_user)):
    try:
        userId = current_user.username
        
        # Verify user has access to this chat
        async with pgdb.db.acquire() as conn:
            chat = await conn.fetchrow("SELECT * FROM chats WHERE chat_id = $1", chatId)
        
        """if not chat or chat["user_id"] != userId:
            raise HTTPException(status_code=403, detail="Access denied to this chat")"""
            
        messages = await pgdb.get_all_messages(chatId)
        
        result = []
        for msg in messages:
            result.append({
                "id": str(msg["id"]),
                "chatId": msg["chat_id"],
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat() if msg["timestamp"] else None
            })
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@app.patch("/chats/{chatId}", response_model=Dict[str, str])
async def update_chat(chatId: str, request: ChatUpdateRequest, current_user: User = Depends(get_current_active_user)):
    try:
        # Ensure the user ID in request matches the authenticated user
        if request.userId != current_user.username:
            raise HTTPException(status_code=403, detail="Access denied: User ID mismatch")
            
        async with pgdb.db.acquire() as conn:
            chat = await conn.fetchrow("SELECT * FROM chats WHERE chat_id = $1", chatId)
        
        if not chat or chat["user_id"] != request.userId:
            raise HTTPException(status_code=403, detail="Access denied to this chat")
            
        # Update chat in DB
        async with pgdb.db.acquire() as conn:
            await conn.execute("""
                UPDATE chats 
                SET title = $1, last_updated = CURRENT_TIMESTAMP
                WHERE chat_id = $2
            """, request.title, chatId)
        
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating chat: {str(e)}")

# Admin only endpoints
@app.get("/admin/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        async with pgdb.db.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users")
        
        users = []
        for row in rows:
            users.append(User(
                username=row["username"],
                email=row.get("email"),
                full_name=row.get("full_name"),
                disabled=row.get("disabled", False),
                is_admin=row.get("is_admin", False)
            ))
        
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")