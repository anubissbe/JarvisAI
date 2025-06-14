#!/usr/bin/env python3

import json
import subprocess

PROJECT_ID = '9a641921-b355-4214-a73c-2dc1be7fd132'

def run_mcp_query(tool, params):
    """Run MCP CLI query command."""
    cmd = [
        'npx', '@modelcontextprotocol/cli', 'query',
        'mcp://project-tasks',
        '--tool', tool,
        '--params', json.dumps(params)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON: {result.stdout}")
        return None

# Get current tasks
print(f"Checking tasks for JarvisAI project (ID: {PROJECT_ID})")
print("-" * 60)

result = run_mcp_query('get_project_tasks', {'project_id': PROJECT_ID})

if result and 'tasks' in result:
    tasks = result['tasks']
    print(f"\nFound {len(tasks)} tasks:\n")
    
    # Group by category
    categories = {}
    for task in tasks:
        tags = task.get('tags', [])
        category = tags[0] if tags else 'Uncategorized'
        if category not in categories:
            categories[category] = []
        categories[category].append(task)
    
    # Display by category
    for category, cat_tasks in sorted(categories.items()):
        print(f"\n{category} ({len(cat_tasks)} tasks):")
        for task in cat_tasks:
            print(f"  - [{task['status']}] {task['title']} (ID: {task['id'][:8]}...)")
            if task.get('description'):
                print(f"    {task['description']}")
    
    # Check for tasks that need updates
    print("\n\nTasks that might need updates:")
    for task in tasks:
        title_lower = task['title'].lower()
        if 'qdrant' in title_lower:
            print(f"  - Replace Qdrant: {task['title']} (ID: {task['id']})")
        elif 'oauth2' in title_lower or 'oauth 2' in title_lower:
            print(f"  - Update OAuth: {task['title']} (ID: {task['id']})")
        elif 'next.js' in title_lower and '15' not in title_lower:
            print(f"  - Update Next.js: {task['title']} (ID: {task['id']})")
            
else:
    print("Failed to fetch tasks or no tasks found.")