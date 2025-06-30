"""
Authentication module for gym chatbot
"""

import jwt
import bcrypt
import datetime
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import aiosqlite
from config import DB_PATH, JWT_SECRET_KEY, JWT_ALGORITHM

# Security scheme for JWT tokens
security = HTTPBearer()

# Guest user configuration
GUEST_USER_ID = "guest"
GUEST_USERNAME = "guest"
GUEST_SESSION_DURATION = datetime.timedelta(hours=24)  # Guest sessions expire after 24 hours

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_guest: bool
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: str
    user: UserResponse
    session_code: Optional[str] = None  # For guest sessions

class GuestSession(BaseModel):
    session_id: str
    user_id: str
    created_at: str
    expires_at: str

# In-memory storage for guest sessions (in production, use Redis or database)
guest_sessions: Dict[str, GuestSession] = {}

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(days=7)  # Default 7 days
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, jwt.DecodeError, jwt.InvalidSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_guest_session() -> GuestSession:
    """Create a new guest session"""
    session_id = secrets.token_urlsafe(32)
    now = datetime.datetime.utcnow()
    expires_at = now + GUEST_SESSION_DURATION
    
    guest_session = GuestSession(
        session_id=session_id,
        user_id=GUEST_USER_ID,
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat()
    )
    
    guest_sessions[session_id] = guest_session
    return guest_session

def get_guest_session(session_id: str) -> Optional[GuestSession]:
    """Get a guest session by session ID"""
    session = guest_sessions.get(session_id)
    if not session:
        return None
    
    # Check if session has expired
    expires_at = datetime.datetime.fromisoformat(session.expires_at)
    if datetime.datetime.utcnow() > expires_at:
        # Remove expired session
        del guest_sessions[session_id]
        return None
    
    return session

def cleanup_expired_guest_sessions():
    """Clean up expired guest sessions"""
    now = datetime.datetime.utcnow()
    expired_sessions = []
    
    for session_id, session in guest_sessions.items():
        expires_at = datetime.datetime.fromisoformat(session.expires_at)
        if now > expires_at:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del guest_sessions[session_id]

async def init_auth_db():
    """Initialize authentication database tables"""
    async with aiosqlite.connect(DB_PATH) as conn:
        # Create users table
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT,
            is_guest BOOLEAN DEFAULT FALSE,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        
        # Create guest_sessions table for persistent guest sessions
        await conn.execute('''CREATE TABLE IF NOT EXISTS guest_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )''')
        
        await conn.commit()

async def create_user(username: str, password: str, email: Optional[str] = None) -> str:
    """Create a new user"""
    user_id = secrets.token_urlsafe(16)
    password_hash = hash_password(password)
    now = datetime.datetime.utcnow().isoformat()
    
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            'INSERT INTO users (id, username, email, password_hash, is_guest, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, username, email, password_hash, False, now, now)
        )
        await conn.commit()
    
    return user_id

async def get_user_by_username(username: str):
    """Get user by username"""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            'SELECT id, username, email, password_hash, is_guest, created_at FROM users WHERE username = ?',
            (username,)
        )
        row = await cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'password_hash': row[3],
                'is_guest': bool(row[4]),
                'created_at': row[5]
            }
        return None

async def get_user_by_id(user_id: str):
    """Get user by ID"""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            'SELECT id, username, email, password_hash, is_guest, created_at FROM users WHERE id = ?',
            (user_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'password_hash': row[3],
                'is_guest': bool(row[4]),
                'created_at': row[5]
            }
        return None

async def authenticate_user(username: str, password: str):
    """Authenticate a user with username and password"""
    user = await get_user_by_username(username)
    if not user:
        return None
    
    if not verify_password(password, user['password_hash']):
        return None
    
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        is_guest = payload.get("is_guest", False)
        
        if is_guest:
            # For guest users, return guest user data
            return {
                'id': user_id,
                'username': payload.get("username", "guest"),
                'email': None,
                'password_hash': None,
                'is_guest': True,
                'created_at': datetime.datetime.utcnow().isoformat()
            }
        else:
            # For registered users, get from database
            if user_id:
                user = await get_user_by_id(user_id)
                if user:
                    return user
    
    except HTTPException:
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user optionally (for guest access)"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def create_persistent_guest_session() -> dict:
    """Create a persistent guest session that can be accessed across devices"""
    guest_user_id = f"guest_{secrets.token_urlsafe(16)}"
    session_code = secrets.token_hex(3).upper()  # 6-character code like "A1B2C3"
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(days=7)  # 7 days expiration
    
    async with aiosqlite.connect(DB_PATH) as conn:
        # Create guest user in database
        await conn.execute('''
            INSERT INTO users (id, username, password_hash, is_guest, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (guest_user_id, f"Guest_{session_code}", None, True, now.isoformat(), now.isoformat()))
        
        # Store session code mapping
        await conn.execute('''
            INSERT OR REPLACE INTO guest_sessions (session_id, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (session_code, guest_user_id, now.isoformat(), expires_at.isoformat()))
        
        await conn.commit()
    
    return {
        'user_id': guest_user_id,
        'session_code': session_code,
        'username': f"Guest_{session_code}",
        'created_at': now.isoformat(),
        'expires_at': expires_at.isoformat()
    }

async def get_guest_session_by_code(session_code: str) -> Optional[dict]:
    """Get guest session by session code"""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute('''
            SELECT gs.user_id, gs.created_at, gs.expires_at, u.username
            FROM guest_sessions gs
            JOIN users u ON gs.user_id = u.id
            WHERE gs.session_id = ?
        ''', (session_code,))
        
        row = await cursor.fetchone()
        if not row:
            return None
        
        user_id, created_at, expires_at, username = row
        
        # Check if session has expired
        expires_at_dt = datetime.datetime.fromisoformat(expires_at)
        if datetime.datetime.utcnow() > expires_at_dt:
            # Clean up expired session
            await conn.execute('DELETE FROM guest_sessions WHERE session_id = ?', (session_code,))
            await conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            await conn.commit()
            return None
        
        return {
            'user_id': user_id,
            'username': username,
            'created_at': created_at,
            'expires_at': expires_at
        }

async def cleanup_expired_guest_sessions_db():
    """Clean up expired guest sessions from database"""
    async with aiosqlite.connect(DB_PATH) as conn:
        now = datetime.datetime.utcnow().isoformat()
        
        # Get expired sessions
        cursor = await conn.execute('''
            SELECT user_id FROM guest_sessions 
            WHERE expires_at < ?
        ''', (now,))
        
        expired_user_ids = [row[0] for row in await cursor.fetchall()]
        
        if expired_user_ids:
            # Delete expired sessions and their users
            placeholders = ','.join('?' * len(expired_user_ids))
            await conn.execute(f'DELETE FROM guest_sessions WHERE user_id IN ({placeholders})', expired_user_ids)
            await conn.execute(f'DELETE FROM users WHERE id IN ({placeholders})', expired_user_ids)
            await conn.commit() 