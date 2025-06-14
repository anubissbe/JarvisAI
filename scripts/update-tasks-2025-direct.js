#!/usr/bin/env node

const { Client } = require('pg');
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

async function main() {
  console.log('🚀 JarvisAI 2025 Task Update\n');
  
  // Install pg if needed
  try {
    require('pg');
  } catch (e) {
    console.log('Installing pg module...');
    require('child_process').execSync('npm install pg', { stdio: 'inherit' });
  }
  
  const client = new Client({
    host: 'localhost',
    port: 5432,
    user: 'mcp_user',
    password: 'mcp_secure_password_2024',
    database: 'mcp_learning'
  });
  
  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL\n');
    
    // Get current tasks
    console.log('📋 Fetching current tasks...');
    const currentTasksResult = await client.query(`
      SELECT id, name, description, status, priority, estimated_hours, metadata
      FROM project_management.tasks
      WHERE project_id = $1
      ORDER BY created_at
    `, [PROJECT_ID]);
    
    const currentTasks = currentTasksResult.rows;
    console.log(`Found ${currentTasks.length} existing tasks\n`);
    
    // Create maps for easy lookup
    const existingTasksMap = new Map();
    currentTasks.forEach(task => {
      existingTasksMap.set(task.name.toLowerCase(), task);
    });
    
    // Track operations
    const toDelete = [];
    const toUpdate = [];
    const toCreate = [];
    
    // Check each complete task
    for (const completeTask of COMPLETE_TASKS) {
      const existing = existingTasksMap.get(completeTask.title.toLowerCase());
      
      if (existing) {
        // Check if update needed
        const needsUpdate = 
          existing.description !== completeTask.description ||
          existing.estimated_hours !== completeTask.estimatedHours ||
          existing.metadata?.category !== completeTask.category;
          
        if (needsUpdate) {
          toUpdate.push({
            id: existing.id,
            name: completeTask.title,
            description: completeTask.description,
            estimated_hours: completeTask.estimatedHours,
            category: completeTask.category
          });
        }
        
        // Remove from map
        existingTasksMap.delete(completeTask.title.toLowerCase());
      } else {
        // Need to create
        toCreate.push(completeTask);
      }
    }
    
    // Check remaining tasks for deletion
    for (const [name, task] of existingTasksMap) {
      if (name.includes('qdrant') || 
          name.includes('oauth2') || 
          name.includes('oauth 2') ||
          (name.includes('next.js') && !name.includes('15'))) {
        toDelete.push(task);
      }
    }
    
    // Summary
    console.log('📊 Update Summary:');
    console.log(`  - Tasks to create: ${toCreate.length}`);
    console.log(`  - Tasks to update: ${toUpdate.length}`);
    console.log(`  - Tasks to delete: ${toDelete.length}`);
    console.log(`  - Total tasks after: ${COMPLETE_TASKS.length}\n`);
    
    // Execute deletions
    if (toDelete.length > 0) {
      console.log('🗑️  Deleting obsolete tasks...');
      for (const task of toDelete) {
        await client.query('DELETE FROM project_management.tasks WHERE id = $1', [task.id]);
        console.log(`  ✓ Deleted: ${task.name}`);
      }
      console.log('');
    }
    
    // Execute updates
    if (toUpdate.length > 0) {
      console.log('🔄 Updating existing tasks...');
      for (const task of toUpdate) {
        await client.query(`
          UPDATE project_management.tasks
          SET description = $2,
              estimated_hours = $3,
              metadata = jsonb_set(COALESCE(metadata, '{}'), '{category}', $4::jsonb),
              updated_at = NOW()
          WHERE id = $1
        `, [task.id, task.description, task.estimated_hours, JSON.stringify(task.category)]);
        console.log(`  ✓ Updated: ${task.name}`);
      }
      console.log('');
    }
    
    // Execute creations
    if (toCreate.length > 0) {
      console.log('➕ Creating new tasks...');
      for (const task of toCreate) {
        await client.query(`
          INSERT INTO project_management.tasks 
          (project_id, name, description, status, priority, estimated_hours, metadata)
          VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [PROJECT_ID, task.title, task.description, 'pending', 'medium', task.estimatedHours, JSON.stringify({ category: task.category })]);
        console.log(`  ✓ Created: ${task.title}`);
      }
      console.log('');
    }
    
    // Verify final count
    const finalResult = await client.query(`
      SELECT COUNT(*) as count
      FROM project_management.tasks
      WHERE project_id = $1
    `, [PROJECT_ID]);
    
    console.log(`✅ Update complete!`);
    console.log(`📈 Final task count: ${finalResult.rows[0].count} (Expected: ${COMPLETE_TASKS.length})`);
    
    // Show category summary
    const categoryResult = await client.query(`
      SELECT metadata->>'category' as category, COUNT(*) as count
      FROM project_management.tasks
      WHERE project_id = $1 AND metadata->>'category' IS NOT NULL
      GROUP BY metadata->>'category'
      ORDER BY count DESC
    `, [PROJECT_ID]);
    
    console.log('\n📊 Tasks by Category:');
    categoryResult.rows.forEach(row => {
      console.log(`  - ${row.category}: ${row.count} tasks`);
    });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main().catch(console.error);