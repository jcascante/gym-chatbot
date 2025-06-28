# Gym Chatbot Backend with AWS Bedrock Knowledge Base

This backend implements a Retrieval-Augmented Generation (RAG) system using AWS Bedrock Knowledge Base for document retrieval and Claude for response generation.

## Features

- **Document Retrieval**: Uses AWS Bedrock Knowledge Base to retrieve relevant documents based on user queries
- **RAG Implementation**: Combines retrieved documents with the language model for context-aware responses
- **Multilingual Support**: Automatically detects user language and responds in the same language (English/Spanish)
- **Citation Tracking**: Automatically tracks and displays which documents were used to generate each response
- **Chat History**: Stores conversation history in SQLite database with citation information
- **RESTful API**: FastAPI-based endpoints for chat and history retrieval

## Prerequisites

1. **AWS Account** with Bedrock access
2. **AWS Bedrock Knowledge Base** created and populated with documents
3. **Python 3.8+** with pip

## Security Setup

**⚠️ IMPORTANT: Never commit AWS credentials to version control!**

1. **Copy the environment template:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` with your actual credentials:**
   ```bash
   # AWS Configuration
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_actual_access_key_here
   AWS_SECRET_ACCESS_KEY=your_actual_secret_key_here
   
   # Knowledge Base Configuration
   KNOWLEDGE_BASE_ID=your_actual_knowledge_base_id
   ```

3. **Verify `.env` is in `.gitignore** (it should be automatically ignored)

4. **Alternative: Set environment variables directly:**
   ```bash
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"
   export KNOWLEDGE_BASE_ID="your_kb_id"
   ```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure AWS Bedrock Knowledge Base

1. Go to AWS Bedrock console
2. Navigate to "Knowledge bases" in the left sidebar
3. Create a new knowledge base or use an existing one
4. Upload your documents (PDFs, text files, etc.)
5. Wait for the knowledge base to be ready (status should be "Active")

### 3. Update Configuration

Edit `config.py` and replace the placeholder values:

```python
# Replace with your actual Knowledge Base ID
KNOWLEDGE_BASE_ID = 'your-actual-knowledge-base-id'

# Update AWS credentials if needed
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
```

### 4. Set Environment Variables (Optional)

You can also set the Knowledge Base ID as an environment variable:

```bash
export KNOWLEDGE_BASE_ID="your-knowledge-base-id"
```

### 5. Run the Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /chat
Send a message and get a response with retrieved context and citations.

**Request:**
```json
{
  "message": "What are the benefits of strength training?"
}
```

**Response:**
```json
{
  "response": "Based on the information in our knowledge base, strength training offers several benefits including increased muscle mass, improved bone density, and enhanced metabolism. Additionally, it can help with weight management and overall physical performance.",
  "citations": ["PT101TimLOCarticle08", "Strength Training Guide"]
}
```

### GET /history
Retrieve chat history (last 50 messages) with citation information.

**Response:**
```json
[
  {
    "user_message": "What are the benefits of strength training?",
    "bot_response": "Based on the information in our knowledge base...",
    "citations": ["PT101TimLOCarticle08", "Strength Training Guide"],
    "timestamp": "2024-01-15T10:30:00"
  }
]
```

## How It Works

1. **Query Processing**: User message is received via the `/chat` endpoint
2. **Document Retrieval**: The system queries the AWS Bedrock Knowledge Base using vector search
3. **Source Tracking**: Each retrieved document's source URI is tracked and formatted for display
4. **Context Building**: Retrieved documents are formatted as context for the language model
5. **Response Generation**: Claude generates a response using the retrieved context
6. **Citation Storage**: Unique source URIs are stored as citations (duplicates are automatically removed)
7. **Storage**: The conversation is stored in the SQLite database with citation information

## Citation System

The system automatically tracks and displays the source documents used to generate each response:

- **Source URIs**: Extracted from the knowledge base retrieval results
- **Formatting**: URIs are formatted to show readable document names (e.g., "PT101TimLOCarticle08" instead of "s3://bucket/path/PT101TimLOCarticle08.pdf")
- **Deduplication**: Duplicate sources are automatically removed from citations
- **Display**: Citations appear below each bot response in the frontend

## Multilingual Support

The system automatically detects the language of user questions and responds in the same language:

- **Language Detection**: Uses common Spanish words and characters to detect if the question is in Spanish
- **Automatic Response**: Responds in Spanish for Spanish questions, English for English questions
- **Context Adaptation**: Provides context and instructions in the detected language
- **Citation Labels**: Displays citation labels in the appropriate language ("Fuentes:" for Spanish, "Sources:" for English)

**Supported Languages:**
- English (default)
- Spanish (detected automatically)

**Example:**
- User asks: "¿Cuáles son los beneficios del entrenamiento de fuerza?"
- Bot responds in Spanish with Spanish citations
- User asks: "What are the benefits of strength training?"
- Bot responds in English with English citations

## Configuration Options

In `config.py`, you can adjust:

- `MAX_RETRIEVAL_RESULTS`: Number of documents to retrieve (default: 3)
- `MAX_TOKENS_TO_SAMPLE`: Maximum tokens for response generation (default: 500)
- `TEMPERATURE`: Response creativity (0.0-1.0, default: 0.7)
- `BEDROCK_MODEL_ID`: The Bedrock model to use (default: anthropic.claude-v2:1)

## Troubleshooting

### Common Issues

1. **Knowledge Base Not Found**: Ensure your Knowledge Base ID is correct and the knowledge base is active
2. **AWS Credentials Error**: Verify your AWS credentials have Bedrock permissions
3. **No Documents Retrieved**: Check if your knowledge base has documents and they're properly indexed
4. **Environment Variables Not Loaded**: Make sure your `.env` file exists and has the correct format

### Error Messages

- `[Error: Bedrock client not initialized]`: AWS credentials or region issue
- `[Error: Bedrock agent client not initialized]`: Knowledge base access issue
- `[Error retrieving from knowledge base]`: Knowledge base query failed
- `[Error: Could not generate response from Bedrock]`: Model access or configuration issue

## Security Notes

- Store AWS credentials securely (consider using AWS IAM roles or environment variables)
- The current implementation stores credentials in code for development - use proper secret management for production
- Consider implementing rate limiting and authentication for production use

## Next Steps

- Add authentication and authorization
- Implement streaming responses
- Add support for multiple knowledge bases
- Implement conversation memory/context
- Add response quality metrics and feedback 