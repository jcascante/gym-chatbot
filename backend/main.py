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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        citations TEXT,
        timestamp TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

# Run database migration to add citations column if needed
def migrate_database():
    """Add citations column to existing chat_history table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if citations column exists
        c.execute("PRAGMA table_info(chat_history)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'citations' not in columns:
            logger.info("Adding citations column to chat_history table...")
            c.execute("ALTER TABLE chat_history ADD COLUMN citations TEXT")
            conn.commit()
            logger.info("Migration completed successfully!")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")

migrate_database()

# Load GPT4All model at startup
try:
    gpt4all_model = GPT4All("ggml-gpt4all-j-v1.3-groovy", model_path="/Users/jcascante/develop/gym-chatbot/")
except Exception as e:
    gpt4all_model = None
    logger.error(f"[Error loading GPT4All model: {e}]")

# Set up Bedrock client for model inference
try:
    bedrock = boto3.client(
        'bedrock-runtime',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
except Exception as e:
    bedrock = None
    logger.error(f"[Error setting up Bedrock client: {e}]")

# Set up Bedrock agent client for knowledge base retrieval
try:
    bedrock_agent = boto3.client(
        'bedrock-agent-runtime',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
except Exception as e:
    bedrock_agent = None
    logger.error(f"[Error setting up Bedrock agent client: {e}]")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    citations: List[str] = []

class HistoryItem(BaseModel):
    user_message: str
    bot_response: str
    citations: List[str] = []
    timestamp: str

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

def retrieve_from_knowledge_base(query: str):
    """
    Retrieve relevant documents from the Bedrock Knowledge Base
    Returns tuple of (documents, source_uris)
    """
    if bedrock_agent is None:
        return None, []
    
    try:
        response = bedrock_agent.retrieve(
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

def generate_response_with_context(user_message: str, retrieved_documents: List[str] | None, source_uris: List[str], chat_history: List[dict]):
    """
    Generate response using the model with retrieved documents as context
    Returns tuple of (response, citations)
    """
    if bedrock is None:
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
        
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=body
        )
        response_body = json.loads(response['body'].read())
        
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
def chat_endpoint(chat_request: ChatRequest):
    user_message = chat_request.message
    
    # Get recent conversation history for language context
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_message, bot_response, citations, timestamp FROM chat_history ORDER BY id DESC LIMIT 5')
    rows = c.fetchall()
    conn.close()
    
    # Convert to list of dicts for language detection
    chat_history = []
    for row in rows:
        chat_history.append({
            'user_message': row[0],
            'bot_response': row[1],
            'citations': row[2],
            'timestamp': row[3]
        })
    chat_history.reverse()  # Put in chronological order
    
    # Step 1: Retrieve relevant documents from knowledge base
    retrieved_documents, source_uris = retrieve_from_knowledge_base(user_message)
    
    # Step 2: Generate response using retrieved documents as context
    bot_response, citations = generate_response_with_context(user_message, retrieved_documents, source_uris, chat_history)
    
    # Step 3: Store in database
    timestamp = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (user_message, bot_response, citations, timestamp) VALUES (?, ?, ?, ?)',
              (user_message, bot_response, json.dumps(citations), timestamp))
    conn.commit()
    conn.close()
    
    return {"response": bot_response, "citations": citations}

@app.get('/history', response_model=List[HistoryItem])
def get_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_message, bot_response, citations, timestamp FROM chat_history ORDER BY id DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    history_items = []
    for row in rows:
        citations = []
        if row[2]:  # citations column
            try:
                citations = json.loads(row[2])
            except json.JSONDecodeError:
                citations = []
        
        history_items.append(HistoryItem(
            user_message=row[0], 
            bot_response=row[1], 
            citations=citations,
            timestamp=row[3]
        ))
    
    return history_items

@app.delete('/history')
def clear_history():
    """Clear all chat history from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM chat_history')
        conn.commit()
        conn.close()
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

def clear_database():
    """Utility function to clear the database table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM chat_history')
    conn.commit()
    conn.close()
    logger.info("Database cleared successfully") 