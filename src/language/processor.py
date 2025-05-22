"""
Language processor for Jarvis AI Assistant.
Handles language detection, intent recognition, and response generation.
"""

import logging
import re
from typing import Dict, List, Tuple, Any, Optional

# In a real implementation, you would use libraries like:
# - langdetect or fastText for language detection
# - spaCy or Transformers for NLP
# - A custom NLU system or Rasa for intent extraction

class LanguageProcessor:
    """Processes natural language for the Jarvis AI Assistant.
    
    This class handles:
    1. Language detection (English/Dutch)
    2. Intent and entity extraction
    3. Response generation
    4. Persona application
    """
    
    def __init__(self):
        """Initialize the language processor."""
        self.logger = logging.getLogger("jarvis.language")
        
        # Common English and Dutch words for basic language detection
        self.language_markers = {
            "en": ["the", "and", "is", "in", "to", "I", "you", "for", "what", "how", "can", "this"],
            "nl": ["de", "het", "een", "in", "van", "is", "op", "te", "en", "dat", "ik", "je", "wat", "hoe", "kan", "dit"]
        }
        
        # Basic intents and their pattern matchers
        self.intent_patterns = {
            "en": {
                "greeting": [r"(?i)hello", r"(?i)hi\b", r"(?i)hey\b", r"(?i)good (morning|afternoon|evening)", r"(?i)greetings"],
                "farewell": [r"(?i)goodbye", r"(?i)bye", r"(?i)see you", r"(?i)later", r"(?i)exit", r"(?i)quit"],
                "question": [r"(?i)what", r"(?i)how", r"(?i)why", r"(?i)when", r"(?i)where", r"(?i)who", r"(?i)\?"],
                "command": [r"(?i)please", r"(?i)can you", r"(?i)would you", r"(?i)need to", r"(?i)want to"]
            },
            "nl": {
                "greeting": [r"(?i)hallo", r"(?i)hoi", r"(?i)hey", r"(?i)goedemorgen", r"(?i)goedemiddag", r"(?i)goedenavond"],
                "farewell": [r"(?i)tot ziens", r"(?i)doei", r"(?i)dag", r"(?i)tot later", r"(?i)exit", r"(?i)afsluiten"],
                "question": [r"(?i)wat", r"(?i)hoe", r"(?i)waarom", r"(?i)wanneer", r"(?i)waar", r"(?i)wie", r"(?i)\?"],
                "command": [r"(?i)alsjeblieft", r"(?i)kun je", r"(?i)zou je", r"(?i)moet", r"(?i)wil"]
            }
        }
        
        # Templates for response generation
        self.response_templates = {
            "en": {
                "greeting": [
                    "Hello! How can I assist you today?",
                    "Greetings! What can I do for you?",
                    "Hi there! How may I help you?"
                ],
                "farewell": [
                    "Goodbye! Feel free to call on me whenever you need assistance.",
                    "Until next time. I'll be here when you need me.",
                    "See you later. It was a pleasure assisting you."
                ],
                "acknowledgment": [
                    "I understand. Let me handle that for you.",
                    "Got it. I'm working on that now.",
                    "I see what you need. One moment."
                ],
                "clarification": [
                    "Could you provide more details about that?",
                    "I'm not quite sure I understand. Could you elaborate?",
                    "I'd like to help better. Can you clarify what you're looking for?"
                ]
            },
            "nl": {
                "greeting": [
                    "Hallo! Hoe kan ik u vandaag helpen?",
                    "Groeten! Wat kan ik voor u doen?",
                    "Hoi! Waarmee kan ik u van dienst zijn?"
                ],
                "farewell": [
                    "Tot ziens! Roep me gerust wanneer u hulp nodig heeft.",
                    "Tot de volgende keer. Ik ben er als u me nodig heeft.",
                    "Tot later. Het was een genoegen u te helpen."
                ],
                "acknowledgment": [
                    "Ik begrijp het. Laat mij dat voor u regelen.",
                    "Begrepen. Ik werk er nu aan.",
                    "Ik zie wat u nodig heeft. Een moment."
                ],
                "clarification": [
                    "Kunt u meer details geven?",
                    "Ik ben niet zeker of ik het begrijp. Kunt u dat toelichten?",
                    "Ik wil u graag beter helpen. Kunt u verduidelijken wat u zoekt?"
                ]
            }
        }
        
        # Persona traits to apply to responses
        self.persona_traits = {
            "en": {
                "friendly": [
                    "I'm happy to ", 
                    "I'd be delighted to ",
                    "It would be my pleasure to "
                ],
                "witty": [
                    "Just doing what I do best: ",
                    "Another day, another digital challenge: ",
                    "No quantum computing required for this one: "
                ],
                "helpful": [
                    "To help you with this, I'll ",
                    "The best approach would be to ",
                    "Let me assist you by "
                ]
            },
            "nl": {
                "friendly": [
                    "Ik help u graag met ",
                    "Met veel plezier zal ik ",
                    "Het is mij een genoegen om "
                ],
                "witty": [
                    "Gewoon doen waar ik goed in ben: ",
                    "Weer een dag, weer een digitale uitdaging: ",
                    "Hiervoor is geen kwantumcomputer nodig: "
                ],
                "helpful": [
                    "Om u hiermee te helpen, zal ik ",
                    "De beste aanpak zou zijn om ",
                    "Laat mij u helpen door "
                ]
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect whether the input is in English or Dutch.
        
        Args:
            text: The text to analyze.
            
        Returns:
            Language code: 'en' for English, 'nl' for Dutch.
        """
        # If text is empty or very short, default to English
        if not text or len(text) < 3:
            return "en"
            
        try:
            # Try to use langdetect library if available
            from langdetect import detect, LangDetectException
            
            try:
                lang_code = detect(text)
                # langdetect returns 'nl' for Dutch and 'en' for English
                if lang_code == "nl":
                    return "nl"
                # For any other language, fall back to English as default
                return "en"
            except LangDetectException:
                # Fall back to the basic method if langdetect fails
                self.logger.warning("Language detection failed, falling back to basic method")
        except ImportError:
            # If langdetect is not available, fall back to the basic method
            self.logger.warning("langdetect library not available, using basic language detection")
        
        # Basic language detection as a fallback
        text_lower = text.lower()
        en_count = 0
        nl_count = 0
        
        # Count language markers
        for word in self.language_markers["en"]:
            if re.search(r"\b" + word.lower() + r"\b", text_lower):
                en_count += 1
                
        for word in self.language_markers["nl"]:
            if re.search(r"\b" + word.lower() + r"\b", text_lower):
                nl_count += 1
        
        # If there's a clear winner, use that language
        if nl_count > en_count:
            return "nl"
        
        # Default to English
        return "en"
    
    def extract_intent_and_entities(self, text: str, language: str) -> Tuple[str, Dict[str, Any]]:
        """Extract the user's intent and entities from the input.
        
        Args:
            text: The text to analyze.
            language: The detected language code.
            
        Returns:
            A tuple of (intent, entities_dict).
        """
        # In a real implementation, use a proper NLU system
        # This is a simplified version
        
        # Try to match intents based on patterns
        for intent, patterns in self.intent_patterns[language].items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return intent, self._extract_entities(text, intent, language)
        
        # Default to general inquiry if no specific intent is matched
        return "general_inquiry", self._extract_entities(text, "general_inquiry", language)
    
    def _extract_entities(self, text: str, intent: str, language: str) -> Dict[str, Any]:
        """Extract entities based on the identified intent.
        
        Args:
            text: The text to analyze.
            intent: The identified intent.
            language: The detected language code.
            
        Returns:
            A dictionary of extracted entities.
        """
        entities = {}
        
        # In a real implementation, this would use more sophisticated NLP
        # Here's a simplified approach
        
        # Extract time-related entities
        time_patterns = {
            "en": r"(?i)at (\d{1,2}(?::\d{2})?(?: ?[ap]m)?)",
            "nl": r"(?i)om (\d{1,2}(?::\d{2})?(?: ?uur)?)"
        }
        
        time_match = re.search(time_patterns[language], text)
        if time_match:
            entities["time"] = time_match.group(1)
        
        # Extract date-related entities
        date_patterns = {
            "en": r"(?i)on ([a-z]+day|tomorrow|yesterday|\d{1,2}(?:st|nd|rd|th)? (?:of )?[a-z]+)",
            "nl": r"(?i)op ([a-z]+dag|morgen|gisteren|\d{1,2} [a-z]+)"
        }
        
        date_match = re.search(date_patterns[language], text)
        if date_match:
            entities["date"] = date_match.group(1)
        
        return entities
    
    def generate_response(self, intent: str, entities: Dict[str, Any], 
                         knowledge_info: Optional[Dict[str, Any]], 
                         context: List[Dict[str, Any]], 
                         language: str) -> str:
        """Generate a response based on intent, entities, and available knowledge.
        
        Args:
            intent: The identified intent.
            entities: The extracted entities.
            knowledge_info: Knowledge retrieved for this query.
            context: Conversation context from memory.
            language: The detected language code.
            
        Returns:
            A generated response string.
        """
        # In a real implementation, this would use more sophisticated NLG
        
        # Handle simple intents with templates
        if intent in self.response_templates[language]:
            # Pick a template (in a real system, this would be more sophisticated)
            import random
            template = random.choice(self.response_templates[language][intent])
            return template
        
        # For knowledge-based responses
        if knowledge_info:
            # Construct a response using the retrieved knowledge
            if language == "en":
                response = f"Based on what I know, {knowledge_info.get('content', 'I can provide the following information')}."
                if knowledge_info.get('sources'):
                    response += f" This information comes from {', '.join(knowledge_info['sources'])}."
            else:  # Dutch
                response = f"Gebaseerd op wat ik weet, {knowledge_info.get('content', 'kan ik de volgende informatie geven')}."
                if knowledge_info.get('sources'):
                    response += f" Deze informatie komt van {', '.join(knowledge_info['sources'])}."
            
            return response
        
        # Default responses when no specific template or knowledge is available
        if language == "en":
            return "I understand your query. Let me assist you with that."
        else:  # Dutch
            return "Ik begrijp uw vraag. Laat mij u daarmee helpen."
    
    def apply_persona(self, content: str, language: str) -> str:
        """Apply the Jarvis persona to the response content.
        
        Args:
            content: The raw response content.
            language: The language code (en/nl).
            
        Returns:
            Response with appropriate persona elements applied.
        """
        # In a real implementation, this would be more sophisticated
        
        # Randomly decide whether to add a persona trait
        import random
        if random.random() < 0.3:  # 30% chance to add a persona trait
            trait = random.choice(list(self.persona_traits[language].keys()))
            prefix = random.choice(self.persona_traits[language][trait])
            
            # For greeting and farewell intents, just return the content
            if any(marker in content.lower() for marker in ["hello", "hi", "hey", "goodbye", "bye", 
                                                          "hallo", "hoi", "doei", "tot ziens"]):
                return content
            
            # For other responses, prepend the persona trait
            if content[0].islower():
                return prefix + content
            else:
                # Make sure we don't mess up capitalization
                first_word_end = content.find(" ")
                if first_word_end == -1:  # Single word
                    return prefix + content.lower()
                else:
                    return prefix + content[0].lower() + content[1:]
        
        return content