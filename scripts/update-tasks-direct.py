#!/usr/bin/env python3

import json
import subprocess
import sys
from typing import Dict, List, Any

# JarvisAI project ID
PROJECT_ID = '9a641921-b355-4214-a73c-2dc1be7fd132'

# Complete task list from COMPLETE_TASK_LIST.md
COMPLETE_TASKS = [
    # Core Infrastructure Tasks
    {"title": "FastAPI Core Structure", "description": "JWT auth, middleware, exception handling", "estimatedHours": 8, "category": "Backend API Development"},
    {"title": "Database Models & Migrations", "description": "User, Chat, Document, Agent models", "estimatedHours": 6, "category": "Backend API Development"},
    {"title": "WebSocket Implementation", "description": "Real-time chat streaming", "estimatedHours": 4, "category": "Backend API Development"},
    {"title": "API Rate Limiting", "description": "Per-user and global limits", "estimatedHours": 3, "category": "Backend API Development"},
    {"title": "Health Check Endpoints", "description": "Service monitoring APIs", "estimatedHours": 2, "category": "Backend API Development"},
    {"title": "Metrics Collection", "description": "Prometheus integration", "estimatedHours": 3, "category": "Backend API Development"},
    
    # Authentication & Security
    {"title": "OAuth 3.0 Implementation", "description": "Latest OAuth standard with PKCE flow", "estimatedHours": 6, "category": "Authentication & Security"},
    {"title": "User Approval Workflow", "description": "Admin approval system", "estimatedHours": 4, "category": "Authentication & Security"},
    {"title": "Role-Based Access Control", "description": "Admin/User permissions", "estimatedHours": 4, "category": "Authentication & Security"},
    {"title": "Session Management", "description": "JWT tokens and refresh", "estimatedHours": 3, "category": "Authentication & Security"},
    {"title": "API Key Management", "description": "For external service auth", "estimatedHours": 2, "category": "Authentication & Security"},
    {"title": "Audit Logging System", "description": "Track all user actions", "estimatedHours": 3, "category": "Authentication & Security"},
    
    # LLM Integration
    {"title": "Ollama Service Setup", "description": "GPU support configuration", "estimatedHours": 6, "category": "LLM Integration"},
    {"title": "Model Management API", "description": "Load/unload models dynamically", "estimatedHours": 5, "category": "LLM Integration"},
    {"title": "Multi-Model Switching", "description": "Hot-swap between models", "estimatedHours": 4, "category": "LLM Integration"},
    {"title": "GPU Memory Optimization", "description": "Dynamic allocation across 2 GPUs", "estimatedHours": 4, "category": "LLM Integration"},
    {"title": "Model Performance Monitoring", "description": "Track inference times", "estimatedHours": 3, "category": "LLM Integration"},
    {"title": "Streaming Response Handler", "description": "Token-by-token output", "estimatedHours": 3, "category": "LLM Integration"},
    
    # Vector Database Setup
    {"title": "Milvus with GPU Acceleration", "description": "NVIDIA GPU-optimized vector database setup", "estimatedHours": 5, "category": "Vector Database Setup"},
    {"title": "Collection Schema Design", "description": "Documents, chat, memory collections", "estimatedHours": 3, "category": "Vector Database Setup"},
    {"title": "Embedding Pipeline", "description": "BGE-M3 integration", "estimatedHours": 4, "category": "Vector Database Setup"},
    {"title": "Late Chunking Implementation", "description": "Context-aware chunking for better retrieval", "estimatedHours": 5, "category": "Vector Database Setup"},
    {"title": "NVIDIA CAGRA Index Setup", "description": "GPU-accelerated graph-based indexing", "estimatedHours": 4, "category": "Vector Database Setup"},
    {"title": "Multi-tenant Data Isolation", "description": "User-specific namespaces", "estimatedHours": 3, "category": "Vector Database Setup"},
    
    # Document Processing
    {"title": "Docling Integration", "description": "IBM document parser setup", "estimatedHours": 4, "category": "Document Processing"},
    {"title": "PaddleOCR Setup", "description": "OCR for scanned documents", "estimatedHours": 4, "category": "Document Processing"},
    {"title": "File Type Handlers", "description": "PDF, DOCX, XLSX, PPTX, EPUB", "estimatedHours": 6, "category": "Document Processing"},
    {"title": "Metadata Extraction", "description": "Author, date, sections", "estimatedHours": 3, "category": "Document Processing"},
    {"title": "Document Summary Generation", "description": "Auto-summarize uploads", "estimatedHours": 3, "category": "Document Processing"},
    {"title": "Duplicate Detection", "description": "Hash-based deduplication", "estimatedHours": 2, "category": "Document Processing"},
    
    # Memory Systems
    {"title": "Long-term Conversation Memory", "description": "Store chat history", "estimatedHours": 4, "category": "Memory Systems"},
    {"title": "User Profile Memory", "description": "Persistent preferences", "estimatedHours": 3, "category": "Memory Systems"},
    {"title": "Episodic Memory System", "description": "Event-based storage", "estimatedHours": 4, "category": "Memory Systems"},
    {"title": "Memory Retrieval Logic", "description": "Context-aware fetching", "estimatedHours": 4, "category": "Memory Systems"},
    {"title": "Memory Expiry/Cleanup", "description": "Aging out old data", "estimatedHours": 3, "category": "Memory Systems"},
    {"title": "Memory Privacy Controls", "description": "User data isolation", "estimatedHours": 3, "category": "Memory Systems"},
    
    # Agent Framework
    {"title": "LangGraph Agent Orchestration", "description": "Production-ready multi-agent workflows with LangGraph", "estimatedHours": 7, "category": "Agent Framework"},
    {"title": "Agent State Management", "description": "Workflow state tracking", "estimatedHours": 4, "category": "Agent Framework"},
    {"title": "Tool Registry System", "description": "Dynamic tool loading", "estimatedHours": 3, "category": "Agent Framework"},
    {"title": "Chain-of-Thought Implementation", "description": "ReAct pattern", "estimatedHours": 4, "category": "Agent Framework"},
    {"title": "Agent Memory/Checkpointing", "description": "State persistence", "estimatedHours": 3, "category": "Agent Framework"},
    {"title": "Multi-Agent Coordination", "description": "Agent-to-agent communication", "estimatedHours": 5, "category": "Agent Framework"},
    
    # Tool Implementation
    {"title": "Python Code Sandbox", "description": "Docker-based execution", "estimatedHours": 6, "category": "Tool Implementation"},
    {"title": "API Calling Tool", "description": "External API integration", "estimatedHours": 4, "category": "Tool Implementation"},
    {"title": "File Management Tool", "description": "Read/write user files", "estimatedHours": 3, "category": "Tool Implementation"},
    {"title": "Web Fetch Tool", "description": "URL content retrieval", "estimatedHours": 3, "category": "Tool Implementation"},
    {"title": "Web Search Tool", "description": "Optional search API integration", "estimatedHours": 4, "category": "Tool Implementation"},
    {"title": "Tool Security Sandbox", "description": "Resource limits, isolation", "estimatedHours": 4, "category": "Tool Implementation"},
    {"title": "Tool Usage Analytics", "description": "Track tool invocations", "estimatedHours": 2, "category": "Tool Implementation"},
    
    # Core UI Development
    {"title": "Next.js 15 with React 19 and Turbopack", "description": "Latest framework setup with Turbopack bundler", "estimatedHours": 5, "category": "Core UI Development"},
    {"title": "Chat Interface", "description": "Message threading, markdown", "estimatedHours": 6, "category": "Core UI Development"},
    {"title": "Model Switcher UI", "description": "Dynamic model selection", "estimatedHours": 3, "category": "Core UI Development"},
    {"title": "File Upload Interface", "description": "Drag-drop, progress", "estimatedHours": 4, "category": "Core UI Development"},
    {"title": "Memory Management UI", "description": "View/delete memories", "estimatedHours": 4, "category": "Core UI Development"},
    {"title": "Tool Console UI", "description": "Show agent actions", "estimatedHours": 3, "category": "Core UI Development"},
    {"title": "Settings/Preferences UI", "description": "User customization", "estimatedHours": 3, "category": "Core UI Development"},
    
    # Advanced UI Features
    {"title": "Therapeutic Mode UI", "description": "Separate interface/theme", "estimatedHours": 4, "category": "Advanced UI Features"},
    {"title": "Admin Dashboard", "description": "User management, metrics", "estimatedHours": 6, "category": "Advanced UI Features"},
    {"title": "Mobile Responsive Design", "description": "Touch-friendly UI", "estimatedHours": 4, "category": "Advanced UI Features"},
    {"title": "Dark/Light Theme", "description": "Theme switching", "estimatedHours": 2, "category": "Advanced UI Features"},
    {"title": "Internationalization", "description": "Multi-language support", "estimatedHours": 3, "category": "Advanced UI Features"},
    {"title": "Accessibility Features", "description": "Screen reader support", "estimatedHours": 3, "category": "Advanced UI Features"},
    
    # Therapeutic Mode Tasks
    {"title": "Therapeutic Model Integration", "description": "Safespace/Clarity with ADHD/autism specialization", "estimatedHours": 5, "category": "Therapeutic Mode"},
    {"title": "Mode Switching Logic", "description": "Context separation", "estimatedHours": 3, "category": "Therapeutic Mode"},
    {"title": "Crisis Detection System", "description": "Keyword monitoring", "estimatedHours": 3, "category": "Therapeutic Mode"},
    {"title": "Neurodivergent-Optimized Prompting", "description": "ADHD/autism-specific conversational patterns", "estimatedHours": 5, "category": "Therapeutic Mode"},
    {"title": "Session Privacy Controls", "description": "Encrypted storage", "estimatedHours": 3, "category": "Therapeutic Mode"},
    {"title": "Consent Management", "description": "Mode activation flow", "estimatedHours": 2, "category": "Therapeutic Mode"},
    {"title": "Professional Help Resources", "description": "Crisis resources", "estimatedHours": 2, "category": "Therapeutic Mode"},
    
    # Monitoring Stack
    {"title": "Prometheus Configuration", "description": "Metrics collection", "estimatedHours": 4, "category": "Monitoring Stack"},
    {"title": "Grafana Dashboards", "description": "System visualization", "estimatedHours": 4, "category": "Monitoring Stack"},
    {"title": "Loki Log Aggregation", "description": "Centralized logging", "estimatedHours": 3, "category": "Monitoring Stack"},
    {"title": "Alert Rules Setup", "description": "Critical issue alerts", "estimatedHours": 3, "category": "Monitoring Stack"},
    {"title": "Custom Metrics", "description": "AI-specific metrics", "estimatedHours": 3, "category": "Monitoring Stack"},
    {"title": "Performance Dashboards", "description": "GPU, latency tracking", "estimatedHours": 3, "category": "Monitoring Stack"},
    
    # Infrastructure
    {"title": "Docker Compose GPU Configuration", "description": "NVIDIA runtime and GPU resource allocation", "estimatedHours": 4, "category": "Infrastructure"},
    {"title": "MinIO Object Storage Setup", "description": "S3-compatible storage for documents and models", "estimatedHours": 4, "category": "Infrastructure"},
    {"title": "Docker Network Security", "description": "Container isolation", "estimatedHours": 3, "category": "Infrastructure"},
    {"title": "Volume Backup Strategy", "description": "Data persistence", "estimatedHours": 3, "category": "Infrastructure"},
    {"title": "Health Check Scripts", "description": "Service monitoring", "estimatedHours": 2, "category": "Infrastructure"},
    {"title": "Auto-restart Policies", "description": "Failure recovery", "estimatedHours": 2, "category": "Infrastructure"},
    {"title": "Resource Limits", "description": "CPU/Memory caps", "estimatedHours": 2, "category": "Infrastructure"},
    
    # Ingestion Systems
    {"title": "URL Crawler Implementation", "description": "Multi-page support", "estimatedHours": 4, "category": "Ingestion Systems"},
    {"title": "Periodic URL Refresh", "description": "Auto-update content", "estimatedHours": 3, "category": "Ingestion Systems"},
    {"title": "Bulk Document Import", "description": "Batch processing", "estimatedHours": 3, "category": "Ingestion Systems"},
    {"title": "Progress Tracking", "description": "Ingestion status", "estimatedHours": 2, "category": "Ingestion Systems"},
    {"title": "Error Recovery", "description": "Failed document handling", "estimatedHours": 3, "category": "Ingestion Systems"},
    
    # Search & Retrieval
    {"title": "Hybrid Search", "description": "Vector + keyword search", "estimatedHours": 4, "category": "Search & Retrieval"},
    {"title": "OpenSearch Full-Text Integration", "description": "Production-grade text search", "estimatedHours": 5, "category": "Search & Retrieval"},
    {"title": "pgvector Optimization", "description": "PostgreSQL vector search performance tuning", "estimatedHours": 4, "category": "Search & Retrieval"},
    {"title": "Search Ranking Algorithm", "description": "Relevance scoring", "estimatedHours": 3, "category": "Search & Retrieval"},
    {"title": "Context Window Management", "description": "Chunk selection", "estimatedHours": 3, "category": "Search & Retrieval"},
    {"title": "Source Attribution", "description": "Citation system", "estimatedHours": 2, "category": "Search & Retrieval"},
    
    # Testing Infrastructure
    {"title": "Unit Test Suite", "description": "Backend coverage", "estimatedHours": 6, "category": "Testing Infrastructure"},
    {"title": "Integration Tests", "description": "Service interactions", "estimatedHours": 6, "category": "Testing Infrastructure"},
    {"title": "E2E Tests with Puppeteer", "description": "UI workflows", "estimatedHours": 5, "category": "Testing Infrastructure"},
    {"title": "Performance Tests", "description": "Load testing", "estimatedHours": 4, "category": "Testing Infrastructure"},
    {"title": "Security Tests", "description": "Penetration testing", "estimatedHours": 4, "category": "Testing Infrastructure"},
    
    # Quality Assurance
    {"title": "Code Linting Setup", "description": "ESLint, Black, etc.", "estimatedHours": 2, "category": "Quality Assurance"},
    {"title": "Type Checking", "description": "TypeScript, mypy", "estimatedHours": 2, "category": "Quality Assurance"},
    {"title": "API Documentation", "description": "OpenAPI/Swagger", "estimatedHours": 3, "category": "Quality Assurance"},
    {"title": "User Documentation", "description": "Guides and tutorials", "estimatedHours": 4, "category": "Quality Assurance"},
    
    # Deployment & DevOps
    {"title": "CI/CD Pipeline", "description": "GitHub Actions setup", "estimatedHours": 4, "category": "Deployment & DevOps"},
    {"title": "Environment Configuration", "description": "Dev/staging/prod", "estimatedHours": 3, "category": "Deployment & DevOps"},
    {"title": "SSL/TLS Setup", "description": "HTTPS configuration", "estimatedHours": 3, "category": "Deployment & DevOps"},
    {"title": "Backup Automation", "description": "Scheduled backups", "estimatedHours": 3, "category": "Deployment & DevOps"},
    {"title": "Disaster Recovery Plan", "description": "Restore procedures", "estimatedHours": 3, "category": "Deployment & DevOps"},
    {"title": "Deployment Scripts", "description": "One-click deploy", "estimatedHours": 3, "category": "Deployment & DevOps"},
    
    # Integration Tasks
    {"title": "MCP Server Integration", "description": "Connect to existing MCP ecosystem", "estimatedHours": 4, "category": "Integration"},
    {"title": "External API Connectors", "description": "Third-party services", "estimatedHours": 4, "category": "Integration"},
    {"title": "Webhook System", "description": "Event notifications", "estimatedHours": 3, "category": "Integration"},
    {"title": "Plugin Architecture", "description": "Extensibility framework", "estimatedHours": 5, "category": "Integration"},
    
    # Advanced Features
    {"title": "Redis LangCache Semantic Caching", "description": "LLM response caching with semantic search", "estimatedHours": 5, "category": "Advanced Features"},
    {"title": "Query Planning Optimizer", "description": "Smart retrieval", "estimatedHours": 4, "category": "Advanced Features"},
    {"title": "Model Fine-tuning Pipeline", "description": "Custom training", "estimatedHours": 6, "category": "Advanced Features"},
    {"title": "Federation Support", "description": "Multi-instance sync", "estimatedHours": 5, "category": "Advanced Features"},
    {"title": "Voice Integration Prep", "description": "API structure for future", "estimatedHours": 3, "category": "Advanced Features"},
    {"title": "Vision Model Prep", "description": "Multimodal architecture", "estimatedHours": 4, "category": "Advanced Features"}
]

def run_mcp_command(server: str, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run an MCP command and return the result."""
    cmd = [
        'npx', '@modelcontextprotocol/cli', 'query',
        f'mcp://project-tasks',
        '--tool', tool,
        '--params', json.dumps(params)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing MCP command: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw output: {result.stdout}")
        raise

def get_current_tasks() -> List[Dict[str, Any]]:
    """Get all current tasks for the JarvisAI project."""
    print("Fetching current tasks for JarvisAI project...")
    try:
        result = run_mcp_command('project-tasks', 'get_project_tasks', {'project_id': PROJECT_ID})
        tasks = result.get('tasks', [])
        print(f"Found {len(tasks)} existing tasks")
        return tasks
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []

def create_task(task: Dict[str, Any]) -> bool:
    """Create a new task."""
    print(f"Creating task: {task['title']}")
    try:
        params = {
            'project_id': PROJECT_ID,
            'title': task['title'],
            'description': task['description'],
            'status': 'TODO',
            'priority': 'MEDIUM',
            'estimated_hours': task['estimatedHours'],
            'tags': [task['category']]
        }
        
        result = run_mcp_command('project-tasks', 'create_task', params)
        print(f"✅ Created: {task['title']}")
        return True
    except Exception as e:
        print(f"❌ Failed to create task '{task['title']}': {e}")
        return False

def update_task(task_id: str, updates: Dict[str, Any]) -> bool:
    """Update an existing task."""
    print(f"Updating task ID: {task_id}")
    try:
        params = {'task_id': task_id, **updates}
        result = run_mcp_command('project-tasks', 'update_task', params)
        print(f"✅ Updated task ID: {task_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to update task ID {task_id}: {e}")
        return False

def delete_task(task_id: str) -> bool:
    """Delete a task."""
    print(f"Deleting task ID: {task_id}")
    try:
        result = run_mcp_command('project-tasks', 'delete_task', {'task_id': task_id})
        print(f"✅ Deleted task ID: {task_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to delete task ID {task_id}: {e}")
        return False

def main():
    print("Starting JarvisAI 2025 task update...\n")
    
    # Get current tasks
    current_tasks = get_current_tasks()
    
    # Create a map of existing tasks by title for easy lookup
    existing_tasks_map = {}
    for task in current_tasks:
        existing_tasks_map[task['title'].lower()] = task
    
    # Track what we need to do
    tasks_to_update = []
    tasks_to_create = []
    tasks_to_delete = []
    
    # Check each complete task
    for complete_task in COMPLETE_TASKS:
        existing_task = existing_tasks_map.get(complete_task['title'].lower())
        
        if existing_task:
            # Check if update is needed
            needs_update = (
                existing_task.get('description', '') != complete_task['description'] or
                existing_task.get('estimated_hours', 0) != complete_task['estimatedHours'] or
                complete_task['category'] not in existing_task.get('tags', [])
            )
            
            if needs_update:
                tasks_to_update.append({
                    'id': existing_task['id'],
                    'updates': {
                        'description': complete_task['description'],
                        'estimated_hours': complete_task['estimatedHours'],
                        'tags': [complete_task['category']]
                    }
                })
            
            # Remove from map to track what's left
            del existing_tasks_map[complete_task['title'].lower()]
        else:
            # Task doesn't exist, need to create
            tasks_to_create.append(complete_task)
    
    # Any tasks left in the map are ones that exist but aren't in our complete list
    # Check for specific replacements
    for title, task in existing_tasks_map.items():
        if 'qdrant' in title or 'oauth2' in title or 'oauth 2' in title:
            tasks_to_delete.append(task['id'])
    
    # Execute updates
    print(f"\n📊 Update Summary:")
    print(f"- Tasks to create: {len(tasks_to_create)}")
    print(f"- Tasks to update: {len(tasks_to_update)}")
    print(f"- Tasks to delete: {len(tasks_to_delete)}")
    print(f"\nTotal tasks after update: {len(COMPLETE_TASKS)}\n")
    
    # Delete old tasks
    if tasks_to_delete:
        print("\n🗑️  Deleting obsolete tasks...")
        for task_id in tasks_to_delete:
            delete_task(task_id)
    
    # Update existing tasks
    if tasks_to_update:
        print("\n🔄 Updating existing tasks...")
        for update_info in tasks_to_update:
            update_task(update_info['id'], update_info['updates'])
    
    # Create new tasks
    if tasks_to_create:
        print("\n➕ Creating new tasks...")
        for task in tasks_to_create:
            create_task(task)
    
    print("\n✅ JarvisAI 2025 task update complete!")
    
    # Verify final count
    final_tasks = get_current_tasks()
    print(f"\n📈 Final task count: {len(final_tasks)} (Expected: {len(COMPLETE_TASKS)})")

if __name__ == "__main__":
    main()