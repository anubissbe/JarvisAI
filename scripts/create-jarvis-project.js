const { Client } = require('pg');

async function createJarvisProject() {
  const client = new Client({
    host: 'localhost',
    port: 5432,
    user: 'mcp_user',
    password: 'mcp_secure_password_2024',
    database: 'mcp_learning'
  });
  
  try {
    await client.connect();
    console.log('Connected to database\n');
    
    // Check if project exists
    const checkResult = await client.query(`
      SELECT id, name FROM project_management.projects
      WHERE id = '9a641921-b355-4214-a73c-2dc1be7fd132'
    `);
    
    if (checkResult.rows.length > 0) {
      console.log('✅ JarvisAI project already exists');
      return;
    }
    
    // Create the project
    console.log('Creating JarvisAI project...');
    await client.query(`
      INSERT INTO project_management.projects (id, name, description, requirements, created_at, updated_at)
      VALUES (
        '9a641921-b355-4214-a73c-2dc1be7fd132',
        'JarvisAI - Advanced AI Assistant System',
        'A comprehensive, privacy-focused AI assistant leveraging dual GPU acceleration for advanced capabilities including document processing, therapeutic support, and multi-agent orchestration.',
        'Dual GPU system, 128GB RAM, multiple LLMs, vector databases with GPU acceleration, therapeutic mode with ADHD/autism specialization, production-ready infrastructure',
        NOW(),
        NOW()
      )
    `);
    
    console.log('✅ JarvisAI project created successfully!');
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await client.end();
  }
}

createJarvisProject();