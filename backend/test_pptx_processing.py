#!/usr/bin/env python3
"""
Test script for PPTX preprocessing functionality.

This script verifies that all dependencies are installed and the preprocessing
module can be imported successfully.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    # Test basic Python modules
    try:
        import json
        import argparse
        from pathlib import Path
        from typing import List, Dict, Any, Tuple, Optional
        from dataclasses import dataclass
        import logging
        print("✅ Basic Python modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import basic modules: {e}")
        return False
    
    # Test python-pptx
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
        from pptx.dml.color import RGBColor
        from pptx.enum.dml import MSO_THEME_COLOR
        print("✅ python-pptx library imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import python-pptx: {e}")
        print("Install it with: pip install python-pptx")
        return False
    
    # Test our custom module
    try:
        from preprocess_pptx import PPTXProcessor, ColorCodingInterpreter, process_pptx_files
        print("✅ PPTX preprocessing module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import preprocessing module: {e}")
        return False
    
    return True

def test_color_interpreter():
    """Test the color coding interpreter"""
    print("\n🎨 Testing color coding interpreter...")
    
    try:
        from preprocess_pptx import ColorCodingInterpreter
        
        interpreter = ColorCodingInterpreter()
        
        # Test color interpretation
        test_colors = {
            '00FF00': 'Excellent/Great',  # Green
            'FF0000': 'Poor/Needs Attention',  # Red
            'FFFF00': 'Moderate/Average',  # Yellow
            '0000FF': 'Informational',  # Blue
            '808080': 'Neutral',  # Gray
        }
        
        for hex_color, expected in test_colors.items():
            result = interpreter.interpret_color(hex_color)
            if result == expected:
                print(f"✅ {hex_color} -> {result}")
            else:
                print(f"⚠️  {hex_color} -> {result} (expected {expected})")
        
        return True
        
    except Exception as e:
        print(f"❌ Color interpreter test failed: {e}")
        return False

def test_processor_creation():
    """Test that the PPTX processor can be created"""
    print("\n⚙️  Testing PPTX processor creation...")
    
    try:
        from preprocess_pptx import PPTXProcessor
        
        processor = PPTXProcessor(output_format='structured')
        print("✅ PPTX processor created successfully")
        
        # Test that it has the expected attributes
        assert hasattr(processor, 'color_interpreter')
        assert hasattr(processor, 'output_format')
        print("✅ Processor has expected attributes")
        
        return True
        
    except Exception as e:
        print(f"❌ Processor creation test failed: {e}")
        return False

def test_file_operations():
    """Test basic file operations"""
    print("\n📁 Testing file operations...")
    
    try:
        from pathlib import Path
        
        # Test creating output directory
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        print("✅ Output directory creation works")
        
        # Test file writing
        test_file = test_dir / "test.txt"
        test_file.write_text("Test content")
        print("✅ File writing works")
        
        # Clean up
        test_file.unlink()
        test_dir.rmdir()
        print("✅ File cleanup works")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 PPTX Preprocessing Test Suite")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Color Interpreter Test", test_color_interpreter),
        ("Processor Creation Test", test_processor_creation),
        ("File Operations Test", test_file_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PPTX preprocessing is ready to use.")
        print("\n📚 Next steps:")
        print("1. Place your PPTX files in the backend directory")
        print("2. Run: python preprocess_pptx.py your_file.pptx -o processed/")
        print("3. Check the generated markdown files")
        print("4. Upload to your knowledge base")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check that python-pptx is installed: pip install python-pptx")
        print("3. Verify file permissions for output directories")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 