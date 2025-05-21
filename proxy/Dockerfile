FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the proxy port
EXPOSE 11435

# Copy the URL fixer script
COPY fix_openwebui_url.py /app/fix_openwebui_url.py

# Create a simple run script that fixes the OpenWebUI URL before starting
RUN printf '#!/bin/sh\nset -euo pipefail\nexport PYTHONPATH=/opt/jarvis:$PYTHONPATH\npython /app/fix_openwebui_url.py\nexec python /app/ollama_proxy.py\n' > /usr/local/bin/run.sh \
    && chmod +x /usr/local/bin/run.sh

# Command to run the proxy with the fix applied
CMD ["/usr/local/bin/run.sh"]
