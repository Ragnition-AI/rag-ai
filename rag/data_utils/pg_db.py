import uuid
import asyncpg

from datetime import datetime
from asyncpg.pool import Pool

from config import Config
from rag.types import ChatMessage, ChatSession

class PgDatabase:
    db: Pool

    def __init__(self):
        pass


    async def connect(self):
        self.db = await asyncpg.create_pool(Config.DATABASE_URL)
        await self.setup_db()


    async def setup_db(self):
        async with self.db.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    disabled BOOLEAN DEFAULT FALSE,
                    is_admin BOOLEAN DEFAULT FALSE
                );

                CREATE TABLE IF NOT EXISTS chats (
                    id SERIAL PRIMARY KEY,
                    chat_id TEXT UNIQUE NOT NULL,
                    username TEXT REFERENCES users(username) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    chat_id TEXT REFERENCES chats(chat_id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('human', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)


    async def get_or_create_user(self, username: str):
        async with self.db.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
            if not user:
                await conn.execute("INSERT INTO users (username) VALUES ($1)", username)

    async def get_or_create_chat(self, username: str, chat_id: str = None, title: str = "New Chat"):
        async with self.db.acquire() as conn:
            if chat_id:
                chat = await conn.fetchrow("SELECT * FROM chats WHERE chat_id = $1", chat_id)
                if chat:
                    return ChatSession(chatId=chat["chat_id"], title=chat["title"], lastUpdated=chat["last_updated"], messages=[])

            # Create a new chat if it doesn't exist
            new_chat_id = chat_id or str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO chats (chat_id, username, title) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                new_chat_id, username, title
            )
            return ChatSession(chatId=new_chat_id, title=title, lastUpdated=datetime.utcnow(), messages=[])


    async def get_chat_messages(self, chat_id: str):
        async with self.db.acquire() as conn:
            messages = await conn.fetch("SELECT role, content, timestamp FROM messages WHERE chat_id = $1", chat_id)
            return [ChatMessage(role=m["role"], content=m["content"], timestamp=m["timestamp"]) for m in messages]


    async def save_message(self, chat_id: str, role: str, content: str):
        async with self.db.acquire() as conn:
            await conn.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES ($1, $2, $3)",
                chat_id, role, content
            )

    
    async def get_all_chats(self, username):
        async with self.db.acquire() as conn:
            chats = await conn.fetch("""
                SELECT c.chat_id, c.title, c.username, c.last_updated
                FROM chats c
                WHERE c.username = $1
                ORDER BY c.last_updated DESC
            """, 
                username
            )
            return chats

    async def get_last_message(self, chat_id):
        async with self.db.acquire() as conn:
            last_message = await conn.fetchrow("""
                SELECT content 
                FROM messages 
                WHERE chat_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, 
                chat_id
            )
            return last_message


    async def get_all_messages(self, chat_id):
        async with self.db.acquire() as conn:
            messages = await conn.fetch("""
                SELECT id, chat_id, role, content, timestamp
                FROM messages
                WHERE chat_id = $1
                ORDER BY timestamp ASC
            """, 
                chat_id
            )
            return messages


pgdb = PgDatabase()