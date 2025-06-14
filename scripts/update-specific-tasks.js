#!/usr/bin/env node

/**
 * Update specific tasks with research findings
 */

const axios = require('axios');

const REMOTE_API = 'http://192.168.1.25:3001/api';
const PROJECT_ID = '9a641921-b355-4214-a73c-2dc1be7fd132';

async function updateSpecificTasks() {
  try {
    console.log('🔄 Updating specific tasks with research findings...');
    
    // Get current tasks
    const response = await axios.get(`${REMOTE_API}/projects/${PROJECT_ID}/tasks`);
    const currentTasks = response.data;
    
    // Find and update OAuth task
    const oauthTask = currentTasks.find(task => 
      (task.name || '').toLowerCase().includes('oauth')
    );
    
    if (oauthTask) {
      console.log(`📝 Updating OAuth task: ${oauthTask.name}`);
      try {
        await axios.put(`${REMOTE_API}/tasks/${oauthTask.id}`, {
          ...oauthTask,
          name: oauthTask.name.replace('OAuth 3.0', 'OAuth 2.1'),
          description: `${oauthTask.description}\n\nUPDATE: Research shows OAuth 3.0 does not exist. OAuth 2.1 is the current standard with mandatory PKCE for all clients. Update implementation to use OAuth 2.1 with PKCE flow.`,
          priority: 'critical',
          updated_at: new Date().toISOString()
        });
        console.log('✅ OAuth task updated');
      } catch (error) {
        console.error('❌ Error updating OAuth task:', error.response?.data || error.message);
      }
    }
    
    // Find and update Milvus task
    const milvusTask = currentTasks.find(task => 
      (task.name || '').toLowerCase().includes('milvus')
    );
    
    if (milvusTask) {
      console.log(`📝 Updating Milvus task: ${milvusTask.name}`);
      try {
        await axios.put(`${REMOTE_API}/tasks/${milvusTask.id}`, {
          ...milvusTask,
          description: `${milvusTask.description}\n\nUPDATE: Research shows realistic performance improvement is 10-20x (not 50x). NVIDIA CAGRA provides significant but realistic performance gains for vector search operations.`,
          updated_at: new Date().toISOString()
        });
        console.log('✅ Milvus task updated');
      } catch (error) {
        console.error('❌ Error updating Milvus task:', error.response?.data || error.message);
      }
    }
    
    // Find and update Redis task
    const redisTask = currentTasks.find(task => 
      (task.name || '').toLowerCase().includes('redis') && 
      (task.name || '').toLowerCase().includes('cache')
    );
    
    if (redisTask) {
      console.log(`📝 Updating Redis task: ${redisTask.name}`);
      try {
        await axios.put(`${REMOTE_API}/tasks/${redisTask.id}`, {
          ...redisTask,
          description: `${redisTask.description}\n\nUPDATE: LangCache is currently in private preview. Start with open-source Redis semantic caching using langchain-redis, then migrate to LangCache when generally available.`,
          updated_at: new Date().toISOString()
        });
        console.log('✅ Redis task updated');
      } catch (error) {
        console.error('❌ Error updating Redis task:', error.response?.data || error.message);
      }
    }
    
    // Find and update chunking task
    const chunkingTask = currentTasks.find(task => 
      (task.name || '').toLowerCase().includes('chunking')
    );
    
    if (chunkingTask) {
      console.log(`📝 Updating chunking task: ${chunkingTask.name}`);
      try {
        await axios.put(`${REMOTE_API}/tasks/${chunkingTask.id}`, {
          ...chunkingTask,
          description: `${chunkingTask.description}\n\nUPDATE: Research confirms late chunking is best practice for 2025. Process entire document through transformer before chunking to preserve context across boundaries.`,
          priority: 'high',
          updated_at: new Date().toISOString()
        });
        console.log('✅ Chunking task updated');
      } catch (error) {
        console.error('❌ Error updating chunking task:', error.response?.data || error.message);
      }
    }
    
    console.log('✅ Specific task updates complete!');
    
  } catch (error) {
    console.error('❌ Failed to update tasks:', error.message);
    process.exit(1);
  }
}

// Run the update
updateSpecificTasks();