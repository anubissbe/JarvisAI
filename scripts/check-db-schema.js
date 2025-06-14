const { Client } = require('pg');

async function checkSchema() {
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
    
    // Check if project_management schema exists
    const schemaResult = await client.query(`
      SELECT schema_name 
      FROM information_schema.schemata 
      WHERE schema_name = 'project_management'
    `);
    
    if (schemaResult.rows.length === 0) {
      console.log('❌ project_management schema does not exist!');
      return;
    }
    
    console.log('✅ project_management schema exists\n');
    
    // Get table columns
    const columnsResult = await client.query(`
      SELECT column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_schema = 'project_management' 
      AND table_name = 'tasks'
      ORDER BY ordinal_position
    `);
    
    console.log('Tasks table columns:');
    columnsResult.rows.forEach(col => {
      console.log(`  - ${col.column_name} (${col.data_type}) ${col.is_nullable === 'NO' ? 'NOT NULL' : ''}`);
    });
    
    // Check if JarvisAI project exists
    console.log('\nChecking for JarvisAI project...');
    const projectResult = await client.query(`
      SELECT id, name, description
      FROM project_management.projects
      WHERE id = '9a641921-b355-4214-a73c-2dc1be7fd132'
    `);
    
    if (projectResult.rows.length > 0) {
      console.log('✅ JarvisAI project found:');
      console.log(`  ID: ${projectResult.rows[0].id}`);
      console.log(`  Name: ${projectResult.rows[0].name}`);
    } else {
      console.log('❌ JarvisAI project not found!');
    }
    
    // Get sample tasks
    console.log('\nSample tasks:');
    const tasksResult = await client.query(`
      SELECT * FROM project_management.tasks 
      WHERE project_id = '9a641921-b355-4214-a73c-2dc1be7fd132'
      LIMIT 3
    `);
    
    console.log(`Found ${tasksResult.rowCount} tasks`);
    if (tasksResult.rows.length > 0) {
      console.log('\nFirst task structure:');
      console.log(JSON.stringify(tasksResult.rows[0], null, 2));
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await client.end();
  }
}

checkSchema();