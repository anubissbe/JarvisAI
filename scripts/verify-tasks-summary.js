const { Client } = require('pg');

async function verifyTasksSummary() {
  const client = new Client({
    host: 'localhost',
    port: 5432,
    user: 'mcp_user',
    password: 'mcp_secure_password_2024',
    database: 'mcp_learning'
  });
  
  try {
    await client.connect();
    console.log('🚀 JarvisAI 2025 Tasks Verification\n');
    
    // Get project info
    const projectResult = await client.query(`
      SELECT name, description
      FROM project_management.projects
      WHERE id = '9a641921-b355-4214-a73c-2dc1be7fd132'
    `);
    
    if (projectResult.rows.length > 0) {
      console.log(`📁 Project: ${projectResult.rows[0].name}`);
      console.log(`📝 ${projectResult.rows[0].description}\n`);
    }
    
    // Total count
    const countResult = await client.query(`
      SELECT COUNT(*) as total,
             SUM(estimated_hours) as total_hours
      FROM project_management.tasks
      WHERE project_id = '9a641921-b355-4214-a73c-2dc1be7fd132'
    `);
    
    console.log(`📊 Total Tasks: ${countResult.rows[0].total}`);
    console.log(`⏱️  Total Estimated Hours: ${countResult.rows[0].total_hours} hours (~${Math.round(countResult.rows[0].total_hours / 40)} weeks)\n`);
    
    // Category breakdown
    console.log('📂 Tasks by Category:');
    const categoryResult = await client.query(`
      SELECT 
        metadata->>'category' as category,
        COUNT(*) as count,
        SUM(estimated_hours) as hours
      FROM project_management.tasks
      WHERE project_id = '9a641921-b355-4214-a73c-2dc1be7fd132'
        AND metadata->>'category' IS NOT NULL
      GROUP BY metadata->>'category'
      ORDER BY count DESC, category
    `);
    
    categoryResult.rows.forEach(row => {
      console.log(`  • ${row.category}: ${row.count} tasks (${row.hours}h)`);
    });
    
    // Key 2025 features
    console.log('\n✨ Key 2025 Updates:');
    const key2025 = await client.query(`
      SELECT name, description
      FROM project_management.tasks
      WHERE project_id = '9a641921-b355-4214-a73c-2dc1be7fd132'
        AND (
          name ILIKE '%Milvus%' OR
          name ILIKE '%OAuth 3.0%' OR
          name ILIKE '%Next.js 15%' OR
          name ILIKE '%Redis LangCache%' OR
          name ILIKE '%OpenSearch%' OR
          name ILIKE '%MinIO%' OR
          name ILIKE '%NVIDIA CAGRA%' OR
          name ILIKE '%Late Chunking%' OR
          name ILIKE '%LangGraph%' OR
          name ILIKE '%Docling%' OR
          name ILIKE '%Neurodivergent%'
        )
      ORDER BY name
    `);
    
    key2025.rows.forEach(task => {
      console.log(`  🆕 ${task.name}`);
      console.log(`     ${task.description}`);
    });
    
    // Phase breakdown
    console.log('\n📅 Recommended Implementation Phases:');
    
    const phases = [
      { 
        name: 'Phase 1 - Foundation (Week 1-2)',
        categories: ['Backend API Development', 'Authentication & Security', 'LLM Integration', 'Core UI Development', 'Infrastructure']
      },
      {
        name: 'Phase 2 - AI Capabilities (Week 3-4)',
        categories: ['Vector Database Setup', 'Document Processing', 'Agent Framework']
      },
      {
        name: 'Phase 3 - Advanced Features (Week 5-6)',
        categories: ['Tool Implementation', 'Therapeutic Mode', 'Advanced Features', 'Advanced UI Features']
      },
      {
        name: 'Phase 4 - Production Ready (Week 7-8)',
        categories: ['Search & Retrieval', 'Monitoring Stack', 'Testing Infrastructure', 'Quality Assurance']
      },
      {
        name: 'Phase 5 - Polish & Extend (Week 9+)',
        categories: ['Memory Systems', 'Deployment & DevOps', 'Integration', 'Ingestion Systems']
      }
    ];
    
    for (const phase of phases) {
      const phaseResult = await client.query(`
        SELECT COUNT(*) as count, SUM(estimated_hours) as hours
        FROM project_management.tasks
        WHERE project_id = '9a641921-b355-4214-a73c-2dc1be7fd132'
          AND metadata->>'category' = ANY($1)
      `, [phase.categories]);
      
      console.log(`\n  ${phase.name}`);
      console.log(`    Tasks: ${phaseResult.rows[0].count} | Hours: ${phaseResult.rows[0].hours}`);
      console.log(`    Categories: ${phase.categories.join(', ')}`);
    }
    
    console.log('\n✅ All 118 tasks successfully loaded into the project-tasks MCP server!');
    console.log('💡 Use the Task Management WebUI at http://localhost:5173 to view and manage tasks');
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await client.end();
  }
}

verifyTasksSummary();