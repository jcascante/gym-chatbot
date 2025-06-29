#!/usr/bin/env python3
"""
Test runner script for gym chatbot
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests with pytest"""
    print("🧪 Running Gym Chatbot Tests")
    print("=" * 50)
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest not found. Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Run tests
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode

def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"🧪 Running test: {test_file}")
    print("=" * 50)
    
    cmd = [sys.executable, "-m", "pytest", f"tests/{test_file}", "-v"]
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ Test {test_file} passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test {test_file} failed with exit code {e.returncode}")
        return e.returncode

def run_unit_tests():
    """Run only unit tests"""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "unit",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Unit tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Unit tests failed with exit code {e.returncode}")
        return e.returncode

def run_integration_tests():
    """Run only integration tests"""
    print("🧪 Running Integration Tests")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "integration",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Integration tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Integration tests failed with exit code {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unit":
            sys.exit(run_unit_tests())
        elif command == "integration":
            sys.exit(run_integration_tests())
        elif command == "file" and len(sys.argv) > 2:
            sys.exit(run_specific_test(sys.argv[2]))
        else:
            print("Usage:")
            print("  python run_tests.py              # Run all tests")
            print("  python run_tests.py unit         # Run unit tests only")
            print("  python run_tests.py integration  # Run integration tests only")
            print("  python run_tests.py file <file>  # Run specific test file")
            sys.exit(1)
    else:
        sys.exit(run_tests()) 