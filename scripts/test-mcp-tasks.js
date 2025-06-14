#!/usr/bin/env node

const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');
const { spawn } = require('child_process');
const path = require('path');

const PROJECT_ID = '9a641921-b355-4214-a73c-2dc1be7fd132';

async function testProjectTasks() {
  const serverPath = path.join('/opt/projects/mcp-servers/project-tasks/dist/index.js');
  
  console.log('Connecting to project-tasks MCP server...');
  
  const transport = new StdioClientTransport({
    command: 'node',
    args: [serverPath],
    env: {
      ...process.env,
      DB_PATH: '/opt/projects/databases/project_management.db'
    }
  });

  const client = new Client({
    name: 'test-client',
    version: '1.0.0'
  }, {
    capabilities: {}
  });

  try {
    await client.connect(transport);
    console.log('✅ Connected to project-tasks server\n');

    // Get current tasks
    console.log('Fetching current tasks for JarvisAI project...');
    const tasksResult = await client.callTool('get_project_tasks', {
      project_id: PROJECT_ID
    });
    
    console.log(`Found ${tasksResult.tasks.length} tasks\n`);
    
    // Group by category
    const categories = {};
    tasksResult.tasks.forEach(task => {
      const category = task.tags?.[0] || 'Uncategorized';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(task);
    });
    
    // Display summary
    console.log('Tasks by category:');
    Object.entries(categories).forEach(([category, tasks]) => {
      console.log(`\n${category}: ${tasks.length} tasks`);
      tasks.forEach(task => {
        console.log(`  - [${task.status}] ${task.title}`);
      });
    });
    
    // Check for outdated tasks
    console.log('\n\n🔍 Tasks that need updates:');
    const tasksToUpdate = [];
    const tasksToDelete = [];
    
    tasksResult.tasks.forEach(task => {
      const titleLower = task.title.toLowerCase();
      if (titleLower.includes('qdrant')) {
        console.log(`  - Replace Qdrant: "${task.title}" (ID: ${task.id})`);
        tasksToDelete.push(task);
      } else if (titleLower.includes('oauth2') || titleLower.includes('oauth 2')) {
        console.log(`  - Update OAuth: "${task.title}" (ID: ${task.id})`);
        tasksToUpdate.push({
          task,
          newTitle: task.title.replace(/OAuth\s*2\.?0?/i, 'OAuth 3.0'),
          newDescription: task.description?.replace(/OAuth\s*2\.?0?/i, 'OAuth 3.0') || ''
        });
      }
    });
    
    console.log(`\nTotal tasks to update: ${tasksToUpdate.length}`);
    console.log(`Total tasks to delete: ${tasksToDelete.length}`);
    
    await client.close();
    console.log('\n✅ Test completed successfully');
    
  } catch (error) {
    console.error('❌ Error:', error);
    await client.close();
    process.exit(1);
  }
}

testProjectTasks().catch(console.error);