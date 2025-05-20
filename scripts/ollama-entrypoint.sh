#!/bin/bash
set -e

# Force use of both GPUs with tensor parallelism
export CUDA_VISIBLE_DEVICES=0,1

# Enable higher GPU layers and parallel execution
export OLLAMA_GPU_LAYERS=32
export OLLAMA_PARALLEL=2

# Wait for any previous Ollama instances to fully terminate
pkill -9 ollama || true
sleep 2

# Start Ollama with monitoring
echo "Starting Ollama with optimized multi-GPU settings..."
ollama serve &
OLLAMA_PID=$!

# Function to monitor running models and ensure they use both GPUs
monitor_and_optimize() {
  while true; do
    # Find any ollama runner processes
    runner_pids=$(ps aux | grep 'ollama runner' | grep -v grep | awk '{print $2}')
    
    if [ -n "$runner_pids" ]; then
      for pid in $runner_pids; do
        cmd=$(ps -o cmd= $pid 2>/dev/null || echo "")
        
        # Check if this process is using the right GPU configuration
        if [[ "$cmd" == *"n-gpu-layers 2"* || "$cmd" != *"parallel 2"* ]]; then
          echo "[$(date)] Found runner process with suboptimal GPU settings: $pid"
          echo "[$(date)] Command: $cmd"
          echo "[$(date)] Terminating to restart with optimal settings"
          kill $pid
        fi
      done
    fi
    
    # Check Ollama main process
    if ! kill -0 $OLLAMA_PID 2>/dev/null; then
      echo "[$(date)] Main Ollama process died, restarting..."
      ollama serve &
      OLLAMA_PID=$!
    fi
    
    # Clean up unused models every 30 minutes for lazy loading
    current_min=$(date +%M)
    if [ $((current_min % 30)) -eq 0 ]; then
      echo "[$(date)] Performing maintenance - cleaning unused models"
      pkill -SIGUSR1 ollama || true
    fi
    
    sleep 5
  done
}

# Start monitoring in background
monitor_and_optimize &

# Keep script running
wait $OLLAMA_PID
