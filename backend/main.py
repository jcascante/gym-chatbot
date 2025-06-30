from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
import datetime
from fastapi.middleware.cors import CORSMiddleware
import requests
from gpt4all import GPT4All
import boto3
import json
from config import *
import logging
import asyncio
import aiosqlite
import aioboto3
from contextlib import asynccontextmanager
from auth import (
    init_auth_db, create_user, authenticate_user, get_current_user, 
    get_current_user_optional, create_access_token, create_guest_session,
    get_user_by_username, get_user_by_id,
    UserCreate, UserLogin, UserResponse, TokenResponse,
    hash_password, verify_password, verify_token,
    create_persistent_guest_session, get_guest_session_by_code
)
import secrets

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "https://gym-chatbot-frontend.loca.lt",
        "https://gym-chatbot-test.loca.lt",
        # Ngrok domains (wildcard for free plan)
        "https://*.ngrok.io",
        "https://*.ngrok-free.app",
        # Allow all origins for development (remove in production)
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Async database operations
async def init_db_async():
    """Initialize database asynchronously"""
    async with aiosqlite.connect(DB_PATH) as conn:
        # Initialize authentication tables
        await init_auth_db()
        
        # Create conversations table with user_id
        await conn.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        
        # Create chat_history table with conversation_id
        await conn.execute('''CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            citations TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )''')
        
        await conn.commit()

async def migrate_database_async():
    """Migrate database schema for conversation support and user authentication"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # Initialize auth tables first
            await init_auth_db()
            
            # Check if conversations table exists
            cursor = await conn.execute("PRAGMA table_info(conversations)")
            conversations_columns = [column[1] async for column in cursor]
            
            if not conversations_columns:
                logger.info("Creating conversations table...")
                await conn.execute('''CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
                
                # Create default guest user if it doesn't exist
                cursor = await conn.execute("SELECT id FROM users WHERE username = 'guest'")
                guest_user = await cursor.fetchone()
                if not guest_user:
                    await conn.execute('''INSERT INTO users (id, username, is_guest, created_at, updated_at) 
                                        VALUES (?, ?, ?, ?, ?)''', 
                                     ('guest', 'guest', True, datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()))
                
                # Create default conversation for existing data
                now = datetime.datetime.now().isoformat()
                await conn.execute(
                    'INSERT INTO conversations (user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)',
                    ('guest', 'Default Conversation', now, now)
                )
                default_conversation_id = await conn.execute('SELECT last_insert_rowid()')
                default_conversation_id = (await default_conversation_id.fetchone())[0]
                
                # Check if chat_history table has conversation_id column
                cursor = await conn.execute("PRAGMA table_info(chat_history)")
                chat_columns = [column[1] async for column in cursor]
                
                if 'conversation_id' not in chat_columns:
                    logger.info("Adding conversation_id column to chat_history table...")
                    # Create new table with conversation_id
                    await conn.execute('''CREATE TABLE chat_history_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id INTEGER NOT NULL,
                        user_message TEXT NOT NULL,
                        bot_response TEXT NOT NULL,
                        citations TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )''')
                    
                    # Migrate existing data to new table
                    await conn.execute('''
                        INSERT INTO chat_history_new (conversation_id, user_message, bot_response, citations, timestamp)
                        SELECT ?, user_message, bot_response, citations, timestamp FROM chat_history
                    ''', (default_conversation_id,))
                    
                    # Drop old table and rename new one
                    await conn.execute('DROP TABLE chat_history')
                    await conn.execute('ALTER TABLE chat_history_new RENAME TO chat_history')
                
                await conn.commit()
                logger.info("Migration completed successfully!")
            else:
                # Check if user_id column exists in conversations table
                if 'user_id' not in conversations_columns:
                    logger.info("Adding user_id column to conversations table...")
                    # Create new table with user_id
                    await conn.execute('''CREATE TABLE conversations_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')
                    
                    # Create default guest user if it doesn't exist
                    cursor = await conn.execute("SELECT id FROM users WHERE username = 'guest'")
                    guest_user = await cursor.fetchone()
                    if not guest_user:
                        await conn.execute('''INSERT INTO users (id, username, is_guest, created_at, updated_at) 
                                            VALUES (?, ?, ?, ?, ?)''', 
                                         ('guest', 'guest', True, datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat()))
                    
                    # Migrate existing conversations to guest user
                    await conn.execute('''
                        INSERT INTO conversations_new (user_id, title, created_at, updated_at)
                        SELECT ?, title, created_at, updated_at FROM conversations
                    ''', ('guest',))
                    
                    # Drop old table and rename new one
                    await conn.execute('DROP TABLE conversations')
                    await conn.execute('ALTER TABLE conversations_new RENAME TO conversations')
                    await conn.commit()
                    logger.info("Added user_id column to conversations table!")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")

async def get_chat_history_async(user_id: str, conversation_id: int | None = None, limit: int = 50):
    """Get chat history for a specific user and conversation"""
    async with aiosqlite.connect(DB_PATH) as conn:
        if conversation_id:
            # Verify the conversation belongs to the user
            cursor = await conn.execute(
                'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            cursor = await conn.execute(
                'SELECT user_message, bot_response, citations, timestamp FROM chat_history WHERE conversation_id = ? ORDER BY id DESC LIMIT ?',
                (conversation_id, limit)
            )
        else:
            # Get from most recent conversation for the user
            cursor = await conn.execute('''
                SELECT ch.user_message, ch.bot_response, ch.citations, ch.timestamp 
                FROM chat_history ch
                JOIN conversations c ON ch.conversation_id = c.id
                WHERE c.user_id = ?
                ORDER BY c.updated_at DESC, ch.id DESC
                LIMIT ?
            ''', (user_id, limit))
        
        rows = await cursor.fetchall()
        
        chat_history = []
        for row in rows:
            citations = []
            if row[2]:  # citations column
                try:
                    citations = json.loads(row[2])
                except json.JSONDecodeError:
                    citations = []
            
            chat_history.append({
                'user_message': row[0],
                'bot_response': row[1],
                'citations': citations,
                'timestamp': row[3]
            })
        return chat_history

async def save_chat_async(user_id: str, conversation_id: int, user_message: str, bot_response: str, citations: List[str]):
    """Save chat message for a specific user and conversation"""
    # Verify the conversation belongs to the user
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
            (conversation_id, user_id)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Save the chat message
        await conn.execute(
            'INSERT INTO chat_history (conversation_id, user_message, bot_response, citations, timestamp) VALUES (?, ?, ?, ?, ?)',
            (conversation_id, user_message, bot_response, json.dumps(citations), timestamp)
        )
        
        # Update conversation's updated_at timestamp
        await conn.execute(
            'UPDATE conversations SET updated_at = ? WHERE id = ? AND user_id = ?',
            (timestamp, conversation_id, user_id)
        )
        
        await conn.commit()

async def create_conversation_async(user_id: str, title: str | None = None) -> int:
    """Create a new conversation for a specific user and return its ID"""
    if not title:
        title = f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    timestamp = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            'INSERT INTO conversations (user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)',
            (user_id, title, timestamp, timestamp)
        )
        await conn.commit()
        
        # Get the ID of the newly created conversation
        cursor = await conn.execute('SELECT last_insert_rowid()')
        conversation_id = (await cursor.fetchone())[0]
        return conversation_id

async def get_conversations_async(user_id: str) -> List[dict]:
    """Get all conversations for a specific user"""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute('''
            SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(ch.id) as message_count, c.user_id
            FROM conversations c
            LEFT JOIN chat_history ch ON c.id = ch.conversation_id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        ''', (user_id,))
        
        rows = await cursor.fetchall()
        conversations = []
        for row in rows:
            conversations.append({
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'message_count': row[4],
                'user_id': row[5],
            })
        return conversations

async def update_conversation_title_async(user_id: str, conversation_id: int, title: str):
    """Update conversation title for a specific user and update the updated_at timestamp"""
    async with aiosqlite.connect(DB_PATH) as conn:
        # Ensure the conversation belongs to the user
        cursor = await conn.execute(
            'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
            (conversation_id, user_id)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        timestamp = datetime.datetime.now().isoformat()
        await conn.execute(
            'UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?',
            (title, timestamp, conversation_id, user_id)
        )
        await conn.commit()

async def delete_conversation_async(user_id: str, conversation_id: int):
    """Delete a conversation for a specific user"""
    async with aiosqlite.connect(DB_PATH) as conn:
        # Ensure the conversation belongs to the user
        cursor = await conn.execute(
            'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
            (conversation_id, user_id)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete associated chat history first
        await conn.execute('DELETE FROM chat_history WHERE conversation_id = ?', (conversation_id,))
        
        # Delete the conversation
        await conn.execute('DELETE FROM conversations WHERE id = ? AND user_id = ?', (conversation_id, user_id))
        await conn.commit()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db_async()
    await migrate_database_async()
    await setup_bedrock_clients()

# Load GPT4All model at startup
try:
    gpt4all_model = GPT4All("ggml-gpt4all-j-v1.3-groovy", model_path="/Users/jcascante/develop/gym-chatbot/")
except Exception as e:
    gpt4all_model = None
    logger.error(f"[Error loading GPT4All model: {e}]")

# Set up async Bedrock clients
bedrock_session = None

async def setup_bedrock_clients():
    """Setup async Bedrock clients"""
    global bedrock_session
    
    try:
        # Create async session for model invocation
        session = aioboto3.Session()
        bedrock_session = session.client(
            'bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        logger.info("Async Bedrock clients initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up async Bedrock clients: {e}")

async def retrieve_from_knowledge_base_async(query: str):
    """
    Retrieve relevant documents from the Bedrock Knowledge Base asynchronously
    Returns tuple of (documents, source_uris)
    """
    try:
        # Create a new session for each request to avoid coroutine reuse issues
        session = aioboto3.Session()
        async with session.client(
            'bedrock-agent-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        ) as client:
            response = await client.retrieve(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': MAX_RETRIEVAL_RESULTS
                    }
                }
            )
            
            # Extract retrieved passages and source URIs
            retrieved_passages = []
            source_uris = []
            seen_uris = set()  # Track seen URIs to avoid duplicates
            
            logger.debug(f"Retrieved {len(response.get('retrievalResults', []))} results from knowledge base")
            
            for i, result in enumerate(response.get('retrievalResults', [])):
                content = result.get('content', {})
                text = content.get('text', '')
                if text:
                    retrieved_passages.append(text)
                    
                    # Extract source URI if available
                    source_uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
                    if source_uri:
                        if source_uri not in seen_uris:
                            source_uris.append(source_uri)
                            seen_uris.add(source_uri)
                            logger.debug(f"Added source URI {i+1}: {source_uri}")
                        else:
                            logger.debug(f"Skipped duplicate URI {i+1}: {source_uri}")
                    else:
                        logger.debug(f"No source URI found for result {i+1}")
            
            logger.debug(f"Final unique source URIs: {source_uris}")
            return retrieved_passages, source_uris
    except Exception as e:
        logger.error(f"Error retrieving from knowledge base: {e}")
        return None, []

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message cannot be empty")
    conversation_id: int | None = None

class ChatResponse(BaseModel):
    response: str
    citations: List[str] = []
    conversation_id: int

class HistoryItem(BaseModel):
    user_message: str
    bot_response: str
    citations: List[str] = []
    timestamp: str

class ConversationItem(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int

class CreateConversationRequest(BaseModel):
    title: str | None = None

class CreateConversationResponse(BaseModel):
    conversation_id: int
    title: str

class UpdateConversationRequest(BaseModel):
    title: str

class UpdateConversationResponse(BaseModel):
    message: str

class DeleteConversationResponse(BaseModel):
    message: str

class ClearHistoryResponse(BaseModel):
    message: str

def format_source_uri(uri: str) -> str:
    """
    Format source URI to be more user-friendly
    Extracts filename from S3 URI or returns a readable version
    """
    if not uri:
        return "Unknown source"
    
    # Handle S3 URIs: s3://bucket-name/path/to/file.pdf
    if uri.startswith('s3://'):
        # Extract the filename from the path
        parts = uri.split('/')
        if len(parts) > 3:
            filename = parts[-1]  # Get the last part (filename)
            # Remove file extension for cleaner display
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]
            return filename.replace('_', ' ').replace('-', ' ')
        else:
            return uri.split('/')[-1] if uri.split('/')[-1] else "S3 Document"
    
    # Handle other URI formats
    elif uri.startswith('http'):
        # Extract domain or filename
        parts = uri.split('/')
        if len(parts) > 2:
            return parts[-1] if parts[-1] else parts[2]  # filename or domain
        else:
            return uri
    
    # Handle local file paths
    elif '/' in uri or '\\' in uri:
        filename = uri.split('/')[-1] if '/' in uri else uri.split('\\')[-1]
        if '.' in filename:
            filename = filename.rsplit('.', 1)[0]
        return filename.replace('_', ' ').replace('-', ' ')
    
    # Return as is if no special formatting needed
    return uri

def detect_language(text: str) -> str:
    """
    Simple language detection based on common words and characters
    Returns 'es' for Spanish, 'en' for English, 'en' as default
    """
    text_lower = text.lower()
    
    # Spanish indicators (more specific words)
    spanish_words = ['qué', 'cómo', 'dónde', 'cuándo', 'por qué', 'quién', 'cuál', 'cuáles', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas', 'con', 'para', 'por', 'sin', 'sobre', 'entre', 'hacia', 'desde', 'hasta', 'durante', 'según', 'mediante', 'contra', 'bajo', 'tras', 'ante', 'bajo', 'cabe', 'so', 'través', 'versus', 'vía', 'ejercicio', 'rutina', 'series', 'repeticiones', 'peso', 'fuerza', 'musculo', 'gimnasio', 'necesito', 'quiero', 'debo', 'puedo', 'debería']
    spanish_chars = ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü', '¿', '¡']
    
    # English indicators (more specific words)
    english_words = ['what', 'how', 'where', 'when', 'why', 'who', 'which', 'this', 'that', 'these', 'those', 'with', 'for', 'by', 'without', 'over', 'between', 'toward', 'from', 'until', 'during', 'according', 'through', 'against', 'under', 'exercise', 'training', 'routine', 'sets', 'repetitions', 'weight', 'strength', 'muscle', 'gym', 'need', 'want', 'should', 'can', 'could']
    
    # Check for Spanish words and characters
    spanish_word_count = sum(1 for word in spanish_words if word in text_lower)
    spanish_char_count = sum(1 for char in spanish_chars if char in text_lower)
    
    # Check for English words
    english_word_count = sum(1 for word in english_words if word in text_lower)
    
    # Calculate scores
    spanish_score = spanish_word_count + (spanish_char_count * 2)  # Give more weight to special characters
    english_score = english_word_count
    
    logger.debug(f"Language detection for '{text}': Spanish score={spanish_score}, English score={english_score}")
    
    # If we find clear Spanish indicators, return Spanish
    if spanish_score > 0:
        return 'es'
    
    # If we find clear English indicators, return English
    if english_score > 0:
        return 'en'
    
    # Default to English for unclear cases
    return 'en'

def get_conversation_language(user_message: str, chat_history: List[dict]) -> str:
    """
    Determine the language for the response based on current message and conversation history
    """
    # First, check if the current message has clear language indicators
    current_language = detect_language(user_message)
    logger.debug(f"Current message language detected: {current_language}")
    
    # Prioritize the current message language - if it's clearly Spanish or English, use that
    if current_language == 'es':
        logger.debug("Using Spanish based on current message")
        return 'es'
    elif current_language == 'en':
        logger.debug("Using English based on current message")
        return 'en'
    
    # If current message language is unclear, check recent conversation history
    # Look at the last few messages to see if we've been speaking Spanish
    recent_messages = chat_history[-3:] if len(chat_history) >= 3 else chat_history
    
    spanish_count = 0
    english_count = 0
    
    for msg in recent_messages:
        if msg.get('user_message'):
            lang = detect_language(msg['user_message'])
            if lang == 'es':
                spanish_count += 1
            else:
                english_count += 1
    
    logger.debug(f"History analysis: Spanish={spanish_count}, English={english_count}")
    
    # If we've been speaking Spanish recently, continue in Spanish
    if spanish_count > english_count:
        logger.debug("Using Spanish based on conversation history")
        return 'es'
    
    # Default to English
    logger.debug("Using English as default")
    return 'en'

def get_language_instruction(language: str) -> str:
    """
    Get language-specific instruction for the model
    """
    # Document structure instructions
    if language == 'es':
        document_structure = """
IMPORTANTE - ESTRUCTURA DE DOCUMENTOS DE PROGRAMACIÓN:
Los documentos de programaciones están estructurados de la siguiente manera:
- El nombre del documento es el nombre de la programación.
- El contenido del documento es el contenido de la programación.
- La estructura del documento es la siguiente:
    - La primera parte es el nombre de la programación seguido de una descripción de la programación y una guía básica de cómo usarla.
    - La segunda parte es una guía de calentamiento y estiramiento.
    - La tercera parte del documento es la programación en sí, con los ejercicios y las series y repeticiones. Está estructurado en tablas donde cada tabla es una semana y cada columna es un día, en el cual se detallan los ejercicios.
    - La cuarta parte es una "Guía de Programa", la cual explica el código de colores que se usa en la programación.
    - La quinta parte es una "Guía de Volumen". Específica por cada semana y por color el volumen de cada ejercicio. Repeticiones y sets.
    - Existe un codigo de colores que enlaza las diferentes tablas.

"""
        return f"{document_structure}Eres un experto en entrenamiento de fuerza y acondicionamiento físico con amplio conocimiento en programación de ejercicios, periodización, biomecánica y fisiología del ejercicio. IMPORTANTE: Usa ÚNICAMENTE la información proporcionada en los documentos de la base de conocimientos para responder. NO uses ningún conocimiento externo o general. Responde en español usando la información proporcionada arriba. Cuando hagas referencia a información de documentos específicos, cítalos por su número de origen [1], [2], etc. Proporciona consejos técnicos precisos y mantén el formato original con párrafos separados y estructura clara:"
    else:
        document_structure = """
IMPORTANT - PROGRAMMING DOCUMENT STRUCTURE:
The programming documents are structured as follows:
- The document name is the name of the programming.
- The document content is the content of the programming.
- The document structure is as follows:
    - The first part is the name of the programming followed by a description of the programming and a basic guide on how to use it.
    - The second part is a warm-up and stretching guide.
    - The third part of the document is the programming itself, with the exercises and sets and repetitions. It is structured in tables where each table is a week and each column is a day, in which the exercises are detailed.
    - The fourth part is a "Program Guide", which explains the color code used in the programming.
    - The fifth part is a "Volume Guide". It specifies for each week and by color the volume of each exercise. Repetitions and sets.
    - There is a color code that links the different tables.

"""
        return f"{document_structure}You are an expert in strength and conditioning training with extensive knowledge in exercise programming, periodization, biomechanics, and exercise physiology. IMPORTANT: Use ONLY the information provided in the knowledge base documents to answer. DO NOT use any external or general knowledge. Please answer the following question using the information provided above. When referencing information from specific documents, cite them by their source number [1], [2], etc. Provide precise technical advice and maintain the original formatting with separate paragraphs and clear structure:"

def format_response_text(response: str) -> str:
    """
    Post-process the response to ensure proper formatting
    """
    if not response:
        return response
    
    # Split into lines and clean up
    lines = response.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Check if line looks like a list item or exercise
            if (line.startswith(('•', '-', '*', '1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)', '0)')) or
                line.startswith(('A)', 'B)', 'C)', 'D)', 'E)', 'F)', 'G)', 'H)')) or
                line.startswith(('WEEK', 'DAY', 'CONDITIONING', 'GUÍA', 'INTENSITY', 'REST')) or
                line.startswith(('Sets:', 'Reps:', 'Time:', 'Target:'))):
                formatted_lines.append(line)
            elif line.startswith(('*', '_')) and line.endswith(('*', '_')):
                # Preserve italic text
                formatted_lines.append(line)
            elif len(line) > 100 and not line.startswith('|'):
                # Long lines that aren't tables - try to break into sentences
                sentences = line.split('. ')
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        if i == 0:
                            formatted_lines.append(sentence.strip())
                        else:
                            formatted_lines.append(sentence.strip())
            else:
                formatted_lines.append(line)
    
    # Join with proper spacing
    return '\n\n'.join(formatted_lines)

async def generate_response_with_context_async(user_message: str, retrieved_documents: List[str] | None, source_uris: List[str], chat_history: List[dict]):
    """
    Generate response using the model with retrieved documents as context (async)
    Returns tuple of (response, citations)
    """
    if bedrock_session is None:
        return "[Error: Bedrock client not initialized. Check server logs.]", []
    
    try:
        # Detect language based on conversation context, not just current message
        user_language = get_conversation_language(user_message, chat_history)
        language_instruction = get_language_instruction(user_language)
        
        # Build context from retrieved documents
        context = ""
        citations = []
        
        if retrieved_documents:
            if user_language == 'es':
                context = "Basándote en la siguiente información:\n\n"
            else:
                context = "Based on the following information:\n\n"
            
            # First, create the unique citations mapping to ensure consistent numbering
            unique_citations = {}
            for uri in source_uris:
                formatted_name = format_source_uri(uri)
                if formatted_name not in unique_citations:
                    unique_citations[formatted_name] = uri
            
            # Create a mapping from URI to citation number for consistent referencing
            uri_to_citation_number = {}
            for i, (formatted_name, uri) in enumerate(unique_citations.items(), 1):
                uri_to_citation_number[uri] = i
            
            # Group documents by source URI to assign consistent document numbers
            doc_groups = {}
            for i, doc in enumerate(retrieved_documents):
                if i < len(source_uris):
                    uri = source_uris[i]
                    if uri not in doc_groups:
                        doc_groups[uri] = []
                    doc_groups[uri].append(doc)
            
            # Build context with grouped documents using the same numbering as citations
            for uri, docs in doc_groups.items():
                citation_number = uri_to_citation_number.get(uri, 1)
                context += f"[{citation_number}]:\n"
                for doc in docs:
                    context += f"{doc}\n\n"
            
            # Add source URIs to context for reference with matching numbers
            if source_uris:
                if user_language == 'es':
                    context += "Documentos fuente:\n"
                else:
                    context += "Source documents:\n"
                
                for uri in unique_citations.values():
                    citation_number = uri_to_citation_number.get(uri, 1)
                    formatted_name = format_source_uri(uri)
                    context += f"[{citation_number}]: {formatted_name}\n"
                context += "\n"
            
            # Add language instruction first (more prominent)
            context += f"{language_instruction}\n\n"
            
            # Add formatting instructions
            if user_language == 'es':
                context += "IMPORTANTE: Al responder como experto en entrenamiento de fuerza y acondicionamiento, mantén el formato original del texto. Usa párrafos separados, listas con viñetas para ejercicios y series, y preserva la estructura de tablas de entrenamiento, rutinas y progresiones. Organiza la información de manera clara: ejercicios, series, repeticiones, descansos, intensidad y progresión. No combines todo en un solo párrafo.\n\n"
            else:
                context += "IMPORTANT: When responding as a strength and conditioning expert, maintain the original text formatting. Use separate paragraphs, bullet points for exercises and sets, and preserve the structure of training tables, routines, and progressions. Organize information clearly: exercises, sets, repetitions, rest periods, intensity, and progression. Do not combine everything into a single paragraph.\n\n"
        else:
            if user_language == 'es':
                context = "Por favor responde la siguiente pregunta. Si no tienes información específica sobre este tema, por favor indícalo:\n\n"
            else:
                context = "Please answer the following question. If you don't have specific information about this topic, please say so:\n\n"
        
        # Build conversation history context
        conversation_context = ""
        if chat_history:
            if user_language == 'es':
                conversation_context = "Historial de la conversación:\n"
            else:
                conversation_context = "Conversation history:\n"
            
            # Include last 10 messages for context (to avoid token limits)
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            
            for msg in recent_history:
                conversation_context += f"Usuario: {msg['user_message']}\n"
                conversation_context += f"Asistente: {msg['bot_response']}\n\n"
            
            conversation_context += "---\n\n"
        
        # Create the full prompt with conversation history
        full_prompt = f"{context}{conversation_context}{user_message}"
        
        # Add explicit language instruction at the end
        if user_language == 'es':
            full_prompt += "\n\nIMPORTANTE: Responde ÚNICAMENTE en español. NO uses inglés en tu respuesta."
        else:
            full_prompt += "\n\nIMPORTANT: Respond ONLY in English. DO NOT use Spanish in your response."
        
        logger.debug(f"User language detected: {user_language}")
        logger.debug(f"Full prompt: {full_prompt}")
        
        # Handle different model types and API versions
        if BEDROCK_MODEL_ID and 'claude-3' in BEDROCK_MODEL_ID:
            # Claude 3 models use Messages API
            # Note: Claude 3 Haiku doesn't support system messages, so we include language instruction in user message
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_TOKENS_TO_SAMPLE,
                "temperature": TEMPERATURE,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            })
        elif BEDROCK_MODEL_ID and 'anthropic' in BEDROCK_MODEL_ID:
            # Older Claude models use the old format
            prompt = f"Human: {full_prompt}\nAssistant:"
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": MAX_TOKENS_TO_SAMPLE,
                "temperature": TEMPERATURE
            })
        elif BEDROCK_MODEL_ID and 'amazon' in BEDROCK_MODEL_ID:
            # Amazon models (Titan)
            body = json.dumps({
                "inputText": full_prompt,
                "textGenerationConfig": {
                    "maxTokenCount": MAX_TOKENS_TO_SAMPLE,
                    "temperature": TEMPERATURE
                }
            })
        else:
            # Default to Anthropic format
            prompt = f"Human: {full_prompt}\nAssistant:"
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": MAX_TOKENS_TO_SAMPLE,
                "temperature": TEMPERATURE
            })
        
        # Use synchronous boto3 client for model invocation to avoid coroutine issues
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=body
        )
        
        # Read the response body
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Extract response based on model type
        if BEDROCK_MODEL_ID and 'claude-3' in BEDROCK_MODEL_ID:
            # Claude 3 Messages API response format
            bot_response = response_body.get('content', [{}])[0].get('text', '').strip()
        elif BEDROCK_MODEL_ID and 'anthropic' in BEDROCK_MODEL_ID:
            bot_response = response_body.get('completion', '').strip()
        elif BEDROCK_MODEL_ID and 'amazon' in BEDROCK_MODEL_ID:
            bot_response = response_body.get('results', [{}])[0].get('outputText', '').strip()
        else:
            bot_response = response_body.get('completion', '').strip()
        
        if not bot_response:
            if user_language == 'es':
                bot_response = 'Lo siento, no pude generar una respuesta.'
            else:
                bot_response = 'Sorry, I could not generate a response.'
        
        # Post-process the response
        formatted_response = format_response_text(bot_response)
        
        # Return unique source URIs as citations with index-to-file mapping
        # Use the same unique_citations mapping that was created earlier for consistency
        if 'unique_citations' in locals():
            # Format citations for display with index-to-file mapping
            formatted_citations = []
            for i, (formatted_name, uri) in enumerate(unique_citations.items(), 1):
                formatted_citations.append(f"[{i}] - {formatted_name}")
        else:
            # Fallback to the original logic if unique_citations wasn't created
            unique_citations = {}
            logger.debug(f"Original source_uris: {source_uris}")
            
            for uri in source_uris:
                formatted_name = format_source_uri(uri)
                if formatted_name not in unique_citations:
                    unique_citations[formatted_name] = uri
                    logger.debug(f"Added citation: {formatted_name} -> {uri}")
                else:
                    logger.debug(f"Skipped duplicate: {formatted_name} (already exists)")
            
            # Format citations for display with index-to-file mapping
            formatted_citations = []
            for i, (formatted_name, uri) in enumerate(unique_citations.items(), 1):
                formatted_citations.append(f"[{i}] - {formatted_name}")
        
        logger.debug(f"Final formatted citations: {formatted_citations}")
        
        return formatted_response, formatted_citations
    except Exception as e:
        if user_language == 'es':
            return f"[Error: No se pudo generar respuesta desde Bedrock: {e}]", []
        else:
            return f"[Error: Could not generate response from Bedrock: {e}]", []

@app.post('/auth/register', response_model=TokenResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    # Check if username already exists
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    user_id = await create_user(user_data.username, user_data.password, user_data.email)
    
    # Get the created user
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            is_guest=user['is_guest'],
            created_at=user['created_at']
        )
    )

@app.post('/auth/login', response_model=TokenResponse)
async def login_user(user_data: UserLogin):
    """Login user with username and password"""
    user = await authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user['id']})
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            is_guest=user['is_guest'],
            created_at=user['created_at']
        )
    )

@app.post('/auth/guest', response_model=TokenResponse)
async def create_guest_session_endpoint():
    """Create a persistent guest session with session code"""
    guest_session = await create_persistent_guest_session()
    
    # Create access token with guest user ID
    access_token = create_access_token(data={
        "sub": guest_session['user_id'], 
        "username": guest_session['username'], 
        "is_guest": True
    })
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=guest_session['expires_at'],
        user=UserResponse(
            id=guest_session['user_id'],
            username=guest_session['username'],
            email=None,
            is_guest=True,
            created_at=guest_session['created_at']
        ),
        session_code=guest_session['session_code']  # Include session code in response
    )

@app.post('/auth/guest/join', response_model=TokenResponse)
async def join_guest_session(session_code: str):
    """Join an existing guest session using session code"""
    guest_session = await get_guest_session_by_code(session_code)
    if not guest_session:
        raise HTTPException(status_code=404, detail="Invalid or expired session code")
    
    # Create access token with guest user ID
    access_token = create_access_token(data={
        "sub": guest_session['user_id'], 
        "username": guest_session['username'], 
        "is_guest": True
    })
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=guest_session['expires_at'],
        user=UserResponse(
            id=guest_session['user_id'],
            username=guest_session['username'],
            email=None,
            is_guest=True,
            created_at=guest_session['created_at']
        )
    )

@app.get('/auth/me', response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user['id'],
        username=current_user['username'],
        email=current_user['email'],
        is_guest=current_user['is_guest'],
        created_at=current_user['created_at']
    )

@app.post('/chat', response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest, current_user = Depends(get_current_user)):
    """Send a message and get an AI response"""
    user_id = current_user['id']
    conversation_id = chat_request.conversation_id
    
    # If no conversation_id provided, create a new conversation
    if not conversation_id:
        conversation_id = await create_conversation_async(user_id, None)
    
    # Get recent conversation history for language context
    chat_history = await get_chat_history_async(user_id, conversation_id, 10)
    
    # Step 1: Retrieve relevant documents from knowledge base
    retrieved_documents, source_uris = await retrieve_from_knowledge_base_async(chat_request.message)
    
    # Step 2: Generate response
    bot_response, citations = await generate_response_with_context_async(
        chat_request.message, retrieved_documents, source_uris, chat_history
    )
    
    # Step 3: Store in database
    await save_chat_async(user_id, conversation_id, chat_request.message, bot_response, citations)
    
    return {"response": bot_response, "citations": citations, "conversation_id": conversation_id}

@app.get('/conversations', response_model=List[ConversationItem])
async def get_conversations(current_user = Depends(get_current_user)):
    """Get list of all conversations for the current user"""
    user_id = current_user['id']
    conversations = await get_conversations_async(user_id)
    return conversations

@app.post('/conversations', response_model=CreateConversationResponse)
async def create_conversation(request: CreateConversationRequest, current_user = Depends(get_current_user)):
    """Create a new conversation"""
    user_id = current_user['id']
    conversation_id = await create_conversation_async(user_id, request.title)
    conversations = await get_conversations_async(user_id)
    new_conversation = next((c for c in conversations if c['id'] == conversation_id), None)
    
    return CreateConversationResponse(
        conversation_id=conversation_id,
        title=new_conversation['title'] if new_conversation else "New Conversation"
    )

@app.get('/conversations/{conversation_id}/history', response_model=List[HistoryItem])
async def get_conversation_history(conversation_id: int, current_user = Depends(get_current_user)):
    """Get chat history for a specific conversation"""
    user_id = current_user['id']
    chat_history = await get_chat_history_async(user_id, conversation_id, 50)
    
    history_items = []
    for msg in chat_history:
        history_items.append(HistoryItem(
            user_message=msg['user_message'],
            bot_response=msg['bot_response'],
            citations=msg['citations'],
            timestamp=msg['timestamp']
        ))
    
    return history_items

@app.put('/conversations/{conversation_id}', response_model=UpdateConversationResponse)
async def update_conversation(conversation_id: int, request: UpdateConversationRequest, current_user = Depends(get_current_user)):
    """Update conversation title"""
    user_id = current_user['id']
    await update_conversation_title_async(user_id, conversation_id, request.title)
    return UpdateConversationResponse(message="Conversation updated successfully")

@app.delete('/conversations/{conversation_id}', response_model=DeleteConversationResponse)
async def delete_conversation(conversation_id: int, current_user = Depends(get_current_user)):
    """Delete a conversation and all its messages"""
    user_id = current_user['id']
    await delete_conversation_async(user_id, conversation_id)
    return DeleteConversationResponse(message="Conversation deleted successfully")

@app.get('/history', response_model=List[HistoryItem])
async def get_history(current_user = Depends(get_current_user)):
    """Get history from the most recent conversation (for backward compatibility)"""
    user_id = current_user['id']
    chat_history = await get_chat_history_async(user_id, limit=50)
    
    history_items = []
    for msg in chat_history:
        history_items.append(HistoryItem(
            user_message=msg['user_message'],
            bot_response=msg['bot_response'],
            citations=msg['citations'],
            timestamp=msg['timestamp']
        ))
    
    return history_items

@app.delete('/history', response_model=ClearHistoryResponse)
async def clear_history():
    """Clear all chat history from the database"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute('DELETE FROM chat_history')
            await conn.commit()
        return ClearHistoryResponse(message="Chat history cleared successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

async def clear_database_async():
    """Utility function to clear the database table asynchronously"""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('DELETE FROM chat_history')
        await conn.commit()
    logger.info("Database cleared successfully")

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@app.post('/auth/change_password')
async def change_password(username: str = Body(...), new_password: str = Body(...)):
    """Change a user's password (for admin/testing)"""
    async with aiosqlite.connect(DB_PATH) as conn:
        password_hash = hash_password(new_password)
        await conn.execute(
            'UPDATE users SET password_hash = ?, updated_at = ? WHERE username = ?',
            (password_hash, datetime.datetime.utcnow().isoformat(), username)
        )
        await conn.commit()
    return {"message": "Password updated"} 