#!/usr/bin/env python3
import os
import time
import hashlib
MILVUS_HOST=os.getenv("MILVUS_HOST","milvus-standalone")
MILVUS_PORT=os.getenv("MILVUS_PORT","19530")
OLLAMA_URL=os.getenv("OLLAMA_URL","http://ollama:11434")
SPACY_MODEL=os.getenv("SPACY_MODEL","en_core_web_lg")
try:
    import spacy
except ImportError:  # pragma: no cover - optional dependency
    spacy = None

try:
    import PyPDF2
except ImportError:  # pragma: no cover - optional dependency
    PyPDF2 = None

try:
    import pytextract
except ImportError:  # pragma: no cover - optional dependency
    pytextract = None

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover - optional dependency
    GraphDatabase = None
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:  # pragma: no cover - optional dependency
    Observer = None
    FileSystemEventHandler = object
import logging
from datetime import datetime
import sys
import io
import re
import json
import traceback
import uuid
try:
    from pymilvus import Collection, utility
except ImportError:  # pragma: no cover - optional dependency
    Collection = None
    utility = None

# Ensure repository root is in import path
repo_root = os.path.dirname(os.path.abspath(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from hybrid_search import HybridSearch

# Determine repository root for logs
repo_root = os.path.dirname(os.path.abspath(__file__))
# Log directory can be overridden via env var, default to repo/logs
log_dir = os.environ.get("JARVIS_LOG_DIR", os.path.join(repo_root, "logs"))
os.makedirs(log_dir, exist_ok=True)

# Configure logging with fallback if file handler fails
log_file = os.path.join(log_dir, "document_processor.log")
handlers = []
try:
    fh = logging.FileHandler(log_file)
    handlers.append(fh)
except Exception as e:
    print(f"Warning: could not open log file {log_file}: {e}", file=sys.stderr)
handlers.append(logging.StreamHandler())
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger("DocumentProcessor")

# Load NLP model with optional GPU support
if spacy is not None:
    try:
        # Prefer running on GPU if available
        spacy.prefer_gpu()
        nlp = spacy.load(SPACY_MODEL)
        logger.info("Loaded spaCy NLP model successfully")
    except Exception as e:
        logger.error(f"Error loading spaCy model: {str(e)}")
        # Fallback to a minimal model if available
        try:
            nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded fallback spaCy model")
        except Exception:
            logger.warning("spaCy models unavailable, using blank English model")
            nlp = spacy.blank("en")
else:
    logger.warning("spaCy library not installed; text processing features disabled")
    nlp = None

class DocumentProcessor:
    def __init__(self):
        # Configuration
        self.neo4j_uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
        self.neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
        self.neo4j_password = os.environ.get("NEO4J_PASSWORD", "VerySecurePassword")
        self.milvus_host = MILVUS_HOST
        self.milvus_port = MILVUS_PORT
        self.ollama_url = OLLAMA_URL
        self.uploads_dir = os.environ.get("UPLOADS_DIR", "/app/backend/data/uploads")
        self.processed_dir = os.environ.get("PROCESSED_DIR", "/processed")
        self.config_dir = os.environ.get("CONFIG_DIR", "/app/config")
        self.chunk_size = int(os.environ.get("DOCUMENT_CHUNK_SIZE", "1536"))
        self.chunk_overlap = int(os.environ.get("DOCUMENT_CHUNK_OVERLAP", "256"))
        self.processing_batch_size = int(os.environ.get("PROCESSING_BATCH_SIZE", "16"))
        
        # Create necessary directories
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Connect to Neo4j if available
        if GraphDatabase is not None:
            try:
                self.driver = GraphDatabase.driver(
                    self.neo4j_uri,
                    auth=(self.neo4j_user, self.neo4j_password)
                )
                logger.info(f"Connected to Neo4j at {self.neo4j_uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {str(e)}")
                self.driver = None
        else:
            logger.warning("neo4j library not installed; graph features disabled")
            self.driver = None
            
        # Initialize hybrid search module for vector DB operations
        try:
            self.searcher = HybridSearch(
                neo4j_uri=self.neo4j_uri,
                neo4j_user=self.neo4j_user,
                neo4j_password=self.neo4j_password,
                milvus_host=self.milvus_host,
                milvus_port=self.milvus_port,
                ollama_url=self.ollama_url
            )
            logger.info("Initialized HybridSearch module")
        except Exception as e:
            logger.error(f"Failed to initialize HybridSearch: {str(e)}")
            logger.error(traceback.format_exc())
            self.searcher = None
            
        # Get or create dynamic default KB ID
        self.default_kb_id = self.get_or_create_default_kb()
        logger.info(f"Using dynamic default knowledge base ID: {self.default_kb_id}")
    
    def get_or_create_default_kb(self):
        """Dynamically get or create a default knowledge base ID"""
        # Path to persistent config file
        config_path = os.path.join(self.config_dir, "kb_default_config.json")
        
        try:
            # Step 1: Try to read from persistent config file
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'default_kb_id' in config and config['default_kb_id']:
                        logger.info(f"Using default KB ID from config file: {config['default_kb_id']}")
                        return config['default_kb_id']
            
            # Step 2: If no config file, try to find KBs from Neo4j
            if self.driver:
                with self.driver.session() as session:
                    # Try to find any existing KB ID
                    result = session.run("""
                        MATCH (d:Document) 
                        WHERE d.kb_id IS NOT NULL 
                        RETURN DISTINCT d.kb_id AS kb_id 
                        LIMIT 1
                    """)
                    
                    record = result.single()
                    if record and record["kb_id"]:
                        kb_id = record["kb_id"]
                        logger.info(f"Found existing KB ID in Neo4j: {kb_id}")
                        
                        # Save this ID to config for next time
                        os.makedirs(os.path.dirname(config_path), exist_ok=True)
                        with open(config_path, 'w') as f:
                            json.dump({'default_kb_id': kb_id}, f)
                        
                        return kb_id
            
            # Step 3: If still no KB found, create a new UUID
            new_kb_id = str(uuid.uuid4())
            logger.info(f"No existing knowledge bases found, creating new default: {new_kb_id}")
            
            # Save this new ID to config file for next time
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump({'default_kb_id': new_kb_id}, f)
            
            return new_kb_id
            
        except Exception as e:
            logger.error(f"Error managing default KB ID: {str(e)}")
            logger.error(traceback.format_exc())
            # Last resort fallback
            return str(uuid.uuid4())
    
    def extract_text_from_pdf(self, file_path):
        """Extract text content from a PDF file"""
        text = ""
        if PyPDF2 is None:
            logger.warning("PyPDF2 not available, skipping PDF extraction")
            return text
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def extract_text_from_document(self, file_path):
        """Extract text from various document formats"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.java', '.c', '.cpp']:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except UnicodeDecodeError:
                # Try with a different encoding if utf-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        return file.read()
                except Exception as e:
                    logger.error(f"Error reading text file: {str(e)}")
                    return ""
        else:
            # For other document types, use pytextract
            if pytextract is None:
                logger.warning("pytextract not available, cannot handle file: %s", file_path)
                return ""
            try:
                raw_content = pytextract.process(file_path)
                try:
                    text = (
                        raw_content.decode("utf-8", errors="ignore")
                        if isinstance(raw_content, (bytes, bytearray))
                        else str(raw_content)
                    )
                    return text.strip()
                except Exception as decode_error:
                    logger.error(
                        f"Error decoding extracted text: {str(decode_error)}"
                    )
                    return ""
            except Exception as e:
                logger.error(f"Error extracting text with pytextract: {str(e)}")
                return ""

    def chunk_text(self, text):
        """Split text into overlapping chunks"""
        chunks = []
        if self.chunk_size <= 0:
            return [text]
        step = self.chunk_size - self.chunk_overlap
        if step <= 0:
            step = self.chunk_size
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def extract_knowledge(self, text, document_title):
        """Extract entities, concepts, and relationships from text"""
        logger.info(f"Extracting knowledge from document: {document_title}")
        
        # Process the text with spaCy if available
        doc = nlp(text[:100000]) if nlp else None  # Limit to avoid memory issues
        
        # Extract entities
        entities = []
        if doc is not None:
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "LAW", "WORK_OF_ART"]:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })
        
        # Extract key phrases and topics
        topics = []
        # Define programming-related topics
        programming_topics = [
            "Python", "JavaScript", "Java", "C++", "Ruby", "Go", "Rust", 
            "Algorithm", "Data Structure", "API", "Framework", "Library",
            "Database", "SQL", "NoSQL", "REST", "GraphQL", "Function", 
            "Class", "Object", "Method", "Variable", "Loop", "Conditional",
            "Exception", "Error", "Debug", "Test", "Deployment", "Docker",
            "Kubernetes", "Cloud", "AWS", "Azure", "GCP", "DevOps", "CI/CD",
            "Git", "Version Control", "Web Development", "Frontend", "Backend",
            "Full Stack", "Mobile Development", "Desktop Application", "Machine Learning",
            "AI", "Deep Learning", "Neural Network", "NLP", "Computer Vision"
        ]
        # Include additional topics for concept-topic mapping
        programming_topics += [
            "Regular Expressions", "File I/O", "Error Handling",
            "Command Line", "Data Processing"
        ]
        
        # Find topics in the text
        for topic in programming_topics:
            if re.search(r'\b' + re.escape(topic) + r'\b', text, re.IGNORECASE):
                topics.append(topic)
        
        # Extract programming concepts using regex patterns
        concepts = []
        concept_patterns = {
            "Function Definition": r'def\s+\w+\s*\(.*?\)\s*:',
            "Class Definition": r'class\s+\w+(\(.*?\))?\s*:',
            "Variable Assignment": r'\w+\s*=\s*[^=].*',
            "Import Statement": r'import\s+[\w\.]+|from\s+[\w\.]+\s+import',
            "For Loop": r'for\s+\w+\s+in\s+.*:',
            "While Loop": r'while\s+.*:',
            "If Statement": r'if\s+.*:',
            "Try/Except": r'try\s*:.*?except',
            "List Comprehension": r'\[.*for\s+\w+\s+in\s+.*\]',
            "Dictionary Comprehension": r'\{.*:.*for\s+\w+\s+in\s+.*\}',
            "Lambda Function": r'lambda\s+.*:',
            "Regular Expression": r're\.(search|match|findall|sub|split)',
            "File Operations": r'open\(.*\)|with\s+open\(.*\)\s+as',
            "Exception Handling": r'(try|except|finally|raise)',
            "Web Request": r'(requests|urllib|http)',
            "Database Operation": r'(sql|cursor\.execute|SELECT|INSERT|UPDATE|DELETE)',
            "Argparse": r'argparse\.(ArgumentParser|parse_args)',
            "JSON Handling": r'json\.(loads|dumps)',
            "Logging": r'logging\.(info|debug|warning|error|critical)'
        }
        
        for concept_name, pattern in concept_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Get first match as example
                example = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if example:
                    line = text[max(0, example.start() - 50):min(len(text), example.end() + 50)].strip()
                    concepts.append({
                        "name": concept_name,
                        "example": line,
                        "count": len(matches)
                    })
        
        # Create relationships
        relationships = []
        # Document contains topics
        for topic in topics:
            relationships.append({
                "source": document_title,
                "source_type": "Document",
                "target": topic,
                "target_type": "Topic",
                "relationship": "CONTAINS_TOPIC"
            })
        
        # Document demonstrates concepts
        for concept in concepts:
            relationships.append({
                "source": document_title,
                "source_type": "Document",
                "target": concept["name"],
                "target_type": "Concept",
                "relationship": "DEMONSTRATES_CONCEPT"
            })
        
        # Topics related to concepts
        topic_concept_map = {
            "Python": ["Function Definition", "Class Definition", "Import Statement", "List Comprehension"],
            "Regular Expressions": ["Regular Expression"],
            "File I/O": ["File Operations"],
            "Error Handling": ["Try/Except", "Exception Handling"],
            "Web Development": ["Web Request"],
            "Database": ["Database Operation"],
            "Command Line": ["Argparse"],
            "Data Processing": ["JSON Handling", "Lambda Function"],
            "Debugging": ["Logging"]
        }
        
        for topic, concept_list in topic_concept_map.items():
            for concept_name in concept_list:
                for concept in concepts:
                    if concept["name"] == concept_name and topic in topics:
                        relationships.append({
                            "source": topic,
                            "source_type": "Topic",
                            "target": concept_name,
                            "target_type": "Concept",
                            "relationship": "RELATED_TO"
                        })
        
        return {
            "entities": entities,
            "topics": topics,
            "concepts": concepts,
            "relationships": relationships
        }
    
    def extract_personal_knowledge(self, text, document_title):
        """Extract personal information, categories, and relationships from text"""
        logger.info(f"Extracting personal knowledge from document: {document_title}")
        
        # Process the text with spaCy if available
        doc = nlp(text[:100000]) if nlp else None  # Limit to avoid memory issues with large docs
        
        # Initialize results
        personal_entities = []
        personal_topics = []
        personal_concepts = []
        personal_relationships = []
        
        # 1. PERSONAL IDENTIFIERS
        # Extract names (beyond what spaCy might catch)
        name_patterns = [
            r'(?i)name[\s:]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)',
            r'(?i)I am ([A-Z][a-z]+(?: [A-Z][a-z]+)+)',
            r'(?i)(?:Mr|Mrs|Ms|Dr|Prof)\.?\s([A-Z][a-z]+(?: [A-Z][a-z]+)+)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "Person",
                    "category": "Name"
                })
        
        # Extract contact information
        contact_patterns = {
            "Email": r'[\w\.-]+@[\w\.-]+\.\w+',
            "Phone": r'(?:\+\d{1,3}[- ]?)?(?:\(\d{1,4}\)[- ]?)?\d{1,4}[- ]?\d{1,4}[- ]?\d{1,4}',
            "Address": r'\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Terrace|Ter|Place|Pl)',
            "Website": r'https?://(?:www\.)?[\w\.-]+\.\w+(?:/[\w\.-]+)*/?'
        }
        
        for label, pattern in contact_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "ContactInfo",
                    "category": label
                })
        
        # 2. TEMPORAL INFORMATION
        # Extract dates and time references
        date_patterns = {
            "Date": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',
            "Time": r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?',
            "Deadline": r'(?:due|deadline|by)\s+(?:on|before)?\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})'
        }
        
        for label, pattern in date_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "TemporalInfo",
                    "category": label
                })
        
        # 3. EDUCATIONAL INFORMATION
        # Extract education-related information
        education_patterns = {
            "Degree": r'(?:Bachelor|Master|PhD|Doctorate|BSc|BA|MSc|MA|MBA|MD|JD)[^\n.]*(?:Degree|degree|in)[^\n.]*',
            "University": r'(?:University|College|Institute|School) of [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)* (?:University|College|Institute|School)\b',
            "Course": r'(?:Course|class|lecture)[^\n:.]*: [^\n.]*',
            "Grade": r'(?:Grade|mark|score)[^\n:.]*: [^\n.]*|\b[A-B](?:\+|\-)?|[0-9]{1,3}%|(?:Pass|Distinction|Merit|Credit)\b'
        }
        
        for label, pattern in education_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "EducationInfo",
                    "category": label
                })
        
        # 4. PROFESSIONAL INFORMATION
        # Extract work and job-related information
        # Fixed regex pattern to avoid variable-width lookbehind
        work_patterns = {
            "Job_Title": r'(?:Job Title|Position|Role)[^\n:.]*: [^\n.]*|(\n|^)[A-Z][a-z]+(?: [A-Z][a-z]+)*\n',
            "Company": r'(?:Company|Employer|Organization)[^\n:.]*: [^\n.]*|(?:at|with|for) ([A-Z][a-z]*(?:\s+[A-Z][a-z]*)+)',
            "Skill": r'(?:Skill|Proficiency|Expertise)[^\n:.]*: [^\n.]*|(?:proficient|fluent|experienced|skilled) in [^\n.]*',
            "Experience": r'(?:Experience|Work|History)[^\n:.]*: [^\n.]*|(?:[0-9]+(?:\.[0-9]+)?\s+(?:year|month)[s]? (?:of )?experience)'
        }
        
        for label, pattern in work_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):  # Handle grouped matches
                    match = ''.join(m for m in match if m)
                match = match.strip()
                if match:
                    personal_entities.append({
                        "text": match,
                        "type": "ProfessionalInfo",
                        "category": label
                    })
        
        # 5. FINANCIAL INFORMATION
        # Extract financial information (with care for privacy)
        finance_patterns = {
            "Account_Type": r'\b(?:Checking|Savings|Investment|Retirement|401k|IRA|HSA)\s+(?:Account|account)\b',
            "Currency": r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s+(?:dollars|USD|EUR|GBP)',
            "Transaction": r'(?:paid|received|transferred|deposit|withdrawal)[^\n.]*\$\d+(?:,\d{3})*(?:\.\d{2})?',
            "Budget": r'(?:Budget|budgeted|allocated)[^\n.]*\$\d+(?:,\d{3})*(?:\.\d{2})?'
        }
        
        for label, pattern in finance_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "FinancialInfo",
                    "category": label
                })
        
        # 6. HEALTH & MEDICAL INFORMATION
        # Extract health-related information
        health_patterns = {
            "Condition": r'(?:diagnosed|condition|suffering)[^\n.]*(?:with|from) [^\n.]*',
            "Medication": r'(?:medication|prescribed|taking)[^\n.]*(?:mg|tablet|capsule|dose)[^\n.]*',
            "Appointment": r'(?:doctor|physician|specialist|therapist|dentist)[^\n.]*appointment[^\n.]*',
            "Symptom": r'(?:symptom|experiencing|feeling)[^\n:.]*: [^\n.]*'
        }
        
        for label, pattern in health_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "HealthInfo",
                    "category": label
                })
        
        # 7. RELATIONSHIPS & PERSONAL CONNECTIONS
        # Extract family and relationship information
        relationship_patterns = {
            "Family": r'(?:my|his|her|their)[^\n.]*(?:father|mother|brother|sister|parent|child|son|daughter|husband|wife|spouse|grandparent|uncle|aunt)[^\n.]*',
            "Friend": r'(?:my|his|her|their)[^\n.]*(?:friend|buddy|pal|colleague)[^\n.]*',
            "Acquaintance": r'(?:met|know|introduced)[^\n.]*(?:through|via|at)[^\n.]*'
        }
        
        for label, pattern in relationship_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "RelationshipInfo",
                    "category": label
                })
        
        # 8. LOCATIONS & PLACES
        # Extract geographic information
        location_patterns = {
            "Home": r'(?:home|house|apartment|residence|live)[^\n.]*(?:at|in|on)[^\n.]*',
            "Travel": r'(?:traveled|visited|trip|vacation|journey)[^\n.]*(?:to|in|through)[^\n.]*',
            "Favorite_Place": r'(?:favorite|preferred|like)[^\n.]*(?:place|location|spot|destination)[^\n.]*'
        }
        
        for label, pattern in location_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "LocationInfo",
                    "category": label
                })
        
        # 9. PROJECTS & TASKS
        # Extract project information
        project_patterns = {
            "Project": r'(?:project|initiative|assignment)[^\n:.]*: [^\n.]*',
            "Task": r'(?:task|to-do|todo|action item)[^\n:.]*: [^\n.]*',
            "Goal": r'(?:goal|objective|aim|target)[^\n:.]*: [^\n.]*',
            "Status": r'(?:status|progress|update)[^\n:.]*: [^\n.]*'
        }
        
        for label, pattern in project_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "ProjectInfo",
                    "category": label
                })
        
        # 10. INTERESTS & PREFERENCES
        # Extract interest information
        interest_patterns = {
            "Hobby": r'(?:hobby|pastime|leisure)[^\n:.]*: [^\n.]*|(?:enjoy|love)[^\n.]*(?:doing|playing|reading)[^\n.]*',
            "Preference": r'(?:prefer|like|favorite)[^\n.]*(?:over|more than|rather than)[^\n.]*',
            "Collection": r'(?:collect|collection of)[^\n.]*'
        }
        
        for label, pattern in interest_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "InterestInfo",
                    "category": label
                })
        
        # 11. NOTES & THOUGHTS
        # Extract personal notes
        note_patterns = {
            "Reminder": r'(?:remind|remember|don\'t forget)[^\n.]*',
            "Idea": r'(?:idea|thought|concept)[^\n:.]*: [^\n.]*',
            "Personal_Note": r'(?:note to self|personal note)[^\n:.]*: [^\n.]*'
        }
        
        for label, pattern in note_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "NoteInfo",
                    "category": label
                })
        
        # 12. LEGAL INFORMATION
        # Extract legal document information
        legal_patterns = {
            "Contract": r'(?:contract|agreement|terms)[^\n.]*(?:between|with|for)[^\n.]*',
            "Legal_Doc": r'(?:will|testament|power of attorney|lease|deed)[^\n.]*',
            "Identifier": r'(?:passport|license|identification|ID)[^\n.]*(?:number|#)[^\n.]*'
        }
        
        for label, pattern in legal_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                personal_entities.append({
                    "text": match,
                    "type": "LegalInfo",
                    "category": label
                })
        
        # Generate topics from extracted entities
        personal_topics = self.generate_personal_topics(personal_entities)
        
        # Build relationships between document, entities and topics
        document_relationships = self.build_personal_relationships(document_title, personal_entities, personal_topics)
        personal_relationships.extend(document_relationships)
        
        # Return the collected personal knowledge
        return {
            "entities": personal_entities,
            "topics": personal_topics,
            "relationships": personal_relationships
        }

    def generate_personal_topics(self, entities):
        """Generate topics from extracted personal entities"""
        # Count entity types to determine relevant topics
        entity_type_counts = {}
        for entity in entities:
            entity_type = entity["type"]
            if entity_type in entity_type_counts:
                entity_type_counts[entity_type] += 1
            else:
                entity_type_counts[entity_type] = 1
        
        # Generate topics based on entity types that appear frequently
        topics = []
        for entity_type, count in entity_type_counts.items():
            if count >= 2:  # Threshold for topic creation
                topics.append(entity_type)
        
        # Add specific subtopics based on entity categories
        category_counts = {}
        for entity in entities:
            if "category" in entity:
                category = entity["category"]
                entity_type = entity["type"]
                key = f"{entity_type}_{category}"
                
                if key in category_counts:
                    category_counts[key] += 1
                else:
                    category_counts[key] = 1
        
        # Add specific subtopics that appear multiple times
        for key, count in category_counts.items():
            if count >= 2:  # Threshold for subtopic creation
                entity_type, category = key.split("_", 1)
                topics.append(f"{entity_type}: {category}")
        
        return topics

    def build_personal_relationships(self, document_title, entities, topics):
        """Build relationships between document, entities, and topics"""
        relationships = []
        
        # Document contains topics
        for topic in topics:
            relationships.append({
                "source": document_title,
                "source_type": "Document",
                "target": topic,
                "target_type": "PersonalTopic",
                "relationship": "CONTAINS_PERSONAL_TOPIC"
            })
        
        # Document mentions entities
        for entity in entities:
            entity_text = entity["text"]
            entity_type = entity["type"]
            
            # Create a relationship between document and entity
            relationships.append({
                "source": document_title,
                "source_type": "Document",
                "target": entity_text,
                "target_type": "PersonalEntity",
                "relationship": "MENTIONS_ENTITY"
            })
            
            # Create relationships between entities and topics
            for topic in topics:
                if topic == entity_type or topic.startswith(f"{entity_type}:"):
                    relationships.append({
                        "source": entity_text,
                        "source_type": "PersonalEntity",
                        "target": topic,
                        "target_type": "PersonalTopic",
                        "relationship": "BELONGS_TO_TOPIC"
                    })
        
        return relationships
    
    def extract_kb_id_from_path(self, file_path):
        """Extract knowledge base ID from file path"""
        # OpenWebUI stores uploads in a directory structure that includes the KB ID
        # Path format: /app/backend/data/uploads/KNOWLEDGE_BASE_ID/...
        try:
            # Split the path and look for the KB ID
            path_parts = file_path.split(os.path.sep)
            
            # Find the 'uploads' directory index
            if 'uploads' in path_parts:
                uploads_index = path_parts.index('uploads')
                # The KB ID is expected to be right after the 'uploads' directory
                if len(path_parts) > uploads_index + 1:
                    kb_id = path_parts[uploads_index + 1]
                    # Validate that it looks like a UUID (simple check)
                    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', kb_id):
                        logger.info(f"Extracted KB ID from path: {kb_id}")
                        return kb_id
            
            # If we couldn't extract a valid KB ID, check if config file exists
            kb_config_path = os.path.join(os.path.dirname(file_path), ".kb_config")
            if os.path.exists(kb_config_path):
                try:
                    with open(kb_config_path, 'r') as config_file:
                        config_data = json.load(config_file)
                        if 'kb_id' in config_data:
                            logger.info(f"Found KB ID in config file: {config_data['kb_id']}")
                            return config_data['kb_id']
                except Exception as e:
                    logger.error(f"Error reading KB config file: {str(e)}")
            
            # Query the database through HybridSearch to get active KB contexts
            if self.searcher:
                kb_ids = self.searcher.get_available_knowledge_bases()
                if kb_ids and len(kb_ids) > 0:
                    logger.info(f"Using first available KB ID: {kb_ids[0]}")
                    return kb_ids[0]
            
            # Fallback to dynamic default KB ID
            logger.warning(f"Could not extract KB ID from path, using dynamic default: {self.default_kb_id}")
            return self.default_kb_id
            
        except Exception as e:
            logger.error(f"Error extracting KB ID from path: {str(e)}")
            return self.default_kb_id
    
    def add_to_knowledge_graph(self, document_path, document_title, knowledge):
        """Add extracted knowledge to Neo4j"""
        if not self.driver:
            logger.error("Neo4j driver not initialized. Cannot add to knowledge graph.")
            return False
        
        # Extract knowledge base ID from the document path
        kb_id = self.extract_kb_id_from_path(document_path)
        
        try:
            with self.driver.session() as session:
                # Create document node
                session.run("""
                    MERGE (d:Document {title: $title, path: $path, kb_id: $kb_id})
                    SET d.processed_date = $date
                """, {
                    'title': document_title,
                    'path': document_path,
                    'kb_id': kb_id,
                    'date': datetime.now().isoformat()
                })
                
                # Create topic nodes and relationships
                for topic in knowledge["topics"]:
                    session.run("""
                        MERGE (t:Topic {name: $topic})
                        WITH t
                        MATCH (d:Document {title: $doc_title, kb_id: $kb_id})
                        MERGE (d)-[:CONTAINS_TOPIC]->(t)
                    """, {
                        'topic': topic,
                        'doc_title': document_title,
                        'kb_id': kb_id
                    })
                
                # Create concept nodes and relationships
                for concept in knowledge["concepts"]:
                    session.run("""
                        MERGE (c:Concept {name: $name})
                        SET c.example = $example,
                            c.count = $count,
                            c.description = $description
                        WITH c
                        MATCH (d:Document {title: $doc_title, kb_id: $kb_id})
                        MERGE (d)-[:DEMONSTRATES_CONCEPT]->(c)
                    """, {
                        'name': concept["name"],
                        'example': concept["example"],
                        'count': concept["count"],
                        'description': f"A programming concept related to {concept['name']} found in {concept['count']} instances",
                        'doc_title': document_title,
                        'kb_id': kb_id
                    })
                
                # Create relationships between topics and concepts
                for rel in knowledge["relationships"]:
                    if rel["relationship"] == "RELATED_TO":
                        session.run("""
                            MATCH (source:Topic {name: $source})
                            MATCH (target:Concept {name: $target})
                            MERGE (source)-[:RELATED_TO]->(target)
                        """, {
                            'source': rel["source"],
                            'target': rel["target"]
                        })
                
                logger.info(f"Added document knowledge to Neo4j for: {document_title} (KB: {kb_id})")
                return True
                
        except Exception as e:
            logger.error(f"Error adding knowledge to Neo4j: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def add_personal_knowledge_to_graph(self, document_path, document_title, knowledge):
        """Add extracted personal knowledge to Neo4j"""
        if not self.driver:
            logger.error("Neo4j driver not initialized. Cannot add personal knowledge to graph.")
            return False
        
        # Extract knowledge base ID from the document path
        kb_id = self.extract_kb_id_from_path(document_path)
        
        try:
            with self.driver.session() as session:
                # Create document node (reuse existing if present)
                session.run("""
                    MERGE (d:Document {title: $title, path: $path, kb_id: $kb_id})
                    SET d.processed_date = $date,
                        d.contains_personal_info = true
                """, {
                    'title': document_title,
                    'path': document_path,
                    'kb_id': kb_id,
                    'date': datetime.now().isoformat()
                })
                
                # Create personal entity nodes and relationships
                for entity in knowledge["entities"]:
                    entity_text = entity["text"]
                    entity_type = entity["type"]
                    entity_category = entity.get("category", "")
                    
                    # Create entity node
                    session.run("""
                        MERGE (e:PersonalEntity {text: $text, type: $type, category: $category, kb_id: $kb_id})
                        WITH e
                        MATCH (d:Document {title: $doc_title, kb_id: $kb_id})
                        MERGE (d)-[:MENTIONS_ENTITY]->(e)
                    """, {
                        'text': entity_text,
                        'type': entity_type,
                        'category': entity_category,
                        'doc_title': document_title,
                        'kb_id': kb_id
                    })
                
                # Create personal topic nodes and relationships
                for topic in knowledge["topics"]:
                    session.run("""
                        MERGE (t:PersonalTopic {name: $topic, kb_id: $kb_id})
                        WITH t
                        MATCH (d:Document {title: $doc_title, kb_id: $kb_id})
                        MERGE (d)-[:CONTAINS_PERSONAL_TOPIC]->(t)
                    """, {
                        'topic': topic,
                        'doc_title': document_title,
                        'kb_id': kb_id
                    })
                
                # Create additional relationships between entities and topics
                for rel in knowledge["relationships"]:
                    if rel["source_type"] == "PersonalEntity" and rel["target_type"] == "PersonalTopic":
                        session.run("""
                            MATCH (source:PersonalEntity {text: $source, kb_id: $kb_id})
                            MATCH (target:PersonalTopic {name: $target, kb_id: $kb_id})
                            MERGE (source)-[:BELONGS_TO_TOPIC]->(target)
                        """, {
                            'source': rel["source"],
                            'target': rel["target"],
                            'kb_id': kb_id
                        })
                
                logger.info(f"Added personal knowledge to Neo4j for: {document_title} (KB: {kb_id})")
                return True
                
        except Exception as e:
            logger.error(f"Error adding personal knowledge to Neo4j: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def add_vector_to_milvus(self, title, path, content, kb_id, embedding):
        """Insert document embedding and metadata into Milvus"""
        if Collection is None or utility is None or not self.searcher:
            logger.warning("Milvus not available; skipping vector insertion")
            return

        try:
            collection_name = f"documents_{kb_id.replace('-', '_')}"

            # Create collection if it doesn't exist
            if not utility.has_collection(collection_name):
                if not self.searcher._initialize_vector_collection(kb_id):
                    logger.error(f"Failed to initialize Milvus collection for KB: {kb_id}")
                    return

            collection = Collection(collection_name)
            collection.load()

            data = [
                [title],
                [path],
                [content],
                [kb_id],
                [embedding],
            ]
            collection.insert(data)
            collection.flush()
            logger.info(
                f"Inserted vector for {title} into Milvus collection {collection_name}"
            )
        except Exception as e:
            logger.error(f"Error inserting vector into Milvus: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            try:
                if 'collection' in locals():
                    collection.release()
            except Exception:
                pass
    
    def process_document(self, file_path):
        """Process a document and add its knowledge to Neo4j"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return False
            
            # Get document title
            document_title = os.path.basename(file_path)
            
            # Extract KB ID for this document
            kb_id = self.extract_kb_id_from_path(file_path)
            
            # Check if already processed
            file_hash = self.get_file_hash(file_path)
            processed_path = os.path.join(self.processed_dir, f"{kb_id}_{file_hash}")
            if os.path.exists(processed_path):
                logger.info(f"Document already processed: {document_title} (KB: {kb_id})")
                return True
            
            logger.info(f"Processing document: {document_title} (KB: {kb_id})")
            
            # Extract text from document
            text = self.extract_text_from_document(file_path)
            if not text:
                logger.error(f"Failed to extract text from document: {document_title}")
                return False
            
            # Generate vector embeddings per chunk and store in Milvus
            if self.searcher and self.searcher._initialize_vector_collection(kb_id):
                chunks = self.chunk_text(text)
                for i in range(0, len(chunks), self.processing_batch_size):
                    batch = chunks[i : i + self.processing_batch_size]
                    for chunk in batch:
                        embedding = self.searcher._get_embedding(chunk)
                        if embedding is not None:
                            self.add_vector_to_milvus(
                                document_title,
                                file_path,
                                chunk,
                                kb_id,
                                embedding,
                            )
            elif self.searcher:
                logger.error(f"Failed to initialize vector collection for KB: {kb_id}")

            # Extract technical knowledge (original functionality)
            technical_knowledge = self.extract_knowledge(text, document_title)
            
            # Extract personal knowledge (new functionality)
            personal_knowledge = self.extract_personal_knowledge(text, document_title)
            
            # Add technical knowledge to Neo4j
            tech_success = self.add_to_knowledge_graph(file_path, document_title, technical_knowledge)
            
            # Add personal knowledge to Neo4j
            personal_success = self.add_personal_knowledge_to_graph(file_path, document_title, personal_knowledge)
            
            if tech_success or personal_success:
                # Mark as processed
                with open(processed_path, 'w') as f:
                    f.write(json.dumps({
                        'file': file_path,
                        'title': document_title,
                        'kb_id': kb_id,
                        'processed_date': datetime.now().isoformat(),
                        'topics': technical_knowledge["topics"] + personal_knowledge["topics"],
                        'entities': [e["text"] for e in personal_knowledge["entities"]]
                    }))
                logger.info(f"Document processed successfully: {document_title} (KB: {kb_id})")
                return True
            else:
                logger.error(f"Failed to add knowledge to Neo4j for document: {document_title} (KB: {kb_id})")
                return False
                
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def get_file_hash(self, file_path):
        """Generate a hash for the file to track processed state"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {str(e)}")
            # Fall back to filename and size if hashing fails
            file_stat = os.stat(file_path)
            return f"{os.path.basename(file_path)}_{file_stat.st_size}_{file_stat.st_mtime}"
    
    def discover_knowledge_bases(self):
        """Discover all knowledge bases in the uploads directory and Neo4j"""
        kb_ids = set()
        try:
            # Step 1: Query Neo4j for existing KB IDs
            if self.driver:
                with self.driver.session() as session:
                    result = session.run("""
                        MATCH (d:Document) 
                        WHERE d.kb_id IS NOT NULL 
                        RETURN DISTINCT d.kb_id AS kb_id
                    """)
                    
                    for record in result:
                        if record["kb_id"]:
                            kb_ids.add(record["kb_id"])
            
            # Step 2: Check if the uploads directory exists and scan for KB IDs
            if os.path.exists(self.uploads_dir):
                # Walk through the uploads directory structure to find KB IDs
                for item in os.listdir(self.uploads_dir):
                    item_path = os.path.join(self.uploads_dir, item)
                    if os.path.isdir(item_path):
                        # Check if the directory name looks like a UUID (KB ID)
                        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', item):
                            kb_ids.add(item)
                        
                        # Also check for .kb_config files
                        kb_config_path = os.path.join(item_path, ".kb_config")
                        if os.path.exists(kb_config_path):
                            try:
                                with open(kb_config_path, 'r') as config_file:
                                    config_data = json.load(config_file)
                                    if 'kb_id' in config_data:
                                        kb_ids.add(config_data['kb_id'])
                            except Exception as e:
                                logger.error(f"Error reading KB config file: {str(e)}")
            
            # If no KB IDs found, use the dynamic default
            if not kb_ids:
                logger.warning(f"No knowledge bases found, using dynamic default: {self.default_kb_id}")
                kb_ids.add(self.default_kb_id)
            
            logger.info(f"Discovered knowledge bases: {kb_ids}")
            return list(kb_ids)
        
        except Exception as e:
            logger.error(f"Error discovering knowledge bases: {str(e)}")
            return [self.default_kb_id]
    
    def process_existing_documents(self):
        """Process all existing documents in the uploads directory"""
        logger.info(f"Processing existing documents in {self.uploads_dir}")
        
        # Check if directory exists
        if not os.path.exists(self.uploads_dir):
            logger.error(f"Uploads directory does not exist: {self.uploads_dir}")
            logger.info("Creating uploads directory...")
            try:
                os.makedirs(self.uploads_dir, exist_ok=True)
                logger.info(f"Created uploads directory: {self.uploads_dir}")
            except Exception as e:
                logger.error(f"Failed to create uploads directory: {str(e)}")
                return
        
        # Discover all knowledge bases
        kb_ids = self.discover_knowledge_bases()
        
        try:
            # Process documents for each knowledge base
            for kb_id in kb_ids:
                kb_path = os.path.join(self.uploads_dir, kb_id)
                if os.path.exists(kb_path) and os.path.isdir(kb_path):
                    logger.info(f"Processing documents for knowledge base: {kb_id}")
                    for root, dirs, files in os.walk(kb_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            self.process_document(file_path)
                else:
                    logger.warning(f"Knowledge base directory does not exist: {kb_path}")
            
            # Also process documents in the main uploads directory (if any)
            for file in os.listdir(self.uploads_dir):
                file_path = os.path.join(self.uploads_dir, file)
                if os.path.isfile(file_path):
                    self.process_document(file_path)
        
        except Exception as e:
            logger.error(f"Error walking uploads directory: {str(e)}")
            logger.error(traceback.format_exc())
                
        logger.info("Finished processing existing documents")


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor
        
    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"New file detected: {event.src_path}")
            # Add a small delay to ensure file is fully written
            time.sleep(2)
            self.processor.process_document(event.src_path)
            
    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"File modified: {event.src_path}")
            # Add a small delay to ensure file is fully written
            time.sleep(2)
            self.processor.process_document(event.src_path)


def main():
    logger.info("Starting Document Processor service")
    
    # Create processor
    processor = DocumentProcessor()
    
    # Process existing documents
    processor.process_existing_documents()
    
    # Check if directory exists
    if not os.path.exists(processor.uploads_dir):
        logger.error(f"Uploads directory does not exist: {processor.uploads_dir}")
        logger.info("Creating uploads directory...")
        try:
            os.makedirs(processor.uploads_dir, exist_ok=True)
            logger.info(f"Created uploads directory: {processor.uploads_dir}")
        except Exception as e:
            logger.error(f"Failed to create uploads directory: {str(e)}")
            return
    
    # Set up file watcher
    event_handler = FileEventHandler(processor)
    if Observer is None:
        logger.warning("watchdog not available; directory monitoring disabled")
        observer = None
    else:
        observer = Observer()
    
    # Watch the uploads directory
    if observer:
        try:
            logger.info(f"Attempting to watch directory: {processor.uploads_dir}")
            observer.schedule(event_handler, processor.uploads_dir, recursive=True)
            observer.start()
            logger.info(f"Now watching for new documents in {processor.uploads_dir}")
        except Exception as e:
            logger.error(f"Failed to start directory observer: {str(e)}")
            logger.error(traceback.format_exc())
            return
    
    # Keep the main thread running
    try:
        logger.info("Main loop starting")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping service")
        if observer:
            observer.stop()
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        logger.error(traceback.format_exc())
    
    if observer:
        observer.join()
    logger.info("Document Processor service stopped")


if __name__ == "__main__":
    main()
