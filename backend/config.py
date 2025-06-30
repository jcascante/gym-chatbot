import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS Configuration - Use environment variables for security
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Bedrock Configuration
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID')

# Knowledge Base Configuration
# Replace this with your actual Knowledge Base ID from AWS Bedrock
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')

# Retrieval Configuration
MAX_RETRIEVAL_RESULTS = int(os.getenv('MAX_RETRIEVAL_RESULTS', '3'))
MAX_TOKENS_TO_SAMPLE = int(os.getenv('MAX_TOKENS_TO_SAMPLE', '500'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))

# Database Configuration
DB_PATH = os.getenv('DB_PATH', 'chat_history.db')

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256') 