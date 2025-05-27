# JarvisAI-0.1 API Documentation

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Memory Service API](#memory-service-api)
- [Learning Service API](#learning-service-api)
- [Document Service API](#document-service-api)
- [Plugin API](#plugin-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [WebSocket API](#websocket-api)

## Overview

The JarvisAI API is organized around REST. Our API accepts JSON-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes, authentication, and verbs.

### Base URLs

```
Memory Service:   http://memory-service:8000
Learning Service: http://learning-service:8000
Document Service: http://document-service:8000
```

### Response Format

All API responses follow this format:

```json
{
    "success": true,
    "data": {
        // Response data here
    },
    "error": null,
    "metadata": {
        "request_id": "req_123",
        "timestamp": "2023-11-08T12:34:56Z"
    }
}
```

## Authentication

### JWT Authentication

```http
Authorization: Bearer <token>
```

Example:
```python
import requests

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get("http://memory-service:8000/api/memory/search", headers=headers)
```

## Memory Service API

### Memory Operations

#### Store Memory

```http
POST /api/memory/store
```

Request:
```json
{
    "content": "User prefers dark mode",
    "category": "preference",
    "user_id": "user123",
    "importance": 0.8,
    "tags": ["ui", "preference"],
    "metadata": {
        "source": "explicit",
        "context": "settings discussion"
    }
}
```

Response:
```json
{
    "success": true,
    "data": {
        "memory_id": "mem_abc123",
        "stored_at": "2023-11-08T12:34:56Z",
        "vector_id": "vec_xyz789"
    }
}
```

#### Retrieve Memory

```http
GET /api/memory/retrieve/{memory_id}
```

Response:
```json
{
    "success": true,
    "data": {
        "memory_id": "mem_abc123",
        "content": "User prefers dark mode",
        "category": "preference",
        "user_id": "user123",
        "importance": 0.8,
        "created_at": "2023-11-08T12:34:56Z",
        "last_accessed": "2023-11-08T13:45:67Z",
        "access_count": 3
    }
}
```

#### Search Memories

```http
POST /api/memory/search
```

Request:
```json
{
    "query": "user preferences",
    "user_id": "user123",
    "limit": 10,
    "include_global": true,
    "min_confidence": 0.7,
    "categories": ["preference", "setting"]
}
```

Response:
```json
{
    "success": true,
    "data": {
        "matches": [
            {
                "memory_id": "mem_abc123",
                "content": "User prefers dark mode",
                "confidence": 0.92,
                "category": "preference"
            }
        ],
        "total": 1
    }
}
```

#### Update Memory

```http
PUT /api/memory/update/{memory_id}
```

Request:
```json
{
    "importance": 0.9,
    "metadata": {
        "verified": true
    }
}
```

#### Delete Memory

```http
DELETE /api/memory/delete/{memory_id}
```

### Memory Management

#### Promote Memory

```http
POST /api/memory/promote/{memory_id}
```

Request:
```json
{
    "target_layer": "permanent",
    "reason": "frequently_accessed"
}
```

#### Export Memories

```http
GET /api/memory/export
```

Query Parameters:
- `user_id`: User ID to export memories for
- `format`: Export format (json/csv)
- `categories`: Comma-separated list of categories

#### Import Memories

```http
POST /api/memory/import
```

Multipart form data with JSON/CSV file

## Learning Service API

### Research Operations

#### Queue Research Task

```http
POST /api/learn/research
```

Request:
```json
{
    "topic": "quantum computing",
    "priority": "high",
    "depth": "comprehensive",
    "sources": ["academic", "technical"],
    "deadline": "2023-11-09T00:00:00Z"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "task_id": "task_abc123",
        "estimated_completion": "2023-11-08T14:30:00Z",
        "status": "queued"
    }
}
```

#### Get Research Status

```http
GET /api/learn/status/{task_id}
```

Response:
```json
{
    "success": true,
    "data": {
        "task_id": "task_abc123",
        "status": "in_progress",
        "progress": 0.6,
        "findings_count": 12,
        "started_at": "2023-11-08T12:34:56Z",
        "estimated_completion": "2023-11-08T14:30:00Z"
    }
}
```

#### Get Research Findings

```http
GET /api/learn/findings/{task_id}
```

Response:
```json
{
    "success": true,
    "data": {
        "task_id": "task_abc123",
        "topic": "quantum computing",
        "findings": [
            {
                "fact": "Quantum computers use qubits instead of classical bits",
                "confidence": 0.95,
                "sources": [
                    "https://example.com/quantum-paper",
                    "https://arxiv.org/abs/..."
                ],
                "verification_status": "verified"
            }
        ],
        "summary": "...",
        "relationships": [
            {
                "source": "quantum computing",
                "relationship": "uses",
                "target": "qubits"
            }
        ]
    }
}
```

#### Approve Research

```http
POST /api/learn/approve/{task_id}
```

Request:
```json
{
    "approved_findings": ["finding_1", "finding_2"],
    "rejected_findings": ["finding_3"],
    "modifications": {
        "finding_4": {
            "content": "Modified content",
            "confidence": 0.85
        }
    }
}
```

### Knowledge Management

#### Verify Fact

```http
POST /api/learn/verify
```

Request:
```json
{
    "statement": "Quantum computers use qubits",
    "required_confidence": 0.9,
    "verification_sources": ["academic", "expert"]
}
```

#### Add Knowledge Relationship

```http
POST /api/learn/relationships
```

Request:
```json
{
    "source": "quantum computing",
    "relationship": "uses",
    "target": "qubits",
    "confidence": 0.95
}
```

## Document Service API

### Document Operations

#### Upload Document

```http
POST /api/documents/upload
```

Multipart form data with file and metadata:
```json
{
    "category": "technical",
    "tags": ["quantum", "computing"],
    "priority": "high"
}
```

#### Process Document

```http
POST /api/documents/process/{document_id}
```

Request:
```json
{
    "extraction_settings": {
        "extract_code": true,
        "extract_tables": true,
        "extract_images": false
    },
    "language": "en",
    "max_chunks": 100
}
```

#### Get Document Status

```http
GET /api/documents/status/{document_id}
```

#### Get Document Content

```http
GET /api/documents/content/{document_id}
```

#### Search Documents

```http
POST /api/documents/search
```

Request:
```json
{
    "query": "quantum computing examples",
    "file_types": ["pdf", "md"],
    "categories": ["technical"],
    "date_range": {
        "start": "2023-01-01",
        "end": "2023-12-31"
    }
}
```

## Plugin API

### Plugin Management

#### Register Plugin

```http
POST /api/plugins/register
```

Request:
```json
{
    "name": "weather",
    "version": "1.0.0",
    "description": "Weather information plugin",
    "entry_point": "weather.py",
    "requirements": ["requests>=2.28.0"],
    "permissions": ["network", "location"]
}
```

#### Get Plugin Status

```http
GET /api/plugins/status/{plugin_name}
```

#### Update Plugin

```http
PUT /api/plugins/update/{plugin_name}
```

#### Delete Plugin

```http
DELETE /api/plugins/delete/{plugin_name}
```

## Error Handling

### Error Response Format

```json
{
    "success": false,
    "data": null,
    "error": {
        "code": "memory_not_found",
        "message": "Memory with ID mem_123 not found",
        "details": {
            "memory_id": "mem_123"
        }
    }
}
```

### Common Error Codes

- `authentication_error`: Invalid or missing authentication
- `permission_denied`: Insufficient permissions
- `resource_not_found`: Requested resource not found
- `validation_error`: Invalid request parameters
- `rate_limit_exceeded`: Too many requests
- `internal_error`: Internal server error

## Rate Limiting

Rate limits are applied per API key and endpoint:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1636383600
```

When rate limit is exceeded:
```json
{
    "success": false,
    "error": {
        "code": "rate_limit_exceeded",
        "message": "Rate limit exceeded. Please try again in 60 seconds",
        "details": {
            "reset_at": "2023-11-08T13:00:00Z"
        }
    }
}
```

## WebSocket API

### Memory Updates Stream

```javascript
const ws = new WebSocket('ws://memory-service:8000/ws/memory/updates');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log('Memory update:', update);
};
```

### Research Progress Stream

```javascript
const ws = new WebSocket('ws://learning-service:8000/ws/research/progress');

ws.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    console.log('Research progress:', progress);
};
```