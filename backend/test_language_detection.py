#!/usr/bin/env python3
"""
Test script to debug language detection
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import detect_language, get_conversation_language

def test_language_detection():
    """Test language detection with various Spanish inputs"""
    print("🧪 Testing Language Detection")
    print("=" * 40)
    
    # Test Spanish questions
    spanish_questions = [
        "¿Cuál es la rutina de entrenamiento?",
        "Necesito información sobre ejercicios de fuerza",
        "¿Cómo hago deadlift correctamente?",
        "Quiero saber sobre series y repeticiones",
        "¿Qué ejercicios son buenos para hipertrofia?",
        "Rutina de entrenamiento para principiantes",
        "Ejercicios de pecho y espalda",
        "¿Cuántas series debo hacer?",
        "Entrenamiento de fuerza y acondicionamiento",
        "Programa de ejercicios para gimnasio"
    ]
    
    print("Testing Spanish questions:")
    for i, question in enumerate(spanish_questions, 1):
        detected = detect_language(question)
        print(f"{i}. '{question}' -> {detected}")
    
    print("\n" + "=" * 40)
    
    # Test English questions
    english_questions = [
        "What is the training routine?",
        "I need information about strength exercises",
        "How do I do deadlift correctly?",
        "I want to know about sets and repetitions",
        "What exercises are good for hypertrophy?",
        "Training routine for beginners",
        "Chest and back exercises",
        "How many sets should I do?",
        "Strength and conditioning training",
        "Gym exercise program"
    ]
    
    print("Testing English questions:")
    for i, question in enumerate(english_questions, 1):
        detected = detect_language(question)
        print(f"{i}. '{question}' -> {detected}")
    
    print("\n" + "=" * 40)
    
    # Test conversation language detection
    print("Testing conversation language detection:")
    
    # Spanish conversation
    spanish_history = [
        {"user_message": "¿Cuál es la rutina?", "bot_response": "La rutina incluye..."},
        {"user_message": "¿Cuántas series?", "bot_response": "Debes hacer 3 series..."}
    ]
    
    current_spanish = "¿Cómo hago este ejercicio?"
    result = get_conversation_language(current_spanish, spanish_history)
    print(f"Spanish conversation + Spanish question -> {result}")
    
    # English conversation
    english_history = [
        {"user_message": "What is the routine?", "bot_response": "The routine includes..."},
        {"user_message": "How many sets?", "bot_response": "You should do 3 sets..."}
    ]
    
    current_english = "How do I do this exercise?"
    result = get_conversation_language(current_english, english_history)
    print(f"English conversation + English question -> {result}")

if __name__ == "__main__":
    test_language_detection() 