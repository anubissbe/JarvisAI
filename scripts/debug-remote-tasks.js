#!/usr/bin/env node

const axios = require('axios');

const REMOTE_API = 'http://192.168.1.25:3001/api';
const PROJECT_ID = '9a641921-b355-4214-a73c-2dc1be7fd132';

async function debugTasks() {
  try {
    const response = await axios.get(`${REMOTE_API}/projects/${PROJECT_ID}/tasks`);
    const tasks = response.data;
    
    console.log(`Total tasks: ${tasks.length}`);
    
    if (tasks.length > 0) {
      console.log('\nFirst task structure:');
      console.log(JSON.stringify(tasks[0], null, 2));
      
      console.log('\nTask titles containing OAuth, Milvus, or Redis:');
      tasks.forEach((task, index) => {
        if (task.title && (
          task.title.toLowerCase().includes('oauth') ||
          task.title.toLowerCase().includes('milvus') || 
          task.title.toLowerCase().includes('redis')
        )) {
          console.log(`${index}: ${task.title}`);
        }
      });
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

debugTasks();