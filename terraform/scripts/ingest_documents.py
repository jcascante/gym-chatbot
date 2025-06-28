#!/usr/bin/env python3
"""
Script to ingest documents into the Bedrock Knowledge Base
Run this after deploying the infrastructure with Terraform
"""

import boto3
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

def upload_to_s3(s3_client, bucket_name: str, file_path: str, s3_key: str) -> str | None:
    """Upload a file to S3 and return the S3 URI"""
    try:
        s3_client.upload_file(file_path, bucket_name, s3_key)
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        print(f"✅ Uploaded {file_path} to {s3_uri}")
        return s3_uri
    except Exception as e:
        print(f"❌ Failed to upload {file_path}: {e}")
        return None

def ingest_documents_to_knowledge_base(bedrock_client, knowledge_base_id: str, s3_uris: List[str]) -> bool:
    """Ingest documents from S3 URIs into the knowledge base"""
    try:
        response = bedrock_client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSource={
                'type': 'S3',
                'dataSourceConfiguration': {
                    's3Configuration': {
                        'bucketArn': f"arn:aws:s3:::{s3_uris[0].split('/')[2]}",
                        'inclusionPrefixes': ['documents/']
                    }
                }
            },
            ingestionJobName=f"gym-chatbot-ingestion-{int(time.time())}"
        )
        
        ingestion_job_id = response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {ingestion_job_id}")
        
        # Wait for ingestion to complete
        print("⏳ Waiting for ingestion to complete...")
        while True:
            status_response = bedrock_client.get_ingestion_job(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=response['ingestionJob']['dataSourceId'],
                ingestionJobId=ingestion_job_id
            )
            
            status = status_response['ingestionJob']['status']
            print(f"📊 Ingestion status: {status}")
            
            if status in ['COMPLETE', 'FAILED']:
                if status == 'COMPLETE':
                    print("✅ Document ingestion completed successfully!")
                    return True
                else:
                    print("❌ Document ingestion failed")
                    return False
            
            time.sleep(30)  # Wait 30 seconds before checking again
            
    except Exception as e:
        print(f"❌ Failed to start ingestion: {e}")
        return False

def main():
    # Configuration
    bucket_name = os.getenv('S3_BUCKET_NAME')
    knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    documents_dir = os.getenv('DOCUMENTS_DIR', '../data')
    
    if not bucket_name or not knowledge_base_id:
        print("❌ Please set S3_BUCKET_NAME and KNOWLEDGE_BASE_ID environment variables")
        print("You can get these values from the Terraform outputs")
        sys.exit(1)
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=aws_region)
    bedrock_client = boto3.client('bedrock-agent-runtime', region_name=aws_region)
    
    # Check if documents directory exists
    documents_path = Path(documents_dir)
    if not documents_path.exists():
        print(f"❌ Documents directory not found: {documents_path}")
        sys.exit(1)
    
    # Find all documents
    supported_extensions = ['.pdf', '.txt', '.doc', '.docx', '.md']
    documents = []
    
    for ext in supported_extensions:
        documents.extend(documents_path.glob(f"*{ext}"))
    
    if not documents:
        print(f"❌ No supported documents found in {documents_path}")
        print(f"Supported extensions: {', '.join(supported_extensions)}")
        sys.exit(1)
    
    print(f"📁 Found {len(documents)} documents to upload")
    
    # Upload documents to S3
    s3_uris = []
    for doc in documents:
        s3_key = f"documents/{doc.name}"
        s3_uri = upload_to_s3(s3_client, bucket_name, str(doc), s3_key)
        if s3_uri:
            s3_uris.append(s3_uri)
    
    if not s3_uris:
        print("❌ No documents were uploaded successfully")
        sys.exit(1)
    
    # Ingest documents into knowledge base
    print(f"\n📚 Ingesting {len(s3_uris)} documents into knowledge base...")
    success = ingest_documents_to_knowledge_base(bedrock_client, knowledge_base_id, s3_uris)
    
    if success:
        print("\n🎉 Document ingestion completed successfully!")
        print("Your gym chatbot is now ready to use with the ingested knowledge!")
    else:
        print("\n❌ Document ingestion failed. Please check the logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    import time
    main() 