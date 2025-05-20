FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the proxy port
EXPOSE 11435

# Command to run the proxy
CMD ["python", "ollama_proxy.py"]
# Copy the URL fixer script and run it at startup
COPY fix_openwebui_url.py /app/fix_openwebui_url.py
RUN sed -i 's/python ollama_proxy.py/python fix_openwebui_url.py \&\& python ollama_proxy.py/g' /usr/local/bin/run.sh
