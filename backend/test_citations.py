#!/usr/bin/env python3
"""
Test script to verify citation deduplication
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import format_source_uri

def test_citation_deduplication():
    """Test the citation deduplication logic"""
    print("🧪 Testing Citation Deduplication")
    print("=" * 40)
    
    # Test case 1: Duplicate URIs with same filename
    test_uris = [
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md",
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md",
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md"
    ]
    
    print(f"Test URIs: {test_uris}")
    
    # Simulate the deduplication logic
    unique_citations = {}
    for uri in test_uris:
        formatted_name = format_source_uri(uri)
        if formatted_name not in unique_citations:
            unique_citations[formatted_name] = uri
            print(f"✅ Added: {formatted_name}")
        else:
            print(f"❌ Skipped duplicate: {formatted_name}")
    
    # Format citations
    formatted_citations = []
    for i, (formatted_name, uri) in enumerate(unique_citations.items(), 1):
        formatted_citations.append(f"[{i}] - {formatted_name}")
    
    print(f"\nFinal citations: {formatted_citations}")
    
    # Test case 2: Different URIs with same formatted name
    test_uris_2 = [
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md",
        "s3://bucket/other/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md",
        "s3://bucket/backup/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md"
    ]
    
    print(f"\nTest URIs 2 (different paths, same filename): {test_uris_2}")
    
    unique_citations_2 = {}
    for uri in test_uris_2:
        formatted_name = format_source_uri(uri)
        if formatted_name not in unique_citations_2:
            unique_citations_2[formatted_name] = uri
            print(f"✅ Added: {formatted_name}")
        else:
            print(f"❌ Skipped duplicate: {formatted_name}")
    
    formatted_citations_2 = []
    for i, (formatted_name, uri) in enumerate(unique_citations_2.items(), 1):
        formatted_citations_2.append(f"[{i}] - {formatted_name}")
    
    print(f"\nFinal citations 2: {formatted_citations_2}")
    
    # Test case 3: Different files
    test_uris_3 = [
        "s3://bucket/documents/MTC - PROGRAM 3 - HYPERTROPHY (M)   W1-4_processed.md",
        "s3://bucket/documents/PT101TimLOCarticle08.pdf",
        "s3://bucket/documents/workout_plan.pptx"
    ]
    
    print(f"\nTest URIs 3 (different files): {test_uris_3}")
    
    unique_citations_3 = {}
    for uri in test_uris_3:
        formatted_name = format_source_uri(uri)
        if formatted_name not in unique_citations_3:
            unique_citations_3[formatted_name] = uri
            print(f"✅ Added: {formatted_name}")
        else:
            print(f"❌ Skipped duplicate: {formatted_name}")
    
    formatted_citations_3 = []
    for i, (formatted_name, uri) in enumerate(unique_citations_3.items(), 1):
        formatted_citations_3.append(f"[{i}] - {formatted_name}")
    
    print(f"\nFinal citations 3: {formatted_citations_3}")
    
    print("\n" + "=" * 40)
    print("✅ Citation deduplication test completed!")

if __name__ == "__main__":
    test_citation_deduplication() 