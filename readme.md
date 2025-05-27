# JarvisAI-0.1: Self-Learning AI Assistant with Persistent Memory

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](docs/)

</div>

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Development](#development)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)
## Overview

JarvisAI-0.1 is a sophisticated self-learning AI assistant built on top of Open-WebUI that features autonomous learning capabilities, persistent memory across conversations, and the ability to research and acquire new knowledge independently. The system runs locally using Docker containers and integrates with various AI models through Ollama.

### Key Features

1. **Self-Learning Capability**
   - Automatically detects knowledge gaps
   - Conducts autonomous research
   - Verifies information from multiple sources
   - Integrates new knowledge after approval

2. **Dual Memory System**
   - Global knowledge base shared across users
   - User-specific private memories
   - Temporal memory promotion system
   - Sophisticated memory retrieval

3. **Interactive Features**
   - "Remember This" button for explicit memory storage
   - Memory visualization dashboard
   - Research approval workflow
   - Document upload and processing

4. **Plugin Ecosystem**
   - Weather integration
   - News aggregation with bias detection
   - Secure code execution sandbox
   - Extensible plugin architecture

## System Requirements

### Minimum Requirements
- CPU: 8 cores
- RAM: 32GB
- Storage: 1TB SSD
- GPU: NVIDIA GPU with 8GB VRAM

### Recommended Requirements
- CPU: 16+ cores
- RAM: 256GB
- Storage: 10TB NVMe SSD
- GPU: 2x NVIDIA V100/A100 GPUs

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Driver 525+
- NVIDIA Container Toolkit (for Linux deployment)
- Python 3.11+

## Quick Start

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/your-org/jarvisai-0.1
cd jarvisai-0.1
```

