#!/usr/bin/env python3
"""
Example script demonstrating PPTX preprocessing for gym chatbot knowledge base.

This script shows how to use the preprocess_pptx.py module to process PowerPoint files
and prepare them for ingestion into the AWS Bedrock Knowledge Base.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocess_pptx import process_pptx_files, PPTXProcessor

def example_single_file_processing():
    """Example: Process a single PPTX file"""
    print("=== Example: Single File Processing ===")
    
    # Example file path (replace with your actual PPTX file)
    input_file = "example_presentation.pptx"
    output_dir = "processed_output"
    
    if not os.path.exists(input_file):
        print(f"❌ Example file {input_file} not found.")
        print("Please place a PPTX file in the backend directory or update the path.")
        return
    
    try:
        # Process the file
        output_files = process_pptx_files([input_file], output_dir, 'structured')
        
        print(f"✅ Successfully processed {input_file}")
        print("Output files:")
        for output_file in output_files:
            print(f"  - {output_file}")
            
    except Exception as e:
        print(f"❌ Error processing file: {e}")

def example_batch_processing():
    """Example: Process multiple PPTX files"""
    print("\n=== Example: Batch Processing ===")
    
    # Example directory with PPTX files
    input_dir = "pptx_files"
    output_dir = "batch_processed"
    
    if not os.path.exists(input_dir):
        print(f"❌ Input directory {input_dir} not found.")
        print("Create a directory with PPTX files or update the path.")
        return
    
    try:
        # Find all PPTX files in directory
        pptx_files = list(Path(input_dir).glob("*.pptx"))
        
        if not pptx_files:
            print(f"❌ No PPTX files found in {input_dir}")
            return
        
        print(f"Found {len(pptx_files)} PPTX files to process")
        
        # Process all files
        output_files = process_pptx_files([str(f) for f in pptx_files], output_dir, 'structured')
        
        print(f"✅ Successfully processed {len(output_files)} files")
        print("Output files:")
        for output_file in output_files:
            print(f"  - {output_file}")
            
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")

def example_custom_processing():
    """Example: Custom processing with PPTXProcessor class"""
    print("\n=== Example: Custom Processing ===")
    
    input_file = "example_presentation.pptx"
    
    if not os.path.exists(input_file):
        print(f"❌ Example file {input_file} not found.")
        return
    
    try:
        # Create processor instance
        processor = PPTXProcessor(output_format='structured')
        
        # Process the file
        processed_data = processor.process_pptx_file(input_file)
        
        # Access processed data
        metadata = processed_data['metadata']
        slides = processed_data['slides']
        summary = processed_data['summary']
        
        print(f"📊 Processing Summary:")
        print(f"  - File: {metadata['filename']}")
        print(f"  - Total Slides: {summary['total_slides']}")
        print(f"  - Total Tables: {summary['total_tables']}")
        print(f"  - Color-coded Cells: {summary['total_color_coded_cells']}")
        
        # Show color distribution
        if summary['color_distribution']:
            print(f"  - Color Distribution:")
            for color, count in summary['color_distribution'].items():
                print(f"    * {color}: {count} cells")
        
        # Generate markdown for knowledge base
        markdown_content = processor.format_for_knowledge_base(processed_data)
        
        # Save to file
        output_file = "custom_processed.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Custom processing completed. Output saved to {output_file}")
        
    except Exception as e:
        print(f"❌ Error in custom processing: {e}")

def main():
    """Run all examples"""
    print("🚀 PPTX Preprocessing Examples for Gym Chatbot")
    print("=" * 50)
    
    # Check if python-pptx is installed
    try:
        import pptx
        print("✅ python-pptx library is available")
    except ImportError:
        print("❌ python-pptx library not found.")
        print("Install it with: pip install python-pptx")
        return
    
    # Run examples
    example_single_file_processing()
    example_batch_processing()
    example_custom_processing()
    
    print("\n" + "=" * 50)
    print("📚 Next Steps:")
    print("1. Place your PPTX files in the backend directory")
    print("2. Run: python preprocess_pptx.py your_file.pptx -o processed/")
    print("3. Use the generated markdown files in your knowledge base")
    print("4. Upload to AWS Bedrock Knowledge Base using the ingestion script")

if __name__ == "__main__":
    main() 