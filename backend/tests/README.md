# Testing Guide for Gym Chatbot

This directory contains comprehensive tests for the gym chatbot backend.

## Test Structure

```
tests/
├── __init__.py              # Makes tests a Python package
├── conftest.py              # Pytest configuration and fixtures
├── test_api.py              # API endpoint tests
├── test_language_detection.py # Language detection tests
├── test_database.py         # Database operation tests
└── README.md               # This file
```

## Test Categories

### 1. API Tests (`test_api.py`)
- **Chat Endpoints**: Test `/chat` endpoint functionality
- **Conversation Management**: Test CRUD operations for conversations
- **History Management**: Test chat history retrieval and clearing
- **Error Handling**: Test invalid requests and error responses
- **Health Check**: Test `/health` endpoint

### 2. Language Detection Tests (`test_language_detection.py`)
- **Spanish Detection**: Test Spanish language identification
- **English Detection**: Test English language identification
- **Mixed Language**: Test handling of mixed language content
- **Conversation Context**: Test language detection with conversation history
- **Instruction Generation**: Test AI instruction generation for both languages

### 3. Database Tests (`test_database.py`)
- **Database Initialization**: Test table creation and schema
- **Conversation Operations**: Test CRUD operations for conversations
- **Chat Message Operations**: Test saving and retrieving chat messages
- **Data Integrity**: Test foreign key relationships and constraints
- **Performance**: Test with large datasets and limits

## Running Tests

### Prerequisites
Install testing dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
# Using pytest directly
python -m pytest tests/ -v

# Using the test runner script
python run_tests.py
```

### Run Specific Test Categories
```bash
# Run only unit tests
python run_tests.py unit

# Run only integration tests
python run_tests.py integration

# Run a specific test file
python run_tests.py file test_api.py
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Fixtures

The `conftest.py` file provides several useful fixtures:

- **`test_db`**: Temporary database for testing
- **`mock_bedrock_client`**: Mocked AWS Bedrock client
- **`mock_knowledge_base`**: Mocked knowledge base responses
- **`client`**: FastAPI test client
- **`sample_conversation_data`**: Sample conversation data
- **`sample_chat_message`**: Sample chat message data

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure
```python
import pytest
from main import function_to_test

class TestFeatureName:
    """Test description"""
    
    def test_specific_functionality(self):
        """Test specific functionality"""
        # Arrange
        input_data = "test"
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == "expected"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality"""
        # Arrange
        input_data = "test"
        
        # Act
        result = await async_function_to_test(input_data)
        
        # Assert
        assert result == "expected"
```

### Test Markers
- `@pytest.mark.asyncio`: For async tests
- `@pytest.mark.unit`: For unit tests
- `@pytest.mark.integration`: For integration tests
- `@pytest.mark.slow`: For slow-running tests

## Coverage Reports

After running tests with coverage, you can find reports in:
- **HTML Report**: `htmlcov/index.html`
- **XML Report**: `coverage.xml`
- **Terminal Report**: Shows missing lines

## Continuous Integration

The test suite is designed to work with CI/CD pipelines:
- Fast execution for quick feedback
- Comprehensive coverage of critical paths
- Mocked external dependencies
- Isolated test database

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the backend directory
2. **Database Errors**: Tests use temporary databases, no cleanup needed
3. **Async Test Errors**: Use `@pytest.mark.asyncio` for async tests
4. **Mock Errors**: Ensure mocks are properly configured in fixtures

### Debug Mode
Run tests with verbose output:
```bash
python -m pytest tests/ -v -s
```

### Running Single Test
```bash
python -m pytest tests/test_api.py::TestChatEndpoints::test_chat_endpoint_success -v
``` 