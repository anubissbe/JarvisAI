# REMOTE SERVICES - CRITICAL INFORMATION

## 🚨 IMPORTANT: Task Management System Location

The task management system is **NOT LOCAL** - it runs on a REMOTE SERVER:

### Task Management Server Details:
- **Server IP**: 192.168.1.25
- **API URL**: http://192.168.1.25:3001/api
- **WebUI URL**: http://192.168.1.25:5173
- **Database**: PostgreSQL on 192.168.1.25:5432
- **Project ID**: 9a641921-b355-4214-a73c-2dc1be7fd132

### ⚠️ REMEMBER:
- The project-tasks MCP server is configured to use the REMOTE database
- DO NOT create tasks locally - they won't sync
- Always use the remote API endpoints for task operations
- The task count should be 118 tasks as of June 14, 2025

### Quick Commands:
```bash
# Check task count
curl -s http://192.168.1.25:3001/api/projects/9a641921-b355-4214-a73c-2dc1be7fd132/tasks | jq 'length'

# View tasks in browser
open http://192.168.1.25:5173

# Get all tasks
curl -s http://192.168.1.25:3001/api/projects/9a641921-b355-4214-a73c-2dc1be7fd132/tasks | jq '.'
```

### Other Remote Services:
- **Vault**: http://192.168.1.25:8200
- **Remote PostgreSQL**: 192.168.1.25:5432 (used by task manager)

## DO NOT FORGET: Task management is REMOTE, not local!