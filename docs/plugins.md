# JarvisAI Plugin Development Guide

## Table of Contents

- [Overview](#overview)
- [Plugin Architecture](#plugin-architecture)
- [Creating a Plugin](#creating-a-plugin)
- [Plugin Types](#plugin-types)
- [Security Guidelines](#security-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Publishing Guidelines](#publishing-guidelines)
- [Examples](#examples)

## Overview

JarvisAI plugins extend the core functionality by adding new capabilities such as API integrations, data processing, or UI components. This guide explains how to create, test, and publish plugins for JarvisAI.

### Key Concepts

- **Plugin Types**: Tools, Functions, Actions, Pipelines
- **Sandboxing**: All plugins run in isolated containers
- **Permissions**: Fine-grained access control
- **Version Management**: Semantic versioning support
- **Resource Limits**: CPU, memory, and network restrictions

## Plugin Architecture

### Directory Structure

```
plugins/
├── weather/                    # Plugin root directory
│   ├── __init__.py            # Plugin initialization
│   ├── main.py                # Main plugin logic
│   ├── config.py              # Configuration
│   ├── requirements.txt       # Dependencies
│   ├── README.md             # Documentation
│   ├── tests/                # Test files
│   │   ├── __init__.py
│   │   ├── test_main.py
│   │   └── test_utils.py
│   └── ui/                   # UI components (if any)
│       ├── components/
│       └── styles/
```

### Plugin Manifest

```yaml
name: weather
version: 1.0.0
description: Weather information plugin
author: Your Name
license: MIT
requires:
  python: ">=3.11"
  jarvisai: ">=0.1.0"
dependencies:
  - requests>=2.28.0
  - pydantic>=2.4.2
permissions:
  - network
  - location
config:
  required:
    - api_key
  optional:
    - units: metric
resources:
  memory: 512M
  cpu: 0.5
```

## Creating a Plugin

### 1. Plugin Base Class

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class PluginBase(ABC):
    """Base class for all JarvisAI plugins."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize plugin resources."""
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin functionality."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
```

### 2. Plugin Implementation

```python
from jarvisai.plugins import PluginBase
from pydantic import BaseModel
import httpx

class WeatherConfig(BaseModel):
    """Weather plugin configuration."""
    api_key: str
    units: str = "metric"
    language: str = "en"

class WeatherPlugin(PluginBase):
    """Weather information plugin."""
    
    def __init__(self, config: WeatherConfig):
        self.config = config
        self.client = None
    
    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather information."""
        location = params.get("location")
        if not location:
            raise ValueError("Location is required")
            
        url = f"https://api.weather.com/v1/weather"
        response = await self.client.get(
            url,
            params={
                "location": location,
                "units": self.config.units,
                "language": self.config.language,
                "apikey": self.config.api_key
            }
        )
        
        return response.json()
    
    async def cleanup(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
```

### 3. UI Components (Optional)

```typescript
// ui/components/WeatherWidget.tsx
import React from 'react';
import { useWeather } from '../hooks/useWeather';

export const WeatherWidget: React.FC = () => {
    const { data, loading, error } = useWeather();
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    
    return (
        <div className="weather-widget">
            <h3>{data.location}</h3>
            <div className="temperature">{data.temperature}°C</div>
            <div className="conditions">{data.conditions}</div>
        </div>
    );
};
```

## Plugin Types

### 1. Tool Plugins

Tools integrate external APIs or services:

```python
class ToolPlugin(PluginBase):
    """Base class for tool plugins."""
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate API credentials."""
        pass
```

Example: Weather, News APIs

### 2. Function Plugins

Functions process data or perform calculations:

```python
class FunctionPlugin(PluginBase):
    """Base class for function plugins."""
    
    @abstractmethod
    async def validate_input(self, data: Any) -> bool:
        """Validate input data."""
        pass
```

Example: Data analysis, format conversion

### 3. Action Plugins

Actions modify the UI or trigger system events:

```python
class ActionPlugin(PluginBase):
    """Base class for action plugins."""
    
    @abstractmethod
    async def validate_permissions(self) -> bool:
        """Validate required permissions."""
        pass
```

Example: UI customization, notifications

### 4. Pipeline Plugins

Pipelines combine multiple plugins into workflows:

```python
class PipelinePlugin(PluginBase):
    """Base class for pipeline plugins."""
    
    @abstractmethod
    async def validate_dependencies(self) -> bool:
        """Validate plugin dependencies."""
        pass
```

Example: Complex data processing workflows

## Security Guidelines

### 1. Input Validation

Always validate user input:

```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    location: str
    
    @validator("location")
    def validate_location(cls, v):
        if len(v) < 2:
            raise ValueError("Location too short")
        return v.strip()
```

### 2. Resource Limits

Implement resource monitoring:

```python
import resource
import psutil

def check_resources():
    memory = psutil.Process().memory_info().rss
    if memory > MAX_MEMORY:
        raise ResourceError("Memory limit exceeded")
```

### 3. Error Handling

Implement proper error handling:

```python
class PluginError(Exception):
    """Base class for plugin errors."""
    pass

class APIError(PluginError):
    """API-related errors."""
    pass

class ResourceError(PluginError):
    """Resource limit errors."""
    pass
```

## Testing Guidelines

### 1. Unit Tests

```python
import pytest
from your_plugin import YourPlugin

@pytest.fixture
async def plugin():
    plugin = YourPlugin(config)
    await plugin.initialize()
    yield plugin
    await plugin.cleanup()

async def test_plugin_execute(plugin):
    result = await plugin.execute({"param": "value"})
    assert result["status"] == "success"
```

### 2. Integration Tests

```python
async def test_plugin_integration(plugin, memory_service):
    # Test plugin with actual services
    result = await plugin.execute({"query": "test"})
    assert await memory_service.verify(result)
```

### 3. Performance Tests

```python
import asyncio
import time

async def test_plugin_performance(plugin):
    start = time.time()
    tasks = [plugin.execute({"test": i}) for i in range(100)]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    assert duration < 5.0  # Should complete in under 5 seconds
```

## Publishing Guidelines

### 1. Documentation Requirements

- README.md with:
  - Description
  - Installation
  - Configuration
  - Usage examples
  - API reference

### 2. Version Management

Follow semantic versioning:

```python
__version__ = "1.0.0"  # Major.Minor.Patch
```

### 3. Publishing Process

1. Test thoroughly
2. Update documentation
3. Update version
4. Create release
5. Submit to plugin registry

## Examples

### Weather Plugin

```python
# plugins/weather/main.py
from jarvisai.plugins import ToolPlugin
from pydantic import BaseModel
import httpx

class WeatherPlugin(ToolPlugin):
    """Get weather information."""
    
    name = "weather"
    version = "1.0.0"
    
    async def execute(self, params: dict) -> dict:
        """Get weather for location."""
        location = params["location"]
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.weather.com/v1/current",
                params={"q": location, "appid": self.config.api_key}
            )
            return response.json()
```

### News Plugin

```python
# plugins/news/main.py
from jarvisai.plugins import ToolPlugin
import newsapi

class NewsPlugin(ToolPlugin):
    """Get news articles."""
    
    name = "news"
    version = "1.0.0"
    
    async def execute(self, params: dict) -> dict:
        """Get news articles."""
        client = newsapi.NewsApiClient(api_key=self.config.api_key)
        return client.get_top_headlines(
            q=params.get("query"),
            country=params.get("country", "us")
        )
```

### Code Execution Plugin

```python
# plugins/sandbox/main.py
from jarvisai.plugins import FunctionPlugin
import docker

class CodeSandboxPlugin(FunctionPlugin):
    """Execute code in sandbox."""
    
    name = "code_sandbox"
    version = "1.0.0"
    
    async def execute(self, params: dict) -> dict:
        """Execute code safely."""
        client = docker.from_env()
        container = client.containers.run(
            "python:3.11-slim",
            params["code"],
            remove=True,
            mem_limit="512m",
            network_mode="none"
        )
        return {"output": container.decode()}
```