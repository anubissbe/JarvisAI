#!/bin/bash
# Quick script to check remote task status

echo "🔍 Checking Remote Task Manager Status..."
echo "========================================="
echo "Server: 192.168.1.25"
echo "Project: JarvisAI"
echo ""

# Check task count
TASK_COUNT=$(curl -s http://192.168.1.25:3001/api/projects/9a641921-b355-4214-a73c-2dc1be7fd132/tasks | jq 'length')
echo "📊 Total Tasks: $TASK_COUNT"

# Check API health
if curl -f -s http://192.168.1.25:3001/api/health > /dev/null; then
    echo "✅ API Status: Online"
else
    echo "❌ API Status: Offline"
fi

# Show WebUI URL
echo ""
echo "🌐 WebUI URL: http://192.168.1.25:5173"
echo ""
echo "💡 Remember: Always use the REMOTE task manager, not local!"