# Copy the Modelfile to your container
docker cp Modelfile ollama:/tmp/Modelfile

# Execute commands inside the container
docker exec -it ollama bash

# Inside the container
cd /tmp
ollama create jarvis -f Modelfile
