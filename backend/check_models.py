#!/usr/bin/env python3
"""
Utility script to list available AWS Bedrock models and help find the correct model ID.
"""

import boto3
import json
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

def list_available_models():
    """List all available models in the AWS Bedrock account."""
    try:
        # Create Bedrock client
        bedrock = boto3.client(
            'bedrock',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # List foundation models
        response = bedrock.list_foundation_models()
        
        print("Available Foundation Models:")
        print("=" * 50)
        
        if not response.get('modelSummaries'):
            print("No foundation models found in your AWS account.")
            print("\nTo access models:")
            print("1. Go to AWS Bedrock console")
            print("2. Navigate to 'Model access'")
            print("3. Request access to the models you need")
            return
        
        # Group models by provider
        models_by_provider = {}
        for model in response['modelSummaries']:
            provider = model.get('providerName', 'Unknown')
            if provider not in models_by_provider:
                models_by_provider[provider] = []
            models_by_provider[provider].append(model)
        
        for provider, models in models_by_provider.items():
            print(f"\n{provider.upper()} Models:")
            print("-" * 30)
            for model in models:
                model_id = model.get('modelId', 'N/A')
                model_name = model.get('modelName', 'N/A')
                status = model.get('modelLifecycle', {}).get('status', 'N/A')
                print(f"ID: {model_id}")
                print(f"Name: {model_name}")
                print(f"Status: {status}")
                print()
        
        print("\nRecommended models for chat:")
        print("- anthropic.claude-3-sonnet-20240229-v1:0")
        print("- anthropic.claude-3-haiku-20240307-v1:0")
        print("- anthropic.claude-instant-v1")
        print("- amazon.titan-text-express-v1")
        
    except Exception as e:
        print(f"Error listing models: {e}")
        print("\nMake sure:")
        print("1. Your AWS credentials are correct")
        print("2. You have Bedrock permissions")
        print("3. You're in the correct AWS region")
        print("4. You have requested model access in the Bedrock console")

def test_model_access(model_id):
    """Test if a specific model is accessible."""
    try:
        bedrock = boto3.client(
            'bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Try a simple test call
        if 'claude-3' in model_id:
            # Claude 3 models use Messages API
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ]
            })
        elif 'anthropic' in model_id:
            # Older Claude models
            test_prompt = "Human: Hello\nAssistant:"
            body = json.dumps({
                "prompt": test_prompt,
                "max_tokens_to_sample": 10,
                "temperature": 0.7
            })
        elif 'amazon' in model_id:
            # Amazon models (Titan)
            body = json.dumps({
                "inputText": "Hello",
                "textGenerationConfig": {
                    "maxTokenCount": 10,
                    "temperature": 0.7
                }
            })
        else:
            print(f"Unknown model type: {model_id}")
            return False
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=body
        )
        
        print(f"✅ Model {model_id} is accessible!")
        return True
        
    except Exception as e:
        print(f"❌ Model {model_id} is not accessible: {e}")
        return False

if __name__ == "__main__":
    print("Checking available Bedrock models...")
    list_available_models()
    
    print("\n" + "="*50)
    print("Testing model access...")
    
    # Test common models
    models_to_test = [
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-haiku-20240307-v1:0',
        'anthropic.claude-instant-v1',
        'amazon.titan-text-express-v1'
    ]
    
    for model_id in models_to_test:
        test_model_access(model_id)
        print() 