import spacy
from typing import Optional

class LanguageDetector:
    def __init__(self):
        # Load the language models for English and Dutch
        try:
            self.nlp_en = spacy.load("en_core_web_sm")
        except OSError:
            spacy.cli.download("en_core_web_sm")
            self.nlp_en = spacy.load("en_core_web_sm")
            
        try:
            self.nlp_nl = spacy.load("nl_core_news_sm")
        except OSError:
            spacy.cli.download("nl_core_news_sm")
            self.nlp_nl = spacy.load("nl_core_news_sm")

    def detect(self, text: str) -> str:
        """
        Detect whether the input text is in English or Dutch.
        Returns 'en' for English or 'nl' for Dutch.
        """
        # Basic dictionary of common Dutch words that differ from English
        dutch_indicators = {
            "ik", "je", "hij", "zij", "wij", "jullie", "deze", "dit", "dat",
            "wat", "waarom", "hoe", "wanneer", "waar", "wie", "welk", "welke",
            "en", "of", "maar", "want", "dus", "echter", "omdat", "aangezien",
            "de", "het", "een", "niet", "geen", "wel", "ook", "zeer", "veel"
        }

        # Convert text to lowercase for comparison
        text_lower = text.lower()
        words = set(text_lower.split())

        # Count Dutch indicator words
        dutch_count = len(words.intersection(dutch_indicators))

        # Process with both models
        doc_en = self.nlp_en(text)
        doc_nl = self.nlp_nl(text)

        # Calculate confidence scores based on token recognition
        en_score = sum(1 for token in doc_en if not token.is_oov) / len(doc_en)
        nl_score = sum(1 for token in doc_nl if not token.is_oov) / len(doc_nl)

        # Adjust scores based on Dutch indicators
        if dutch_count > 0:
            nl_score += 0.2

        return "nl" if nl_score > en_score else "en"

    def get_language_name(self, language_code: str) -> str:
        """Convert language code to full name"""
        language_map = {
            "en": "English",
            "nl": "Dutch"
        }
        return language_map.get(language_code, "Unknown")