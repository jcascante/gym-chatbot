"""
Tests for language detection functionality
"""

import pytest
from main import detect_language, get_conversation_language, get_language_instruction

class TestLanguageDetection:
    """Test language detection functions"""
    
    def test_detect_language_spanish(self):
        """Test Spanish language detection"""
        spanish_texts = [
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
        
        for text in spanish_texts:
            result = detect_language(text)
            assert result == 'es', f"Failed to detect Spanish in: {text}"
    
    def test_detect_language_english(self):
        """Test English language detection"""
        english_texts = [
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
        
        for text in english_texts:
            result = detect_language(text)
            assert result == 'en', f"Failed to detect English in: {text}"
    
    def test_detect_language_mixed(self):
        """Test mixed language detection"""
        # Test with Spanish words in English context
        mixed_text = "I want to do ejercicios de fuerza"
        result = detect_language(mixed_text)
        # Should default to English for mixed content
        assert result in ['en', 'es']
    
    def test_detect_language_empty(self):
        """Test empty string handling"""
        result = detect_language("")
        assert result == 'en'  # Default to English
    
    def test_detect_language_numbers(self):
        """Test text with numbers"""
        result = detect_language("3 sets of 10 reps")
        assert result == 'en'
        
        result = detect_language("3 series de 10 repeticiones")
        assert result == 'es'

class TestConversationLanguageDetection:
    """Test conversation language detection"""
    
    def test_conversation_language_spanish(self):
        """Test Spanish conversation detection"""
        spanish_history = [
            {"user_message": "¿Cuál es la rutina?", "bot_response": "La rutina incluye..."},
            {"user_message": "¿Cuántas series?", "bot_response": "Debes hacer 3 series..."}
        ]
        
        current_message = "¿Cómo hago este ejercicio?"
        result = get_conversation_language(current_message, spanish_history)
        assert result == 'es'
    
    def test_conversation_language_english(self):
        """Test English conversation detection"""
        english_history = [
            {"user_message": "What is the routine?", "bot_response": "The routine includes..."},
            {"user_message": "How many sets?", "bot_response": "You should do 3 sets..."}
        ]
        
        current_message = "How do I do this exercise?"
        result = get_conversation_language(current_message, english_history)
        assert result == 'en'
    
    def test_conversation_language_empty_history(self):
        """Test with empty conversation history"""
        result = get_conversation_language("Test message", [])
        assert result in ['en', 'es']  # Should detect based on current message only
    
    def test_conversation_language_mixed_history(self):
        """Test with mixed language history"""
        mixed_history = [
            {"user_message": "What is the routine?", "bot_response": "The routine includes..."},
            {"user_message": "¿Cuántas series?", "bot_response": "Debes hacer 3 series..."}
        ]
        
        # Should prioritize current message
        result = get_conversation_language("¿Cómo hago este ejercicio?", mixed_history)
        assert result == 'es'
        
        result = get_conversation_language("How do I do this exercise?", mixed_history)
        assert result == 'en'

class TestLanguageInstructions:
    """Test language instruction generation"""
    
    def test_spanish_instructions(self):
        """Test Spanish language instructions"""
        instructions = get_language_instruction('es')
        assert 'español' in instructions.lower()
        assert 'estructura de documentos' in instructions.lower()
        assert 'programación' in instructions.lower()
    
    def test_english_instructions(self):
        """Test English language instructions"""
        instructions = get_language_instruction('en')
        assert 'english' in instructions.lower()
        assert 'document structure' in instructions.lower()
        assert 'programming' in instructions.lower()
    
    def test_instructions_include_document_structure(self):
        """Test that instructions include document structure info"""
        spanish_instructions = get_language_instruction('es')
        english_instructions = get_language_instruction('en')
        
        # Check for document structure information
        assert 'primera parte' in spanish_instructions.lower()
        assert 'first part' in english_instructions.lower()
        assert 'guía de volumen' in spanish_instructions.lower()
        assert 'volume guide' in english_instructions.lower()
    
    def test_instructions_include_color_code_info(self):
        """Test that instructions include color code information"""
        spanish_instructions = get_language_instruction('es')
        english_instructions = get_language_instruction('en')
        
        # Check for color code information
        assert 'código de colores' in spanish_instructions.lower()
        assert 'color code' in english_instructions.lower() 