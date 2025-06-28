#!/usr/bin/env python3
"""
Utility script to list AWS Bedrock Knowledge Bases and help find the correct Knowledge Base ID.
"""

import boto3
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

def list_knowledge_bases():
    """List all available knowledge bases in the AWS account."""
    try:
        # Create Bedrock agent client
        bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # List knowledge bases
        response = bedrock_agent.list_knowledge_bases()
        
        print("Available Knowledge Bases:")
        print("=" * 50)
        
        if not response.get('knowledgeBaseSummaries'):
            print("No knowledge bases found in your AWS account.")
            print("\nTo create a knowledge base:")
            print("1. Go to AWS Bedrock console")
            print("2. Navigate to 'Knowledge bases'")
            print("3. Click 'Create knowledge base'")
            print("4. Follow the setup wizard")
            return
        
        for kb in response['knowledgeBaseSummaries']:
            print(f"Name: {kb.get('name', 'N/A')}")
            print(f"ID: {kb.get('knowledgeBaseId', 'N/A')}")
            print(f"Status: {kb.get('status', 'N/A')}")
            print(f"Description: {kb.get('description', 'N/A')}")
            print("-" * 30)
        
        print("\nTo use a knowledge base, copy the ID and update config.py:")
        print("KNOWLEDGE_BASE_ID = 'your-knowledge-base-id'")
        
    except Exception as e:
        print(f"Error listing knowledge bases: {e}")
        print("\nMake sure:")
        print("1. Your AWS credentials are correct")
        print("2. You have Bedrock permissions")
        print("3. You're in the correct AWS region")

if __name__ == "__main__":
    list_knowledge_bases() 