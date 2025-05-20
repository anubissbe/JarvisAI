FROM ollama/ollama:latest

# Create a wrapper script
RUN echo '#!/bin/bash' > /usr/local/bin/ollama-wrapper.sh && \
    echo 'if [[ "$@" == *"runner"* && "$@" == *"--n-gpu-layers 2"* ]]; then' >> /usr/local/bin/ollama-wrapper.sh && \
    echo '    # Replace n-gpu-layers 2 with n-gpu-layers 28' >> /usr/local/bin/ollama-wrapper.sh && \
    echo '    modified_args="${@/--n-gpu-layers 2/--n-gpu-layers 28}"' >> /usr/local/bin/ollama-wrapper.sh && \
    echo '    echo "Modified command: $modified_args" >&2' >> /usr/local/bin/ollama-wrapper.sh && \
    echo '    exec /usr/bin/ollama $modified_args' >> /usr/local/bin/ollama-wrapper.sh && \
    echo 'else' >> /usr/local/bin/ollama-wrapper.sh && \
    echo '    exec /usr/bin/ollama "$@"' >> /usr/local/bin/ollama-wrapper.sh && \
    echo 'fi' >> /usr/local/bin/ollama-wrapper.sh && \
    chmod +x /usr/local/bin/ollama-wrapper.sh

# Use the wrapper script as the entry point
ENTRYPOINT ["/usr/local/bin/ollama-wrapper.sh"]
