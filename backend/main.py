from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Async database operations
async def init_db_async():
    """Initialize database asynchronously"""
    async with aiosqlite.connect(DB_PATH) as conn:
        # Create conversations table
        await conn.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
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
    """Migrate database schema for conversation support"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # Check if conversations table exists
            cursor = await conn.execute("PRAGMA table_info(conversations)")
            conversations_columns = [column[1] async for column in cursor]
            
            if not conversations_columns:
                logger.info("Creating conversations table...")
                await conn.execute('''CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )''')
                
                # Create default conversation for existing data
                now = datetime.datetime.now().isoformat()
                await conn.execute(
                    'INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)',
                    ('Default Conversation', now, now)
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
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")

async def get_chat_history_async(conversation_id: int | None = None, limit: int = 50):
    """Get chat history for a specific conversation asynchronously"""
    async with aiosqlite.connect(DB_PATH) as conn:
        if conversation_id:
            cursor = await conn.execute(
                'SELECT user_message, bot_response, citations, timestamp FROM chat_history WHERE conversation_id = ? ORDER BY id ASC LIMIT ?',
                (conversation_id, limit)
            )
        else:
            # Get from most recent conversation
            cursor = await conn.execute('''
                SELECT ch.user_message, ch.bot_response, ch.citations, ch.timestamp 
                FROM chat_history ch
                JOIN conversations c ON ch.conversation_id = c.id
                ORDER BY c.updated_at DESC, ch.id ASC
                LIMIT ?
            ''', (limit,))
        
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

async def save_chat_async(conversation_id: int, user_message: str, bot_response: str, citations: List[str]):
    """Save chat message asynchronously with conversation ID"""
    timestamp = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        # Save the chat message
        await conn.execute(
            'INSERT INTO chat_history (conversation_id, user_message, bot_response, citations, timestamp) VALUES (?, ?, ?, ?, ?)',
            (conversation_id, user_message, bot_response, json.dumps(citations), timestamp)
        )
        
        # Update conversation's updated_at timestamp
        await conn.execute(
            'UPDATE conversations SET updated_at = ? WHERE id = ?',
            (timestamp, conversation_id)
        )
        
        await conn.commit()

async def create_conversation_async(title: str | None = None) -> int:
    """Create a new conversation and return its ID"""
    if not title:
        title = f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    timestamp = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            'INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)',
            (title, timestamp, timestamp)
        )
        await conn.commit()
        
        # Get the ID of the newly created conversation
        cursor = await conn.execute('SELECT last_insert_rowid()')
        conversation_id = (await cursor.fetchone())[0]
        return conversation_id

async def get_conversations_async() -> List[dict]:
    """Get list of all conversations with their metadata"""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute('''
            SELECT c.id, c.title, c.created_at, c.updated_at,
                   COUNT(ch.id) as message_count
            FROM conversations c
            LEFT JOIN chat_history ch ON c.id = ch.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        ''')
        
        rows = await cursor.fetchall()
        conversations = []
        for row in rows:
            conversations.append({
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'message_count': row[4]
            })
        return conversations

async def update_conversation_title_async(conversation_id: int, title: str):
    """Update the title of a conversation"""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            'UPDATE conversations SET title = ? WHERE id = ?',
            (title, conversation_id)
        )
        await conn.commit()

async def delete_conversation_async(conversation_id: int):
    """Delete a conversation and all its messages"""
    async with aiosqlite.connect(DB_PATH) as conn:
        # Delete all messages in the conversation
        await conn.execute('DELETE FROM chat_history WHERE conversation_id = ?', (conversation_id,))
        # Delete the conversation
        await conn.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
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
bedrock_agent_session = None

async def setup_bedrock_clients():
    """Setup async Bedrock clients"""
    global bedrock_session, bedrock_agent_session
    
    try:
        # Create async session
        session = aioboto3.Session()
        bedrock_session = session.client(
            'bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        bedrock_agent_session = session.client(
            'bedrock-agent-runtime',
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
    if bedrock_agent_session is None:
        return None, []
    
    try:
        async with bedrock_agent_session as client:
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
            
            for result in response.get('retrievalResults', []):
                content = result.get('content', {})
                text = content.get('text', '')
                if text:
                    retrieved_passages.append(text)
                    
                    # Extract source URI if available
                    source_uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
                    if source_uri and source_uri not in source_uris:
                        source_uris.append(source_uri)
            
            return retrieved_passages, source_uris
    except Exception as e:
        logger.error(f"Error retrieving from knowledge base: {e}")
        return None, []

class ChatRequest(BaseModel):
    message: str
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
    
    # Spanish indicators
    spanish_words = ['qué', 'cómo', 'dónde', 'cuándo', 'por qué', 'quién', 'cuál', 'cuáles', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas', 'con', 'para', 'por', 'sin', 'sobre', 'entre', 'hacia', 'desde', 'hasta', 'durante', 'según', 'mediante', 'contra', 'bajo', 'tras', 'ante', 'bajo', 'cabe', 'so', 'través', 'versus', 'vía']
    spanish_chars = ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü', '¿', '¡']
    
    # Check for Spanish words
    spanish_word_count = sum(1 for word in spanish_words if word in text_lower)
    
    # Check for Spanish characters
    spanish_char_count = sum(1 for char in spanish_chars if char in text_lower)
    
    # If we find Spanish indicators, return Spanish
    if spanish_word_count > 0 or spanish_char_count > 0:
        return 'es'
    
    return 'en'  # Default to English

def get_conversation_language(user_message: str, chat_history: List[dict]) -> str:
    """
    Determine the language for the response based on current message and conversation history
    """
    # First, check if the current message has clear language indicators
    current_language = detect_language(user_message)
    
    # If current message is clearly Spanish, use Spanish
    if current_language == 'es':
        return 'es'
    
    # If current message is English, check recent conversation history
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
    
    # If we've been speaking Spanish recently, continue in Spanish
    if spanish_count > english_count:
        return 'es'
    
    # Default to English
    return 'en'

def get_language_instruction(language: str) -> str:
    """
    Get language-specific instruction for the model
    """
    if language == 'es':
        return "Por favor responde en español usando la información proporcionada arriba. Cuando hagas referencia a información de documentos específicos, cítalos por su URI de origen:"
    else:
        return "Please answer the following question using the information provided above. When referencing information from specific documents, cite them by their source URI:"

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
                
            for i, doc in enumerate(retrieved_documents, 1):
                context += f"Document {i}:\n{doc}\n\n"
            
            # Add source URIs to context for reference
            if source_uris:
                if user_language == 'es':
                    context += "Documentos fuente:\n"
                else:
                    context += "Source documents:\n"
                for i, uri in enumerate(source_uris, 1):
                    context += f"Document {i}: {format_source_uri(uri)}\n"
                context += "\n"
            
            context += f"{language_instruction}\n\n"
        else:
            if user_language == 'es':
                context = "Por favor responde la siguiente pregunta. Si no tienes información específica sobre este tema, por favor indícalo:\n\n"
            else:
                context = "Please answer the following question. If you don't have specific information about this topic, please say so:\n\n"
        
        # Create the full prompt
        full_prompt = f"{context}{user_message}"
        
        # Handle different model types and API versions
        if BEDROCK_MODEL_ID and 'claude-3' in BEDROCK_MODEL_ID:
            # Claude 3 models use Messages API
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
        
        # Return unique source URIs as citations
        citations = list(set(source_uris))  # Remove duplicates
        # Format citations for display
        formatted_citations = [format_source_uri(uri) for uri in citations]
        
        return bot_response, formatted_citations
    except Exception as e:
        if user_language == 'es':
            return f"[Error: No se pudo generar respuesta desde Bedrock: {e}]", []
        else:
            return f"[Error: Could not generate response from Bedrock: {e}]", []

@app.post('/chat', response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    user_message = chat_request.message
    conversation_id = chat_request.conversation_id
    
    # If no conversation_id provided, create a new conversation
    if not conversation_id:
        conversation_id = await create_conversation_async()
    
    # Get recent conversation history for language context
    chat_history = await get_chat_history_async(conversation_id, 5)
    
    # Step 1: Retrieve relevant documents from knowledge base
    retrieved_documents, source_uris = await retrieve_from_knowledge_base_async(user_message)
    
    # Step 2: Generate response using retrieved documents as context
    bot_response, citations = await generate_response_with_context_async(user_message, retrieved_documents, source_uris, chat_history)
    
    # Step 3: Store in database
    await save_chat_async(conversation_id, user_message, bot_response, citations)
    
    return {"response": bot_response, "citations": citations, "conversation_id": conversation_id}

@app.get('/conversations', response_model=List[ConversationItem])
async def get_conversations():
    """Get list of all conversations"""
    conversations = await get_conversations_async()
    return conversations

@app.post('/conversations', response_model=CreateConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation"""
    conversation_id = await create_conversation_async(request.title)
    conversations = await get_conversations_async()
    new_conversation = next((c for c in conversations if c['id'] == conversation_id), None)
    
    if new_conversation:
        return CreateConversationResponse(
            conversation_id=conversation_id,
            title=new_conversation['title']
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

@app.get('/conversations/{conversation_id}/history', response_model=List[HistoryItem])
async def get_conversation_history(conversation_id: int):
    """Get chat history for a specific conversation"""
    chat_history = await get_chat_history_async(conversation_id, 50)
    
    history_items = []
    for item in chat_history:
        history_items.append(HistoryItem(
            user_message=item['user_message'],
            bot_response=item['bot_response'],
            citations=item['citations'],
            timestamp=item['timestamp']
        ))
    
    return history_items

@app.put('/conversations/{conversation_id}')
async def update_conversation(conversation_id: int, request: UpdateConversationRequest):
    """Update conversation title"""
    await update_conversation_title_async(conversation_id, request.title)
    return {"message": "Conversation updated successfully"}

@app.delete('/conversations/{conversation_id}')
async def delete_conversation(conversation_id: int):
    """Delete a conversation and all its messages"""
    await delete_conversation_async(conversation_id)
    return {"message": "Conversation deleted successfully"}

@app.get('/history', response_model=List[HistoryItem])
async def get_history():
    """Get history from the most recent conversation (for backward compatibility)"""
    chat_history = await get_chat_history_async(limit=50)
    
    history_items = []
    for item in chat_history:
        history_items.append(HistoryItem(
            user_message=item['user_message'],
            bot_response=item['bot_response'],
            citations=item['citations'],
            timestamp=item['timestamp']
        ))
    
    return history_items

@app.delete('/history')
async def clear_history():
    """Clear all chat history from the database"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute('DELETE FROM chat_history')
            await conn.commit()
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

async def clear_database_async():
    """Utility function to clear the database table asynchronously"""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('DELETE FROM chat_history')
        await conn.commit()
    logger.info("Database cleared successfully") 