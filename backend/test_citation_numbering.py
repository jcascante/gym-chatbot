#!/usr/bin/env python3
"""
Test script to verify citation numbering consistency
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import format_source_uri

def test_citation_numbering_consistency():
    """Test that citation numbering is consistent between context and response"""
    print("🧪 Testing Citation Numbering Consistency")
    print("=" * 50)
    
    # Simulate the source URIs that might come from knowledge base
    source_uris = [
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md",
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md",  # Duplicate
        "s3://bucket/documents/PT101TimLOCarticle08.pdf",
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md"   # Another duplicate
    ]
    
    print(f"Original source URIs: {source_uris}")
    print()
    
    # Simulate the context building logic
    print("📝 Building Context:")
    print("-" * 30)
    
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
    
    print(f"Unique citations mapping: {unique_citations}")
    print(f"URI to citation number mapping: {uri_to_citation_number}")
    print()
    
    # Simulate building context with document numbers
    print("📄 Context Document Numbers:")
    for uri in unique_citations.values():
        citation_number = uri_to_citation_number.get(uri, 1)
        formatted_name = format_source_uri(uri)
        print(f"[{citation_number}]: {formatted_name}")
    
    print()
    
    # Simulate building source document list
    print("📚 Source Documents List:")
    for uri in unique_citations.values():
        citation_number = uri_to_citation_number.get(uri, 1)
        formatted_name = format_source_uri(uri)
        print(f"[{citation_number}]: {formatted_name}")
    
    print()
    
    # Simulate building final citations for response
    print("🏷️ Final Citations for Response:")
    formatted_citations = []
    for i, (formatted_name, uri) in enumerate(unique_citations.items(), 1):
        citation = f"[{i}] - {formatted_name}"
        formatted_citations.append(citation)
        print(citation)
    
    print()
    print("✅ Citation numbering consistency test completed!")
    print("The numbers in context should match the numbers in citations.")

if __name__ == "__main__":
    test_citation_numbering_consistency() 