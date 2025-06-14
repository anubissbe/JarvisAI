#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// JarvisAI project ID
const PROJECT_ID = '9a641921-b355-4214-a73c-2dc1be7fd132';

// Complete task list from COMPLETE_TASK_LIST.md
const COMPLETE_TASKS = [
  // Core Infrastructure Tasks
  { title: "FastAPI Core Structure", description: "JWT auth, middleware, exception handling", estimatedHours: 8, category: "Backend API Development" },
  { title: "Database Models & Migrations", description: "User, Chat, Document, Agent models", estimatedHours: 6, category: "Backend API Development" },
  { title: "WebSocket Implementation", description: "Real-time chat streaming", estimatedHours: 4, category: "Backend API Development" },
  { title: "API Rate Limiting", description: "Per-user and global limits", estimatedHours: 3, category: "Backend API Development" },
  { title: "Health Check Endpoints", description: "Service monitoring APIs", estimatedHours: 2, category: "Backend API Development" },
  { title: "Metrics Collection", description: "Prometheus integration", estimatedHours: 3, category: "Backend API Development" },
  
  // Authentication & Security
  { title: "OAuth 3.0 Implementation", description: "Latest OAuth standard with PKCE flow", estimatedHours: 6, category: "Authentication & Security" },
  { title: "User Approval Workflow", description: "Admin approval system", estimatedHours: 4, category: "Authentication & Security" },
  { title: "Role-Based Access Control", description: "Admin/User permissions", estimatedHours: 4, category: "Authentication & Security" },
  { title: "Session Management", description: "JWT tokens and refresh", estimatedHours: 3, category: "Authentication & Security" },
  { title: "API Key Management", description: "For external service auth", estimatedHours: 2, category: "Authentication & Security" },
  { title: "Audit Logging System", description: "Track all user actions", estimatedHours: 3, category: "Authentication & Security" },
  
  // LLM Integration
  { title: "Ollama Service Setup", description: "GPU support configuration", estimatedHours: 6, category: "LLM Integration" },
  { title: "Model Management API", description: "Load/unload models dynamically", estimatedHours: 5, category: "LLM Integration" },
  { title: "Multi-Model Switching", description: "Hot-swap between models", estimatedHours: 4, category: "LLM Integration" },
  { title: "GPU Memory Optimization", description: "Dynamic allocation across 2 GPUs", estimatedHours: 4, category: "LLM Integration" },
  { title: "Model Performance Monitoring", description: "Track inference times", estimatedHours: 3, category: "LLM Integration" },
  { title: "Streaming Response Handler", description: "Token-by-token output", estimatedHours: 3, category: "LLM Integration" },
  
  // Vector Database Setup
  { title: "Milvus with GPU Acceleration", description: "NVIDIA GPU-optimized vector database setup", estimatedHours: 5, category: "Vector Database Setup" },
  { title: "Collection Schema Design", description: "Documents, chat, memory collections", estimatedHours: 3, category: "Vector Database Setup" },
  { title: "Embedding Pipeline", description: "BGE-M3 integration", estimatedHours: 4, category: "Vector Database Setup" },
  { title: "Late Chunking Implementation", description: "Context-aware chunking for better retrieval", estimatedHours: 5, category: "Vector Database Setup" },
  { title: "NVIDIA CAGRA Index Setup", description: "GPU-accelerated graph-based indexing", estimatedHours: 4, category: "Vector Database Setup" },
  { title: "Multi-tenant Data Isolation", description: "User-specific namespaces", estimatedHours: 3, category: "Vector Database Setup" },
  
  // Document Processing
  { title: "Docling Integration", description: "IBM document parser setup", estimatedHours: 4, category: "Document Processing" },
  { title: "PaddleOCR Setup", description: "OCR for scanned documents", estimatedHours: 4, category: "Document Processing" },
  { title: "File Type Handlers", description: "PDF, DOCX, XLSX, PPTX, EPUB", estimatedHours: 6, category: "Document Processing" },
  { title: "Metadata Extraction", description: "Author, date, sections", estimatedHours: 3, category: "Document Processing" },
  { title: "Document Summary Generation", description: "Auto-summarize uploads", estimatedHours: 3, category: "Document Processing" },
  { title: "Duplicate Detection", description: "Hash-based deduplication", estimatedHours: 2, category: "Document Processing" },
  
  // Memory Systems
  { title: "Long-term Conversation Memory", description: "Store chat history", estimatedHours: 4, category: "Memory Systems" },
  { title: "User Profile Memory", description: "Persistent preferences", estimatedHours: 3, category: "Memory Systems" },
  { title: "Episodic Memory System", description: "Event-based storage", estimatedHours: 4, category: "Memory Systems" },
  { title: "Memory Retrieval Logic", description: "Context-aware fetching", estimatedHours: 4, category: "Memory Systems" },
  { title: "Memory Expiry/Cleanup", description: "Aging out old data", estimatedHours: 3, category: "Memory Systems" },
  { title: "Memory Privacy Controls", description: "User data isolation", estimatedHours: 3, category: "Memory Systems" },
  
  // Agent Framework
  { title: "LangGraph Agent Orchestration", description: "Production-ready multi-agent workflows with LangGraph", estimatedHours: 7, category: "Agent Framework" },
  { title: "Agent State Management", description: "Workflow state tracking", estimatedHours: 4, category: "Agent Framework" },
  { title: "Tool Registry System", description: "Dynamic tool loading", estimatedHours: 3, category: "Agent Framework" },
  { title: "Chain-of-Thought Implementation", description: "ReAct pattern", estimatedHours: 4, category: "Agent Framework" },
  { title: "Agent Memory/Checkpointing", description: "State persistence", estimatedHours: 3, category: "Agent Framework" },
  { title: "Multi-Agent Coordination", description: "Agent-to-agent communication", estimatedHours: 5, category: "Agent Framework" },
  
  // Tool Implementation
  { title: "Python Code Sandbox", description: "Docker-based execution", estimatedHours: 6, category: "Tool Implementation" },
  { title: "API Calling Tool", description: "External API integration", estimatedHours: 4, category: "Tool Implementation" },
  { title: "File Management Tool", description: "Read/write user files", estimatedHours: 3, category: "Tool Implementation" },
  { title: "Web Fetch Tool", description: "URL content retrieval", estimatedHours: 3, category: "Tool Implementation" },
  { title: "Web Search Tool", description: "Optional search API integration", estimatedHours: 4, category: "Tool Implementation" },
  { title: "Tool Security Sandbox", description: "Resource limits, isolation", estimatedHours: 4, category: "Tool Implementation" },
  { title: "Tool Usage Analytics", description: "Track tool invocations", estimatedHours: 2, category: "Tool Implementation" },
  
  // Core UI Development
  { title: "Next.js 15 with React 19 and Turbopack", description: "Latest framework setup with Turbopack bundler", estimatedHours: 5, category: "Core UI Development" },
  { title: "Chat Interface", description: "Message threading, markdown", estimatedHours: 6, category: "Core UI Development" },
  { title: "Model Switcher UI", description: "Dynamic model selection", estimatedHours: 3, category: "Core UI Development" },
  { title: "File Upload Interface", description: "Drag-drop, progress", estimatedHours: 4, category: "Core UI Development" },
  { title: "Memory Management UI", description: "View/delete memories", estimatedHours: 4, category: "Core UI Development" },
  { title: "Tool Console UI", description: "Show agent actions", estimatedHours: 3, category: "Core UI Development" },
  { title: "Settings/Preferences UI", description: "User customization", estimatedHours: 3, category: "Core UI Development" },
  
  // Advanced UI Features
  { title: "Therapeutic Mode UI", description: "Separate interface/theme", estimatedHours: 4, category: "Advanced UI Features" },
  { title: "Admin Dashboard", description: "User management, metrics", estimatedHours: 6, category: "Advanced UI Features" },
  { title: "Mobile Responsive Design", description: "Touch-friendly UI", estimatedHours: 4, category: "Advanced UI Features" },
  { title: "Dark/Light Theme", description: "Theme switching", estimatedHours: 2, category: "Advanced UI Features" },
  { title: "Internationalization", description: "Multi-language support", estimatedHours: 3, category: "Advanced UI Features" },
  { title: "Accessibility Features", description: "Screen reader support", estimatedHours: 3, category: "Advanced UI Features" },
  
  // Therapeutic Mode Tasks
  { title: "Therapeutic Model Integration", description: "Safespace/Clarity with ADHD/autism specialization", estimatedHours: 5, category: "Therapeutic Mode" },
  { title: "Mode Switching Logic", description: "Context separation", estimatedHours: 3, category: "Therapeutic Mode" },
  { title: "Crisis Detection System", description: "Keyword monitoring", estimatedHours: 3, category: "Therapeutic Mode" },
  { title: "Neurodivergent-Optimized Prompting", description: "ADHD/autism-specific conversational patterns", estimatedHours: 5, category: "Therapeutic Mode" },
  { title: "Session Privacy Controls", description: "Encrypted storage", estimatedHours: 3, category: "Therapeutic Mode" },
  { title: "Consent Management", description: "Mode activation flow", estimatedHours: 2, category: "Therapeutic Mode" },
  { title: "Professional Help Resources", description: "Crisis resources", estimatedHours: 2, category: "Therapeutic Mode" },
  
  // Monitoring Stack
  { title: "Prometheus Configuration", description: "Metrics collection", estimatedHours: 4, category: "Monitoring Stack" },
  { title: "Grafana Dashboards", description: "System visualization", estimatedHours: 4, category: "Monitoring Stack" },
  { title: "Loki Log Aggregation", description: "Centralized logging", estimatedHours: 3, category: "Monitoring Stack" },
  { title: "Alert Rules Setup", description: "Critical issue alerts", estimatedHours: 3, category: "Monitoring Stack" },
  { title: "Custom Metrics", description: "AI-specific metrics", estimatedHours: 3, category: "Monitoring Stack" },
  { title: "Performance Dashboards", description: "GPU, latency tracking", estimatedHours: 3, category: "Monitoring Stack" },
  
  // Infrastructure
  { title: "Docker Compose GPU Configuration", description: "NVIDIA runtime and GPU resource allocation", estimatedHours: 4, category: "Infrastructure" },
  { title: "MinIO Object Storage Setup", description: "S3-compatible storage for documents and models", estimatedHours: 4, category: "Infrastructure" },
  { title: "Docker Network Security", description: "Container isolation", estimatedHours: 3, category: "Infrastructure" },
  { title: "Volume Backup Strategy", description: "Data persistence", estimatedHours: 3, category: "Infrastructure" },
  { title: "Health Check Scripts", description: "Service monitoring", estimatedHours: 2, category: "Infrastructure" },
  { title: "Auto-restart Policies", description: "Failure recovery", estimatedHours: 2, category: "Infrastructure" },
  { title: "Resource Limits", description: "CPU/Memory caps", estimatedHours: 2, category: "Infrastructure" },
  
  // Ingestion Systems
  { title: "URL Crawler Implementation", description: "Multi-page support", estimatedHours: 4, category: "Ingestion Systems" },
  { title: "Periodic URL Refresh", description: "Auto-update content", estimatedHours: 3, category: "Ingestion Systems" },
  { title: "Bulk Document Import", description: "Batch processing", estimatedHours: 3, category: "Ingestion Systems" },
  { title: "Progress Tracking", description: "Ingestion status", estimatedHours: 2, category: "Ingestion Systems" },
  { title: "Error Recovery", description: "Failed document handling", estimatedHours: 3, category: "Ingestion Systems" },
  
  // Search & Retrieval
  { title: "Hybrid Search", description: "Vector + keyword search", estimatedHours: 4, category: "Search & Retrieval" },
  { title: "OpenSearch Full-Text Integration", description: "Production-grade text search", estimatedHours: 5, category: "Search & Retrieval" },
  { title: "pgvector Optimization", description: "PostgreSQL vector search performance tuning", estimatedHours: 4, category: "Search & Retrieval" },
  { title: "Search Ranking Algorithm", description: "Relevance scoring", estimatedHours: 3, category: "Search & Retrieval" },
  { title: "Context Window Management", description: "Chunk selection", estimatedHours: 3, category: "Search & Retrieval" },
  { title: "Source Attribution", description: "Citation system", estimatedHours: 2, category: "Search & Retrieval" },
  
  // Testing Infrastructure
  { title: "Unit Test Suite", description: "Backend coverage", estimatedHours: 6, category: "Testing Infrastructure" },
  { title: "Integration Tests", description: "Service interactions", estimatedHours: 6, category: "Testing Infrastructure" },
  { title: "E2E Tests with Puppeteer", description: "UI workflows", estimatedHours: 5, category: "Testing Infrastructure" },
  { title: "Performance Tests", description: "Load testing", estimatedHours: 4, category: "Testing Infrastructure" },
  { title: "Security Tests", description: "Penetration testing", estimatedHours: 4, category: "Testing Infrastructure" },
  
  // Quality Assurance
  { title: "Code Linting Setup", description: "ESLint, Black, etc.", estimatedHours: 2, category: "Quality Assurance" },
  { title: "Type Checking", description: "TypeScript, mypy", estimatedHours: 2, category: "Quality Assurance" },
  { title: "API Documentation", description: "OpenAPI/Swagger", estimatedHours: 3, category: "Quality Assurance" },
  { title: "User Documentation", description: "Guides and tutorials", estimatedHours: 4, category: "Quality Assurance" },
  
  // Deployment & DevOps
  { title: "CI/CD Pipeline", description: "GitHub Actions setup", estimatedHours: 4, category: "Deployment & DevOps" },
  { title: "Environment Configuration", description: "Dev/staging/prod", estimatedHours: 3, category: "Deployment & DevOps" },
  { title: "SSL/TLS Setup", description: "HTTPS configuration", estimatedHours: 3, category: "Deployment & DevOps" },
  { title: "Backup Automation", description: "Scheduled backups", estimatedHours: 3, category: "Deployment & DevOps" },
  { title: "Disaster Recovery Plan", description: "Restore procedures", estimatedHours: 3, category: "Deployment & DevOps" },
  { title: "Deployment Scripts", description: "One-click deploy", estimatedHours: 3, category: "Deployment & DevOps" },
  
  // Integration Tasks
  { title: "MCP Server Integration", description: "Connect to existing MCP ecosystem", estimatedHours: 4, category: "Integration" },
  { title: "External API Connectors", description: "Third-party services", estimatedHours: 4, category: "Integration" },
  { title: "Webhook System", description: "Event notifications", estimatedHours: 3, category: "Integration" },
  { title: "Plugin Architecture", description: "Extensibility framework", estimatedHours: 5, category: "Integration" },
  
  // Advanced Features
  { title: "Redis LangCache Semantic Caching", description: "LLM response caching with semantic search", estimatedHours: 5, category: "Advanced Features" },
  { title: "Query Planning Optimizer", description: "Smart retrieval", estimatedHours: 4, category: "Advanced Features" },
  { title: "Model Fine-tuning Pipeline", description: "Custom training", estimatedHours: 6, category: "Advanced Features" },
  { title: "Federation Support", description: "Multi-instance sync", estimatedHours: 5, category: "Advanced Features" },
  { title: "Voice Integration Prep", description: "API structure for future", estimatedHours: 3, category: "Advanced Features" },
  { title: "Vision Model Prep", description: "Multimodal architecture", estimatedHours: 4, category: "Advanced Features" }
];

async function runMCPCommand(toolName, params) {
  const command = `npx @modelcontextprotocol/cli query --tool ${toolName} --params '${JSON.stringify(params)}'`;
  try {
    const result = execSync(command, { encoding: 'utf-8' });
    return JSON.parse(result);
  } catch (error) {
    console.error(`Error executing MCP command: ${error.message}`);
    throw error;
  }
}

async function getCurrentTasks() {
  console.log('Fetching current tasks for JarvisAI project...');
  try {
    const result = await runMCPCommand('get_project_tasks', { project_id: PROJECT_ID });
    return result.tasks || [];
  } catch (error) {
    console.error('Error fetching tasks:', error);
    return [];
  }
}

async function createTask(task) {
  console.log(`Creating task: ${task.title}`);
  try {
    const params = {
      project_id: PROJECT_ID,
      title: task.title,
      description: task.description,
      status: 'TODO',
      priority: 'MEDIUM',
      estimated_hours: task.estimatedHours,
      tags: [task.category]
    };
    
    const result = await runMCPCommand('create_task', params);
    console.log(`✅ Created: ${task.title}`);
    return result;
  } catch (error) {
    console.error(`❌ Failed to create task "${task.title}":`, error.message);
    return null;
  }
}

async function updateTask(taskId, updates) {
  console.log(`Updating task ID: ${taskId}`);
  try {
    const params = {
      task_id: taskId,
      ...updates
    };
    
    const result = await runMCPCommand('update_task', params);
    console.log(`✅ Updated task ID: ${taskId}`);
    return result;
  } catch (error) {
    console.error(`❌ Failed to update task ID ${taskId}:`, error.message);
    return null;
  }
}

async function deleteTask(taskId) {
  console.log(`Deleting task ID: ${taskId}`);
  try {
    const result = await runMCPCommand('delete_task', { task_id: taskId });
    console.log(`✅ Deleted task ID: ${taskId}`);
    return result;
  } catch (error) {
    console.error(`❌ Failed to delete task ID ${taskId}:`, error.message);
    return null;
  }
}

async function main() {
  console.log('Starting JarvisAI 2025 task update...\n');
  
  // Get current tasks
  const currentTasks = await getCurrentTasks();
  console.log(`Found ${currentTasks.length} existing tasks\n`);
  
  // Create a map of existing tasks by title for easy lookup
  const existingTasksMap = new Map();
  currentTasks.forEach(task => {
    existingTasksMap.set(task.title.toLowerCase(), task);
  });
  
  // Track what we need to do
  const tasksToUpdate = [];
  const tasksToCreate = [];
  const tasksToDelete = [];
  
  // Check each complete task
  for (const completeTask of COMPLETE_TASKS) {
    const existingTask = existingTasksMap.get(completeTask.title.toLowerCase());
    
    if (existingTask) {
      // Check if update is needed
      if (existingTask.description !== completeTask.description ||
          existingTask.estimated_hours !== completeTask.estimatedHours ||
          !existingTask.tags?.includes(completeTask.category)) {
        tasksToUpdate.push({
          id: existingTask.id,
          updates: {
            description: completeTask.description,
            estimated_hours: completeTask.estimatedHours,
            tags: [completeTask.category]
          }
        });
      }
      // Remove from map to track what's left
      existingTasksMap.delete(completeTask.title.toLowerCase());
    } else {
      // Task doesn't exist, need to create
      tasksToCreate.push(completeTask);
    }
  }
  
  // Any tasks left in the map are ones that exist but aren't in our complete list
  // These might be old tasks that need to be deleted
  for (const [title, task] of existingTasksMap) {
    // Check for specific replacements
    if (title.includes('qdrant') || title.includes('oauth2') || title.includes('oauth 2')) {
      tasksToDelete.push(task.id);
    }
  }
  
  // Execute updates
  console.log(`\n📊 Update Summary:`);
  console.log(`- Tasks to create: ${tasksToCreate.length}`);
  console.log(`- Tasks to update: ${tasksToUpdate.length}`);
  console.log(`- Tasks to delete: ${tasksToDelete.length}`);
  console.log(`\nTotal tasks after update: ${COMPLETE_TASKS.length}\n`);
  
  // Delete old tasks
  if (tasksToDelete.length > 0) {
    console.log('\n🗑️  Deleting obsolete tasks...');
    for (const taskId of tasksToDelete) {
      await deleteTask(taskId);
    }
  }
  
  // Update existing tasks
  if (tasksToUpdate.length > 0) {
    console.log('\n🔄 Updating existing tasks...');
    for (const { id, updates } of tasksToUpdate) {
      await updateTask(id, updates);
    }
  }
  
  // Create new tasks
  if (tasksToCreate.length > 0) {
    console.log('\n➕ Creating new tasks...');
    for (const task of tasksToCreate) {
      await createTask(task);
    }
  }
  
  console.log('\n✅ JarvisAI 2025 task update complete!');
  
  // Verify final count
  const finalTasks = await getCurrentTasks();
  console.log(`\n📈 Final task count: ${finalTasks.length} (Expected: ${COMPLETE_TASKS.length})`);
}

// Run the update
main().catch(console.error);