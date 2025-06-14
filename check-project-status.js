const { spawn } = require('child_process');
const fs = require('fs');

// Read claude.json to get project-tasks server config
const claudeConfig = JSON.parse(fs.readFileSync('/opt/projects/claude.json', 'utf8'));
const projectTasksConfig = claudeConfig.mcpServers['project-tasks'];

if (!projectTasksConfig) {
  console.error('project-tasks server not found in claude.json');
  process.exit(1);
}

// Prepare environment - IMPORTANT: Connect to REMOTE database
const env = { 
  ...process.env, 
  ...projectTasksConfig.env,
  POSTGRES_URL: 'postgresql://mcp_user:mcp_secure_password_2024@192.168.1.25:5432/mcp_learning'
};

// Spawn the MCP server
const server = spawn(projectTasksConfig.command, projectTasksConfig.args, { env });

let buffer = '';
let initialized = false;
let requestId = 1;

// Handle server output
server.stdout.on('data', (data) => {
  buffer += data.toString();
  
  // Process complete JSON-RPC messages
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (!line.trim()) continue;
    
    try {
      const message = JSON.parse(line);
      
      if (message.id === 1 && message.result) {
        // Initialization response
        console.log('✅ Connected to project-tasks MCP server');
        initialized = true;
        
        // Now query the project status
        queryProjectStatus();
      } else if (message.id === 2 && message.result) {
        // Project status response
        console.log('\n📊 JarvisAI Project Status:\n');
        const content = message.result.content[0].text;
        const projectData = JSON.parse(content);
        console.log(JSON.stringify(projectData, null, 2));
        
        // Query tasks for more details
        queryProjectTasks();
      } else if (message.id === 3 && message.result) {
        // Tasks response
        const content = message.result.content[0].text;
        const tasksData = JSON.parse(content);
        const tasks = tasksData.tasks;
        
        // Calculate statistics
        const stats = {
          total: tasks.length,
          completed: tasks.filter(t => t.status === 'completed').length,
          inProgress: tasks.filter(t => t.status === 'in_progress').length,
          pending: tasks.filter(t => t.status === 'pending').length,
          blocked: tasks.filter(t => t.status === 'blocked').length
        };
        
        const completionPercentage = ((stats.completed / stats.total) * 100).toFixed(1);
        
        console.log('\n📈 Task Statistics:\n');
        console.log(`Total Tasks: ${stats.total}`);
        console.log(`Completion: ${completionPercentage}%`);
        console.log(`\nBreakdown:`);
        console.log(`- Completed: ${stats.completed}`);
        console.log(`- In Progress: ${stats.inProgress}`);
        console.log(`- Pending: ${stats.pending}`);
        console.log(`- Blocked: ${stats.blocked}`);
        
        // Get phase breakdown
        const phaseBreakdown = {};
        tasks.forEach(task => {
          const phase = task.metadata?.phase || 'Unassigned';
          if (!phaseBreakdown[phase]) {
            phaseBreakdown[phase] = { total: 0, completed: 0 };
          }
          phaseBreakdown[phase].total++;
          if (task.status === 'completed') {
            phaseBreakdown[phase].completed++;
          }
        });
        
        console.log('\n🎯 Phase Breakdown:');
        Object.entries(phaseBreakdown).forEach(([phase, stats]) => {
          const phaseCompletion = ((stats.completed / stats.total) * 100).toFixed(1);
          console.log(`- ${phase}: ${stats.completed}/${stats.total} (${phaseCompletion}%)`);
        });
        
        // Exit cleanly
        server.kill();
        process.exit(0);
      } else if (message.error) {
        console.error('Error:', message.error);
        server.kill();
        process.exit(1);
      }
    } catch (e) {
      // Ignore parsing errors for incomplete messages
    }
  }
});

server.stderr.on('data', (data) => {
  console.error('Server error:', data.toString());
});

server.on('error', (err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

// Send initialization
console.log('🔌 Connecting to project-tasks MCP server...');
server.stdin.write(JSON.stringify({
  jsonrpc: "2.0",
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "jarvis-status-checker", version: "1.0.0" }
  },
  id: 1
}) + '\n');

function queryProjectStatus() {
  const request = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "get_project_status",
      arguments: {
        project_id: "9a641921-b355-4214-a73c-2dc1be7fd132"
      }
    },
    id: 2
  };
  
  server.stdin.write(JSON.stringify(request) + '\n');
}

function queryProjectTasks() {
  const request = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "list_project_tasks",
      arguments: {
        project_id: "9a641921-b355-4214-a73c-2dc1be7fd132"
      }
    },
    id: 3
  };
  
  server.stdin.write(JSON.stringify(request) + '\n');
}

// Timeout after 30 seconds
setTimeout(() => {
  console.error('\n⏱️ Timeout - no response from server');
  server.kill();
  process.exit(1);
}, 30000);