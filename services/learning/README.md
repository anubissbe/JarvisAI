# JarvisAI Learning Service

This service implements the autonomous learning pipeline for JarvisAI, providing:

- Confidence analysis for responses
- Research engine for unknown topics
- Fact verification from multiple sources
- Knowledge integration

## API Endpoints

- `POST /learn/research` - Queue a research task
- `GET /learn/status/{task_id}` - Check research status
- `GET /learn/findings/{task_id}` - Get research findings
- `POST /learn/approve` - Approve findings for integration

## Components

- Research Scheduler
- Source Selection
- Information Gathering
- Fact Extraction
- Cross-Reference Validation
- Knowledge Integration

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload
```