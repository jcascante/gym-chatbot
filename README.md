# Gym AI Chatbot

A multilingual chatbot for fitness and gym-related questions, powered by AWS Bedrock Knowledge Base and Claude AI.

## Features

- 🤖 **AI-Powered Responses**: Uses AWS Bedrock Claude models for intelligent responses
- 📚 **Knowledge Base Integration**: Retrieves relevant information from your custom knowledge base
- 🌍 **Multilingual Support**: Automatically detects and responds in English or Spanish
- 📖 **Citation Tracking**: Shows which documents were used to generate each response
- 💬 **Chat History**: Maintains conversation history with persistent storage
- 🎨 **Modern UI**: Clean, responsive React frontend
- 🔒 **Secure**: Environment-based configuration for sensitive data

## Architecture

```
gym-chatbot/
├── backend/          # FastAPI backend with RAG implementation
├── frontend/         # React frontend with chat interface
└── data/            # Knowledge base documents
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- AWS Account with Bedrock access
- AWS Bedrock Knowledge Base

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd gym-chatbot
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your AWS credentials and knowledge base ID
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Run the Application

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit `http://localhost:5173` to use the chatbot!

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Knowledge Base Configuration
KNOWLEDGE_BASE_ID=your_knowledge_base_id_here

# Optional: Customize behavior
MAX_RETRIEVAL_RESULTS=3
MAX_TOKENS_TO_SAMPLE=500
TEMPERATURE=0.7
```

### AWS Setup

1. **Create Knowledge Base**:
   - Go to AWS Bedrock Console
   - Navigate to "Knowledge bases"
   - Create a new knowledge base
   - Upload your fitness/gym documents

2. **Request Model Access**:
   - Go to "Model access" in Bedrock Console
   - Request access to Claude models

3. **Get Knowledge Base ID**:
   - Copy the Knowledge Base ID from the console
   - Add it to your `.env` file

## API Endpoints

### POST /chat
Send a message and get an AI response with citations.

```json
{
  "message": "What are the benefits of strength training?"
}
```

### GET /history
Retrieve chat history (last 50 messages).

### DELETE /history
Clear all chat history.

## Multilingual Support

The chatbot automatically detects the language of your question and responds in the same language:

- **English**: "What are the benefits of strength training?"
- **Spanish**: "¿Cuáles son los beneficios del entrenamiento de fuerza?"

## Security

- ✅ No hardcoded credentials
- ✅ Environment variable configuration
- ✅ `.gitignore` excludes sensitive files
- ✅ Secure AWS credential management

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload

# Run tests
python -m pytest

# Check available models
python check_models.py
```

### Frontend Development

```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

## Troubleshooting

### Common Issues

1. **Model Access Denied**: Request access to Bedrock models in AWS Console
2. **Knowledge Base Not Found**: Verify your Knowledge Base ID is correct
3. **Environment Variables**: Ensure `.env` file exists and is properly formatted
4. **CORS Issues**: Check that frontend is running on `http://localhost:5173`

### Error Messages

- `AccessDeniedException`: Model access not granted
- `ValidationException`: Invalid model ID or API format
- `No module named 'dotenv'`: Install dependencies with `pip install -r requirements.txt`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review AWS Bedrock documentation
3. Open an issue on GitHub 