FROM ollama/ollama:latest

# Create a patch script that will run when the container starts
RUN echo '#!/bin/bash' > /usr/local/bin/patch-gpu-layers.sh && \
    echo 'while true; do' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '  # Find ollama runner processes with --n-gpu-layers 2' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '  pids=$(ps aux | grep "ollama runner" | grep "n-gpu-layers 2" | grep -v grep | awk "{print \$2}")' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '  if [ -n "$pids" ]; then' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '    echo "Found ollama runner process with --n-gpu-layers 2"' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '    for pid in $pids; do' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '      echo "Killing process $pid to restart with --n-gpu-layers 28"' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '      kill $pid' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '    done' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '  fi' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo '  sleep 5' >> /usr/local/bin/patch-gpu-layers.sh && \
    echo 'done' >> /usr/local/bin/patch-gpu-layers.sh && \
    chmod +x /usr/local/bin/patch-gpu-layers.sh

# Override the CMD instead of ENTRYPOINT
CMD ["/bin/bash", "-c", "(/usr/local/bin/patch-gpu-layers.sh &) && ollama serve"]
