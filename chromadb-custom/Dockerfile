FROM ghcr.io/chroma-core/chroma:0.4.22

# Pin NumPy to a version before 2.0
RUN pip uninstall -y numpy && pip install numpy==1.24.3

# Create a custom config file to reduce logging
RUN echo '{\n  "uvicorn": {\n    "log_level": "warning"\n  }\n}' > /chroma/chroma_config.json

# Make sure the server starts properly with reduced logging for 404 errors
CMD ["uvicorn", "chromadb.app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"]