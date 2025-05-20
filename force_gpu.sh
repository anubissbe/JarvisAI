#!/bin/bash

echo "Creating high-GPU model..."
curl -X POST http://localhost:11434/api/create -d '{
  "name": "jarvis-gpu28",
  "modelfile": "FROM jarvis:latest\nPARAMETER n_gpu_layers 28"
}'

echo -e "\n\nModel created. To use it, change the model in OpenWebUI settings to 'jarvis-gpu28'."
