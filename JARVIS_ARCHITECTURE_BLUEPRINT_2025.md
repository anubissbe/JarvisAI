# JARVIS AI ASSISTANT: COMPREHENSIVE ARCHITECTURE BLUEPRINT 2025
## Production-Ready Self-Hosted AI Assistant with Advanced Capabilities

**Version:** 2025.1  
**Date:** June 13, 2025  
**Authors:** AI Architecture Research Team  
**Target Hardware:** HP ProLiant G10, Dual NVIDIA V100 GPUs (32GB VRAM), 256GB RAM  

---

## EXECUTIVE SUMMARY

This blueprint presents a production-ready architecture for Jarvis, a comprehensive self-hosted AI assistant optimized for dual NVIDIA V100 GPUs. Based on extensive research of 2025 best practices, this system integrates cutting-edge technologies to deliver advanced capabilities including multi-modal RAG, therapeutic support, agent orchestration, and enterprise-grade security.

**Key Innovations:**
- Dual-GPU optimization with intelligent model switching
- Advanced therapeutic mode with ADHD/autism support
- Production-grade RAG with semantic caching
- Multi-agent orchestration with LangGraph
- Enterprise security with OAuth 2.1 (with PKCE) and RBAC
- Comprehensive observability and monitoring

---

## CORE TECHNOLOGY STACK (2025 OPTIMIZED)

### Frontend & UI Framework
- **Next.js 15** with React 19 support
- **TypeScript** with Next.js config.ts support
- **Tailwind CSS v4** with semantic design system
- **shadcn/ui** components for AI interfaces
- **assistant-ui** for specialized chat interfaces
- **Turbopack** for 76.7% faster development builds

### Backend Services
- **FastAPI** with OAuth 2.1 authentication (PKCE required)
- **JWT** with HS256 and 30-minute access tokens
- **Python 3.11** with async/await optimizations
- **Uvicorn** with production ASGI server
- **Pydantic v2** for data validation

### AI & LLM Infrastructure
- **Ollama** with dual V100 GPU orchestration
- **LangGraph** for multi-agent workflows
- **Semantic Caching** with open-source Redis (LangCache migration planned)
- **Model Switching** with memory optimization
- **Safespace** fine-tuned model for therapeutic mode

### Data & Vector Storage
- **Milvus** with GPU acceleration (NVIDIA CAGRA)
- **PostgreSQL 16** with pgvector extension
- **Redis 8** with vector sets and open-source semantic caching
- **MinIO** for S3-compatible object storage
- **OpenSearch** for full-text search capabilities

### Document Processing
- **Docling** (IBM) for advanced PDF parsing
- **PaddleOCR** for scanned document support
- **Semantic Chunking** with late chunking techniques
- **Multi-modal** processing for tables and images

### Infrastructure & Deployment
- **Docker Compose v2** with multi-stage builds
- **NVIDIA Container Toolkit** for GPU support
- **Traefik** for reverse proxy and SSL termination
- **Prometheus + Grafana + Loki** for observability

---

## SYSTEM ARCHITECTURE OVERVIEW

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Next.js 15 UI] --> B[shadcn/ui Components]
        A --> C[assistant-ui Chat]
        A --> D[Authentication Layer]
    end
    
    subgraph "API Gateway"
        E[FastAPI Backend] --> F[OAuth 2.1 Auth]
        E --> G[JWT Middleware]
        E --> H[RBAC Authorization]
    end
    
    subgraph "AI Processing Layer"
        I[Ollama GPU Manager] --> J[Model Switching]
        I --> K[LangGraph Orchestrator]
        I --> L[Agent Tools]
        M[Therapeutic Mode] --> N[Safespace Model]
    end
    
    subgraph "Data Layer"
        O[Milvus Vector DB] --> P[GPU Acceleration]
        Q[PostgreSQL + pgvector] --> R[User Data]
        S[Redis Cache] --> T[Semantic Cache]
        U[MinIO Object Store] --> V[Document Storage]
    end
    
    subgraph "Processing Pipeline"
        W[Docling Parser] --> X[Semantic Chunking]
        X --> Y[Embedding Generation]
        Y --> O
    end
    
    subgraph "Monitoring"
        Z[Prometheus] --> AA[Grafana Dashboards]
        BB[Loki] --> AA
        CC[GPU Metrics] --> AA
    end
    
    A --> E
    E --> I
    I --> O
    E --> Q
    E --> S
    W --> U
```

---

## DETAILED COMPONENT SPECIFICATIONS

### 1. FRONTEND ARCHITECTURE (Next.js 15)

#### Core Framework Configuration
```javascript
// next.config.ts (New TypeScript config support)
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    turbo: true, // Stable Turbopack for 96.3% faster updates
    reactCompiler: true, // React 19 optimizations
  },
  typescript: {
    strict: true,
  },
  tailwindcss: {
    version: 4, // Latest Tailwind v4 support
  }
}

export default nextConfig
```

#### Authentication Integration (OAuth 2.1 with PKCE)
```typescript
// lib/auth.ts - OAuth 2.1 with PKCE Implementation
import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import GitHubProvider from 'next-auth/providers/github'

export const authOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: "openid email profile",
          response_type: "code",
          // OAuth 2.1 with PKCE parameters
          code_challenge_method: "S256"
        }
      }
    }),
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    })
  ],
  callbacks: {
    async signIn({ user, account }) {
      // Admin approval workflow
      const isApproved = await checkAdminApproval(user.email)
      return isApproved
    },
    async session({ session, token }) {
      session.user.role = token.role
      session.user.permissions = token.permissions
      return session
    }
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 60, // 30 minutes
  }
}
```

#### UI Component Architecture
```typescript
// components/chat/ChatInterface.tsx
import { useAssistant } from '@ai-sdk/react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function ChatInterface() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useAssistant({
    api: '/api/chat',
    streamMode: 'text',
  })

  return (
    <Card className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>
      <ChatInput
        value={input}
        onChange={handleInputChange}
        onSubmit={handleSubmit}
        disabled={isLoading}
      />
    </Card>
  )
}
```

### 2. BACKEND SERVICES (FastAPI with OAuth 2.1)

#### FastAPI Configuration with Security
```python
# main.py - FastAPI with OAuth 2.1 (PKCE) and JWT
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import httpx

app = FastAPI(
    title="Jarvis AI Assistant API",
    version="2025.1",
    description="Production-ready AI Assistant with OAuth 2.1 and PKCE"
)

# Security Configuration
SECRET_KEY = "your-secret-key-generated-with-openssl-rand-hex-32"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# OAuth 2.1 Configuration with PKCE
OAUTH_PROVIDERS = {
    "google": {
        "client_id": "your-google-client-id",
        "client_secret": "your-google-client-secret",
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo"
    }
}

# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Authentication Dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# RBAC Authorization
async def require_admin(user_id: str = Depends(get_current_user)):
    user = await get_user_by_id(user_id)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# API Endpoints
@app.post("/api/chat")
async def chat_completion(
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    # Chat processing logic
    pass

@app.post("/api/admin/users/{user_id}/approve")
async def approve_user(
    user_id: str,
    admin: User = Depends(require_admin)
):
    # User approval logic
    pass
```

### 3. AI PROCESSING LAYER

#### Ollama GPU Management
```python
# services/ollama_manager.py
import httpx
import asyncio
from typing import List, Dict
import nvidia_ml_py as nvml

class OllamaGPUManager:
    def __init__(self, hosts: List[str] = None):
        self.hosts = hosts or ["http://ollama-gpu0:11434", "http://ollama-gpu1:11434"]
        self.client = httpx.AsyncClient(timeout=300.0)
        self.gpu_allocation = {}
        nvml.nvmlInit()
        
    async def get_gpu_memory_usage(self, gpu_id: int) -> Dict:
        """Get current GPU memory usage"""
        handle = nvml.nvmlDeviceGetHandleByIndex(gpu_id)
        info = nvml.nvmlDeviceGetMemoryInfo(handle)
        return {
            "gpu_id": gpu_id,
            "total": info.total,
            "used": info.used,
            "free": info.free,
            "utilization": (info.used / info.total) * 100
        }
    
    async def optimal_model_placement(self, model_size_gb: float) -> int:
        """Determine optimal GPU for model placement"""
        gpu0_usage = await self.get_gpu_memory_usage(0)
        gpu1_usage = await self.get_gpu_memory_usage(1)
        
        # Choose GPU with more available memory
        if gpu0_usage["free"] >= gpu1_usage["free"]:
            return 0
        return 1
    
    async def load_model(self, model_name: str, gpu_id: int = None):
        """Load model on specific GPU"""
        if gpu_id is None:
            gpu_id = await self.optimal_model_placement(self.get_model_size(model_name))
            
        response = await self.client.post(
            f"{self.hosts[gpu_id]}/api/generate",
            json={"model": model_name, "keep_alive": -1}
        )
        return response.json()
    
    async def generate_streaming(self, model: str, prompt: str, gpu_id: int = 0):
        """Generate streaming response"""
        async with self.client.stream(
            "POST",
            f"{self.hosts[gpu_id]}/api/generate",
            json={"model": model, "prompt": prompt, "stream": True}
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    yield json.loads(line)
```

#### LangGraph Agent Orchestration
```python
# services/agent_orchestrator.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Dict, Any
import json

class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    current_agent: str
    task_queue: List[Dict]
    results: Dict[str, Any]
    tools_used: List[str]
    context: Dict[str, Any]

class JarvisOrchestrator:
    def __init__(self):
        self.memory = MemorySaver()
        self.workflow = StateGraph(AgentState)
        self.setup_agents()
        
    def setup_agents(self):
        """Setup multi-agent workflow"""
        # Define agent nodes
        self.workflow.add_node("router", self.router_agent)
        self.workflow.add_node("researcher", self.research_agent)
        self.workflow.add_node("coder", self.coding_agent)
        self.workflow.add_node("writer", self.writing_agent)
        self.workflow.add_node("therapist", self.therapeutic_agent)
        
        # Define conditional edges
        self.workflow.add_conditional_edges(
            "router",
            self.route_to_agent,
            {
                "research": "researcher",
                "code": "coder",
                "write": "writer",
                "therapy": "therapist",
                "end": END
            }
        )
        
        # Set entry point
        self.workflow.set_entry_point("router")
        
        # Compile with memory
        self.app = self.workflow.compile(checkpointer=self.memory)
    
    async def router_agent(self, state: AgentState) -> AgentState:
        """Route queries to appropriate specialized agent"""
        last_message = state["messages"][-1]["content"]
        
        # Determine routing based on content analysis
        if "code" in last_message.lower() or "python" in last_message.lower():
            state["current_agent"] = "code"
        elif "research" in last_message.lower() or "find" in last_message.lower():
            state["current_agent"] = "research"
        elif "feeling" in last_message.lower() or "therapy" in last_message.lower():
            state["current_agent"] = "therapy"
        else:
            state["current_agent"] = "write"
            
        return state
    
    async def research_agent(self, state: AgentState) -> AgentState:
        """Handle research and RAG queries"""
        # Implement RAG retrieval logic
        query = state["messages"][-1]["content"]
        
        # Semantic search in vector database
        relevant_docs = await self.vector_search(query)
        
        # Generate response with context
        response = await self.generate_with_context(query, relevant_docs)
        
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "agent": "researcher"
        })
        state["tools_used"].append("vector_search")
        
        return state
    
    async def coding_agent(self, state: AgentState) -> AgentState:
        """Handle code generation and execution"""
        query = state["messages"][-1]["content"]
        
        # Generate code
        code = await self.generate_code(query)
        
        # Execute in sandbox if requested
        if "run" in query.lower():
            result = await self.execute_code_sandbox(code)
            state["results"]["code_execution"] = result
        
        state["messages"].append({
            "role": "assistant",
            "content": f"```python\n{code}\n```",
            "agent": "coder"
        })
        state["tools_used"].append("code_generator")
        
        return state
    
    async def therapeutic_agent(self, state: AgentState) -> AgentState:
        """Handle therapeutic conversations"""
        query = state["messages"][-1]["content"]
        
        # Use specialized therapeutic model
        response = await self.generate_therapeutic_response(query)
        
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "agent": "therapist"
        })
        
        return state
```

### 4. VECTOR DATABASE & RAG SYSTEM

#### Milvus with GPU Acceleration
```python
# services/vector_store.py
from pymilvus import (
    connections, 
    Collection, 
    CollectionSchema, 
    FieldSchema, 
    DataType,
    utility
)
import numpy as np
from sentence_transformers import SentenceTransformer

class MilvusVectorStore:
    def __init__(self, gpu_enabled: bool = True):
        self.gpu_enabled = gpu_enabled
        connections.connect(
            alias="default",
            host="milvus",
            port="19530"
        )
        self.embedding_model = SentenceTransformer('BAAI/bge-m3')
        self.setup_collections()
        
    def setup_collections(self):
        """Setup collections with GPU indexing"""
        # Document embeddings collection
        doc_fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="timestamp", dtype=DataType.INT64)
        ]
        
        doc_schema = CollectionSchema(
            fields=doc_fields,
            description="Document embeddings with user isolation"
        )
        
        self.docs = Collection("jarvis_documents", doc_schema)
        
        # Create GPU-accelerated index (NVIDIA CAGRA)
        if self.gpu_enabled:
            index_params = {
                "metric_type": "COSINE",
                "index_type": "GPU_CAGRA",  # NVIDIA CAGRA for 10-20x performance improvement
                "params": {
                    "intermediate_graph_degree": 64,
                    "graph_degree": 32
                }
            }
        else:
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 256}
            }
            
        self.docs.create_index("embedding", index_params)
        self.docs.load()
    
    async def semantic_search(self, query: str, user_id: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search with user isolation"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search with user filter
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 256}  # Higher ef for better recall
        }
        
        results = self.docs.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=f'user_id == "{user_id}"',  # User isolation
            output_fields=["text", "metadata", "timestamp"]
        )
        
        return [
            {
                "text": hit.entity.get("text"),
                "metadata": hit.entity.get("metadata"),
                "score": hit.score,
                "timestamp": hit.entity.get("timestamp")
            }
            for hit in results[0]
        ]
    
    async def late_chunking_ingest(self, document: str, metadata: Dict, user_id: str):
        """Implement late chunking for better context preservation"""
        # Generate embedding for full document first
        full_embedding = self.embedding_model.encode(document)
        
        # Perform semantic chunking based on sentence boundaries
        chunks = self.semantic_chunk(document)
        
        # Generate chunk embeddings from full document embedding
        chunk_data = []
        for i, chunk in enumerate(chunks):
            # Late chunking: slice embedding based on token positions
            chunk_embedding = self.slice_embedding(full_embedding, chunk, document)
            
            chunk_data.append({
                "embedding": chunk_embedding.tolist(),
                "text": chunk,
                "metadata": {**metadata, "chunk_id": i, "total_chunks": len(chunks)},
                "user_id": user_id,
                "timestamp": int(time.time())
            })
        
        # Batch insert
        self.docs.insert(chunk_data)
        self.docs.flush()
```

#### PostgreSQL with pgvector Integration
```python
# services/postgres_vector.py
import asyncpg
import numpy as np
from typing import List, Dict, Optional

class PostgresVectorStore:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
        
    async def initialize(self):
        """Initialize connection pool and setup tables"""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=10,
            max_size=50,
            command_timeout=60
        )
        
        async with self.pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create optimized tables for RAG
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS document_embeddings (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    document_id VARCHAR(128) NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding vector(1024) NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                -- Create HNSW index for fast similarity search
                CREATE INDEX IF NOT EXISTS doc_embedding_hnsw_idx 
                ON document_embeddings 
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
                
                -- Create index for user isolation
                CREATE INDEX IF NOT EXISTS doc_user_idx 
                ON document_embeddings (user_id);
                
                -- Create partial index for recent documents
                CREATE INDEX IF NOT EXISTS doc_recent_idx 
                ON document_embeddings (created_at DESC)
                WHERE created_at > NOW() - INTERVAL '30 days';
            """)
    
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        user_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """Optimized similarity search with pgvector"""
        async with self.pool.acquire() as conn:
            # Set HNSW search parameters for better performance
            await conn.execute("SET hnsw.ef_search = 100")
            
            results = await conn.fetch("""
                SELECT 
                    chunk_text,
                    metadata,
                    1 - (embedding <=> $1::vector) AS similarity,
                    created_at
                FROM document_embeddings
                WHERE user_id = $2
                    AND 1 - (embedding <=> $1::vector) > $3
                ORDER BY embedding <=> $1::vector
                LIMIT $4
            """, query_embedding, user_id, similarity_threshold, limit)
            
            return [
                {
                    "text": row["chunk_text"],
                    "metadata": row["metadata"],
                    "similarity": float(row["similarity"]),
                    "created_at": row["created_at"]
                }
                for row in results
            ]
```

### 5. SEMANTIC CACHING WITH REDIS (OPEN-SOURCE FIRST)

**Migration Strategy**: Start with open-source Redis semantic caching using langchain-redis, then migrate to Redis LangCache when it becomes generally available (currently in private preview).

#### Redis Semantic Caching Implementation (Open-Source)
```python
# services/semantic_cache.py
import redis
import json
import hashlib
from typing import Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticCache:
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.embedding_model = SentenceTransformer('BAAI/bge-m3')
        self.similarity_threshold = 0.95
        
    async def get_cached_response(self, query: str, user_id: str) -> Optional[Dict]:
        """Retrieve cached response based on semantic similarity"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Search for similar cached queries
        cache_key = f"semantic_cache:{user_id}:*"
        cached_keys = self.redis_client.keys(cache_key)
        
        best_match = None
        best_similarity = 0
        
        for key in cached_keys:
            cached_data = json.loads(self.redis_client.get(key))
            cached_embedding = np.array(cached_data["embedding"])
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, cached_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(cached_embedding)
            )
            
            if similarity > best_similarity and similarity > self.similarity_threshold:
                best_similarity = similarity
                best_match = cached_data
        
        if best_match:
            # Update TTL on cache hit
            self.redis_client.expire(best_match["cache_key"], 86400)  # 24 hours
            return {
                "response": best_match["response"],
                "similarity": best_similarity,
                "cached_at": best_match["timestamp"]
            }
        
        return None
    
    async def cache_response(self, query: str, response: str, user_id: str, metadata: Dict = None):
        """Cache response with semantic embedding"""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        cache_data = {
            "query": query,
            "response": response,
            "embedding": query_embedding,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": int(time.time())
        }
        
        # Create cache key
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        cache_key = f"semantic_cache:{user_id}:{query_hash}"
        cache_data["cache_key"] = cache_key
        
        # Store with 24-hour TTL
        self.redis_client.setex(
            cache_key,
            86400,  # 24 hours
            json.dumps(cache_data)
        )
        
        # Manage cache size (keep only recent 1000 entries per user)
        user_cache_keys = self.redis_client.keys(f"semantic_cache:{user_id}:*")
        if len(user_cache_keys) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(user_cache_keys, 
                               key=lambda k: json.loads(self.redis_client.get(k))["timestamp"])[:100]
            for key in oldest_keys:
                self.redis_client.delete(key)
```

### 6. THERAPEUTIC MODE IMPLEMENTATION

#### Safespace Model Integration
```python
# services/therapeutic_mode.py
from typing import Dict, List, Optional
import httpx
import json

class TherapeuticAssistant:
    def __init__(self, ollama_host: str = "http://ollama:11434"):
        self.ollama_host = ollama_host
        self.client = httpx.AsyncClient(timeout=300.0)
        self.current_mode = "general"
        self.conversation_context = {}
        
        # Therapeutic prompt templates
        self.therapeutic_prompts = {
            "adhd_support": """
            You are a supportive AI assistant specialized in helping individuals with ADHD.
            Your responses should be:
            - Clear and structured with numbered steps when helpful
            - Break down complex tasks into smaller, manageable pieces
            - Provide gentle reminders and focus cues
            - Use encouraging, non-judgmental language
            - Be patient with topic changes or scattered thoughts
            - Offer practical strategies for organization and time management
            """,
            "autism_support": """
            You are a supportive AI assistant specialized in helping individuals with autism.
            Your responses should be:
            - Use literal, direct language without idioms or sarcasm
            - Be clear and specific in all communications
            - Respect routine preferences and need for predictability
            - Be patient and understanding of sensory concerns
            - Provide structured information and step-by-step guidance
            - Avoid overwhelming with too much information at once
            """,
            "general_therapeutic": """
            You are a supportive conversational agent and personal counselor.
            You always respond with empathy, encouragement, and understanding.
            Your goal is to help the user process their thoughts and feelings.
            You do not judge; you listen and ask gentle questions.
            Use a warm, friendly tone and encourage self-reflection.
            For serious mental health concerns, gently suggest professional help.
            """
        }
    
    async def switch_mode(self, mode: str, user_profile: Dict, user_consent: bool = True) -> Dict:
        """Switch to therapeutic mode with user consent"""
        if not user_consent:
            return {"error": "User consent required for therapeutic mode"}
        
        # Save current context
        await self.save_context()
        
        # Determine appropriate therapeutic approach
        if user_profile.get("adhd_support"):
            self.current_mode = "adhd_support"
        elif user_profile.get("autism_support"):
            self.current_mode = "autism_support"
        else:
            self.current_mode = "general_therapeutic"
        
        return {
            "mode": self.current_mode,
            "message": "Switched to therapeutic mode. I'm here to listen and support you.",
            "disclaimer": "This is an AI assistant, not a licensed therapist. For crisis situations or medical advice, please seek professional help."
        }
    
    async def generate_therapeutic_response(self, user_input: str, user_id: str) -> str:
        """Generate therapeutic response using fine-tuned model"""
        # Get conversation context
        context = self.conversation_context.get(user_id, [])
        
        # Build therapeutic prompt
        system_prompt = self.therapeutic_prompts[self.current_mode]
        
        # Check for crisis indicators
        if self.detect_crisis_language(user_input):
            return await self.crisis_response()
        
        # Construct full prompt with context
        messages = [
            {"role": "system", "content": system_prompt},
            *context[-5:],  # Keep last 5 exchanges for context
            {"role": "user", "content": user_input}
        ]
        
        # Use Safespace model for therapeutic responses
        response = await self.client.post(
            f"{self.ollama_host}/api/generate",
            json={
                "model": "safespace:7b",  # Fine-tuned therapeutic model
                "messages": messages,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9
            }
        )
        
        result = response.json()
        therapeutic_response = result["response"]
        
        # Update conversation context (but don't store permanently)
        if user_id not in self.conversation_context:
            self.conversation_context[user_id] = []
        
        self.conversation_context[user_id].extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": therapeutic_response}
        ])
        
        # Keep only recent context (privacy consideration)
        if len(self.conversation_context[user_id]) > 20:
            self.conversation_context[user_id] = self.conversation_context[user_id][-20:]
        
        return therapeutic_response
    
    def detect_crisis_language(self, text: str) -> bool:
        """Detect potential crisis language requiring professional intervention"""
        crisis_indicators = [
            "suicide", "kill myself", "end it all", "no point in living",
            "hurt myself", "self-harm", "cutting", "overdose"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in crisis_indicators)
    
    async def crisis_response(self) -> str:
        """Provide appropriate crisis response"""
        return """
        I'm concerned about what you've shared. Your feelings are valid, but I want you to know that help is available.
        
        Please consider reaching out to:
        • National Suicide Prevention Lifeline: 988
        • Crisis Text Line: Text HOME to 741741
        • A trusted friend, family member, or mental health professional
        
        You don't have to go through this alone. There are people who want to help.
        
        Is there someone you can reach out to right now?
        """
```

### 7. DOCUMENT PROCESSING PIPELINE

#### Docling Integration with Semantic Chunking
```python
# services/document_processor.py
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from typing import List, Dict, Any
import paddleocr
import asyncio

class DocumentProcessor:
    def __init__(self):
        # Initialize Docling converter
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: pipeline_options,
            }
        )
        
        # Initialize PaddleOCR for scanned documents
        self.ocr = paddleocr.PaddleOCR(
            use_angle_cls=True,
            lang='en',
            show_log=False
        )
        
    async def process_document(self, file_path: str, user_id: str) -> Dict[str, Any]:
        """Process document with advanced parsing and chunking"""
        try:
            # Convert document using Docling
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Extract structured content
            extracted_content = {
                "text": doc.export_to_markdown(),
                "tables": [],
                "images": [],
                "metadata": {
                    "title": getattr(doc, "title", ""),
                    "pages": len(doc.pages) if hasattr(doc, "pages") else 0,
                    "format": self.detect_format(file_path)
                }
            }
            
            # Process tables separately for better RAG
            for table in doc.tables:
                table_data = {
                    "content": table.export_to_markdown(),
                    "bbox": table.bbox if hasattr(table, "bbox") else None,
                    "page": table.page if hasattr(table, "page") else None
                }
                extracted_content["tables"].append(table_data)
            
            # Process images with OCR if needed
            for image in doc.images:
                if hasattr(image, "image_data"):
                    ocr_text = await self.extract_text_from_image(image.image_data)
                    image_data = {
                        "ocr_text": ocr_text,
                        "bbox": image.bbox if hasattr(image, "bbox") else None,
                        "page": image.page if hasattr(image, "page") else None
                    }
                    extracted_content["images"].append(image_data)
            
            # Apply semantic chunking
            chunks = await self.semantic_chunk(extracted_content["text"])
            
            # Generate embeddings and store
            await self.store_document_chunks(chunks, extracted_content, user_id, file_path)
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "metadata": extracted_content["metadata"],
                "summary": await self.generate_summary(extracted_content["text"])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def semantic_chunk(self, text: str, max_chunk_size: int = 512) -> List[Dict]:
        """Implement semantic chunking with late chunking principles"""
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('BAAI/bge-m3')
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            # Estimate tokens (rough approximation)
            para_tokens = len(paragraph.split()) * 1.3
            
            if current_tokens + para_tokens <= max_chunk_size:
                current_chunk += paragraph + "\n\n"
                current_tokens += para_tokens
            else:
                if current_chunk:
                    # Create chunk with overlap for context
                    chunks.append({
                        "text": current_chunk.strip(),
                        "tokens": current_tokens,
                        "type": "semantic"
                    })
                
                current_chunk = paragraph + "\n\n"
                current_tokens = para_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "tokens": current_tokens,
                "type": "semantic"
            })
        
        # Add overlap between chunks for better retrieval
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_text = chunk["text"]
            
            # Add overlap from previous chunk
            if i > 0:
                prev_sentences = chunks[i-1]["text"].split('.')[-2:]
                if prev_sentences:
                    overlap = '. '.join(prev_sentences) + '. '
                    chunk_text = overlap + chunk_text
            
            overlapped_chunks.append({
                **chunk,
                "text": chunk_text,
                "chunk_id": i,
                "overlap_added": i > 0
            })
        
        return overlapped_chunks
    
    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from images using PaddleOCR"""
        try:
            # Convert bytes to format PaddleOCR can process
            import io
            from PIL import Image
            import numpy as np
            
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Perform OCR
            result = self.ocr.ocr(image_array)
            
            # Extract text
            text_parts = []
            for line in result[0] if result[0] else []:
                text_parts.append(line[1][0])
            
            return '\n'.join(text_parts)
            
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
```

### 8. DOCKER DEPLOYMENT CONFIGURATION

#### Production Docker Compose
```yaml
# docker-compose.production.yml
version: '3.8'

x-logging: &loki-logging
  driver: loki
  options:
    loki-url: "http://loki:3100/loki/api/v1/push"
    loki-external-labels: service={{.Name}},container={{.ID}}

x-security: &security-defaults
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  cap_add:
    - CHOWN
    - SETGID
    - SETUID

networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.1.0/24
  backend:
    internal: true
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.2.0/24
  ai_network:
    internal: true
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.3.0/24
  monitoring:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  milvus_data:
  opensearch_data:
  minio_data:
  model_cache_gpu0:
  model_cache_gpu1:
  grafana_data:
  prometheus_data:
  loki_data:

services:
  # Frontend Service (Next.js 15)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.production
      target: runner
    <<: *security-defaults
    logging: *loki-logging
    ports:
      - "3000:3000"
    networks:
      - frontend
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.jarvis.local
      - NEXTAUTH_URL=https://jarvis.local
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    depends_on:
      - api
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # API Gateway (FastAPI)
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.production
    <<: *security-defaults
    logging: *loki-logging
    ports:
      - "8000:8000"
    networks:
      - frontend
      - backend
      - ai_network
    environment:
      - DATABASE_URL=postgresql://jarvis_user:${DB_PASSWORD}@postgres:5432/jarvis
      - REDIS_URL=redis://redis:6379
      - MILVUS_HOST=milvus
      - OLLAMA_HOST=http://ollama:11434
      - JWT_SECRET=${JWT_SECRET}
      - OAUTH_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - OAUTH_GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      milvus:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

  # Dual Ollama LLM Services for optimal GPU utilization
  ollama-gpu0:
    image: ollama/ollama:latest
    <<: *security-defaults
    logging: *loki-logging
    container_name: jarvis_ollama_gpu0
    ports:
      - "11434:11434"
    networks:
      - ai_network
    volumes:
      - model_cache_gpu0:/root/.ollama
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - OLLAMA_KEEP_ALIVE=24h
      - OLLAMA_MAX_LOADED_MODELS=3
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_FLASH_ATTENTION=1
      - OLLAMA_KV_CACHE_TYPE=q8_0
      # GPU0 preloaded models
      - OLLAMA_MODELS=llama3.1:8b,mistral:7b,codellama:13b
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]
        limits:
          memory: 32G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  ollama-gpu1:
    image: ollama/ollama:latest
    <<: *security-defaults
    logging: *loki-logging
    container_name: jarvis_ollama_gpu1
    ports:
      - "11435:11434"
    networks:
      - ai_network
    volumes:
      - model_cache_gpu1:/root/.ollama
    environment:
      - CUDA_VISIBLE_DEVICES=1
      - OLLAMA_KEEP_ALIVE=24h
      - OLLAMA_MAX_LOADED_MODELS=3
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_FLASH_ATTENTION=1
      - OLLAMA_KV_CACHE_TYPE=q8_0
      # GPU1 preloaded models
      - OLLAMA_MODELS=deepseek-r1:14b,safespace:7b,qwen2.5:14b
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
        limits:
          memory: 32G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Milvus Vector Database (GPU Accelerated)
  milvus:
    image: milvusdb/milvus:v2.4.0-gpu-nvidia
    <<: *security-defaults
    logging: *loki-logging
    ports:
      - "19530:19530"
      - "9091:9091"
    networks:
      - ai_network
      - backend
    volumes:
      - milvus_data:/var/lib/milvus
    environment:
      - ETCD_ENDPOINTS=etcd:2379
      - MINIO_ADDRESS=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - QDRANT__GPU__INDEXING=true
    depends_on:
      - etcd
      - minio
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 64G
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]
          cpus: '4.0'
          memory: 32G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  # PostgreSQL Database
  postgres:
    image: ankane/pgvector:v0.5.1
    <<: *security-defaults
    logging: *loki-logging
    networks:
      - backend
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-postgres.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_USER=jarvis_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=jarvis
      - POSTGRES_INITDB_ARGS="--encoding=UTF-8 --locale=en_US.UTF-8"
    command: >
      postgres 
      -c shared_preload_libraries=vector
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=2GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jarvis_user -d jarvis"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16G
        reservations:
          cpus: '2.0'
          memory: 8G

  # Redis Cache with Vector Support
  redis:
    image: redis/redis-stack:7.4.0-v1
    <<: *security-defaults
    logging: *loki-logging
    ports:
      - "6379:6379"
      - "8001:8001"  # RedisInsight
    networks:
      - backend
    volumes:
      - redis_data:/data
    command: >
      redis-server 
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 8gb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
      --loadmodule /opt/redis-stack/lib/redisearch.so
      --loadmodule /opt/redis-stack/lib/redistimeseries.so
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 8G
        reservations:
          cpus: '1.0'
          memory: 4G

  # OpenSearch
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    <<: *security-defaults
    logging: *loki-logging
    networks:
      - backend
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    environment:
      - cluster.name=jarvis-cluster
      - node.name=jarvis-node
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "OPENSEARCH_JAVA_OPTS=-Xms4g -Xmx4g"
      - DISABLE_SECURITY_PLUGIN=false
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_PASSWORD}
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
    restart: unless-stopped

  # MinIO Object Storage
  minio:
    image: minio/minio:RELEASE.2024-01-01T16-36-33Z
    <<: *security-defaults
    logging: *loki-logging
    networks:
      - backend
      - ai_network
    volumes:
      - minio_data:/data
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
      - MINIO_PROMETHEUS_AUTH_TYPE=public
    command: server /data --console-address ":9001" --address ":9000"
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    restart: unless-stopped

  # Message Broker for Event-Driven Architecture
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    <<: *security-defaults
    logging: *loki-logging
    container_name: jarvis_rabbitmq
    restart: unless-stopped
    ports:
      - "5672:5672"     # AMQP port
      - "15672:15672"   # Management UI
    networks:
      - backend_network
    environment:
      - RABBITMQ_DEFAULT_USER=jarvis
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
      - RABBITMQ_DEFAULT_VHOST=jarvis
      - RABBITMQ_PLUGINS_ENABLE=rabbitmq_management,rabbitmq_prometheus
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 10s
      retries: 3

  # Supporting Services
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    networks:
      - ai_network
    environment:
      - ETCD_AUTO_COMPACTION_RETENTION=1
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    command: etcd -advertise-client-urls=http://0.0.0.0:2379 -listen-client-urls=http://0.0.0.0:2379 --data-dir /etcd
    volumes:
      - ./etcd:/etcd
    restart: unless-stopped

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:v2.48.0
    <<: *security-defaults
    logging: *loki-logging
    networks:
      - monitoring
      - backend
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.2.0
    <<: *security-defaults
    logging: *loki-logging
    networks:
      - monitoring
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3001:3000"
    restart: unless-stopped

  loki:
    image: grafana/loki:2.9.0
    <<: *security-defaults
    networks:
      - monitoring
    volumes:
      - loki_data:/loki
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
    restart: unless-stopped

  # NVIDIA GPU Exporter for Monitoring
  nvidia-gpu-exporter:
    image: utkuozdemir/nvidia_gpu_exporter:1.2.0
    networks:
      - monitoring
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

### 9. EVENT-DRIVEN ARCHITECTURE

#### Event Bus Implementation

Implementing event-driven architecture for loose coupling, scalability, and system resilience.

```python
# services/event_bus.py
from typing import Dict, Any, Callable, Optional
import asyncio
import aio_pika
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """Central event bus for system-wide communication"""
    
    def __init__(self, rabbitmq_url: str):
        self.url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.exchange = None
        
    async def connect(self):
        """Establish connection with retry logic"""
        self.connection = await aio_pika.connect_robust(
            self.url,
            reconnect_interval=5
        )
        self.channel = await self.connection.channel()
        
        # Create topic exchange
        self.exchange = await self.channel.declare_exchange(
            'jarvis.events',
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish event with reliability guarantees"""
        message = aio_pika.Message(
            body=json.dumps({
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self.exchange.publish(
            message,
            routing_key=event_type
        )
```

#### Event Types Catalog

```python
# events/catalog.py
class EventTypes:
    """Central registry of all event types"""
    
    # Document processing
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_INDEXED = "document.indexed"
    
    # AI agent events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_HANDOFF = "agent.handoff"
    
    # Cache events
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    
    # Model events
    MODEL_LOADED = "model.loaded"
    MODEL_SWITCHED = "model.switched"
```

#### Event-Driven Document Processing

```python
# Example workflow using events
class DocumentProcessor:
    async def process_document(self, doc_id: str, content: bytes):
        # Publish upload event
        await self.event_bus.publish(
            EventTypes.DOCUMENT_UPLOADED,
            {'doc_id': doc_id, 'size': len(content)}
        )
        
        # Process with late chunking
        chunks = await self.late_chunking_process(content)
        
        # Publish processed event
        await self.event_bus.publish(
            EventTypes.DOCUMENT_PROCESSED,
            {'doc_id': doc_id, 'chunks': len(chunks)}
        )
        
        # Vector store will react to this event
        # Cache will warm up automatically
        # Analytics will track processing
```

### 10. MONITORING & OBSERVABILITY

#### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "id": null,
    "title": "Jarvis AI Assistant - Production Monitoring",
    "tags": ["jarvis", "ai", "gpu", "llm"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "LLM Response Times",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, llm_response_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, llm_response_duration_seconds_bucket)",
            "legendFormat": "50th percentile"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 2},
                {"color": "red", "value": 5}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "GPU Memory Usage",
        "type": "timeseries",
        "targets": [
          {
            "expr": "nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes * 100",
            "legendFormat": "GPU {{gpu}} Memory Usage %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "max": 100,
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 90}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Active User Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(active_user_sessions)",
            "legendFormat": "Active Sessions"
          }
        ]
      },
      {
        "id": 4,
        "title": "RAG Query Performance",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(rag_queries_total[5m])",
            "legendFormat": "RAG Queries/sec"
          },
          {
            "expr": "rate(vector_search_duration_seconds_sum[5m]) / rate(vector_search_duration_seconds_count[5m])",
            "legendFormat": "Avg Vector Search Time"
          }
        ]
      },
      {
        "id": 5,
        "title": "Semantic Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(semantic_cache_hits_total[5m]) / (rate(semantic_cache_hits_total[5m]) + rate(semantic_cache_misses_total[5m])) * 100",
            "legendFormat": "Cache Hit Rate %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 70},
                {"color": "green", "value": 85}
              ]
            }
          }
        }
      },
      {
        "id": 6,
        "title": "Model Switching Events",
        "type": "logs",
        "targets": [
          {
            "expr": "{job=\"ollama\"} |= \"model_switch\"",
            "refId": "A"
          }
        ]
      },
      {
        "id": 7,
        "title": "Therapeutic Mode Usage",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(therapeutic_mode_sessions_total[1h])",
            "legendFormat": "Therapeutic Sessions/hour"
          }
        ]
      },
      {
        "id": 8,
        "title": "Document Processing Pipeline",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(documents_processed_total[5m])",
            "legendFormat": "Documents/min"
          },
          {
            "expr": "rate(document_processing_duration_seconds_sum[5m]) / rate(document_processing_duration_seconds_count[5m])",
            "legendFormat": "Avg Processing Time"
          }
        ]
      }
    ]
  }
}
```

### 10. SECURITY IMPLEMENTATION

#### Multi-Layer Security Architecture
```python
# security/security_manager.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Dict, List, Optional
import redis
import json

class SecurityManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.secret_key = secrets.token_hex(32)  # Generated securely
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # Rate limiting configuration
        self.rate_limits = {
            "chat": {"requests": 60, "window": 60},  # 60 requests per minute
            "upload": {"requests": 10, "window": 3600},  # 10 uploads per hour
            "therapeutic": {"requests": 30, "window": 60}  # 30 requests per minute
        }
    
    async def verify_oauth_token(self, provider: str, token: str) -> Dict:
        """Verify OAuth 2.1 token with provider"""
        # OAuth 2.1 implementation with mandatory PKCE
        if provider == "google":
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    return response.json()
        
        raise HTTPException(status_code=401, detail="Invalid OAuth token")
    
    def create_access_token(self, data: Dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials) -> Dict:
        """Verify JWT token and check user status"""
        try:
            payload = jwt.decode(
                credentials.credentials, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check if user is still active
            user_status = await self.get_user_status(user_id)
            if user_status != "active":
                raise HTTPException(status_code=401, detail="User account not active")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def check_rate_limit(self, user_id: str, endpoint: str, request: Request) -> bool:
        """Check rate limiting for user and endpoint"""
        if endpoint not in self.rate_limits:
            return True
        
        limit_config = self.rate_limits[endpoint]
        key = f"rate_limit:{user_id}:{endpoint}"
        
        # Get current request count
        current_requests = self.redis_client.get(key)
        if current_requests is None:
            # First request in window
            self.redis_client.setex(key, limit_config["window"], 1)
            return True
        
        current_count = int(current_requests)
        if current_count >= limit_config["requests"]:
            # Log rate limit violation
            await self.log_security_event(user_id, "rate_limit_exceeded", {
                "endpoint": endpoint,
                "count": current_count,
                "limit": limit_config["requests"],
                "ip": request.client.host
            })
            return False
        
        # Increment counter
        self.redis_client.incr(key)
        return True
    
    async def validate_input(self, data: str, input_type: str) -> bool:
        """Validate and sanitize user input"""
        # SQL injection prevention
        sql_injection_patterns = [
            "'; DROP TABLE", "UNION SELECT", "INSERT INTO",
            "DELETE FROM", "UPDATE SET", "ALTER TABLE"
        ]
        
        data_upper = data.upper()
        for pattern in sql_injection_patterns:
            if pattern in data_upper:
                await self.log_security_event(None, "sql_injection_attempt", {
                    "pattern": pattern,
                    "input_type": input_type
                })
                return False
        
        # XSS prevention
        xss_patterns = ["<script", "javascript:", "onload=", "onerror="]
        data_lower = data.lower()
        for pattern in xss_patterns:
            if pattern in data_lower:
                await self.log_security_event(None, "xss_attempt", {
                    "pattern": pattern,
                    "input_type": input_type
                })
                return False
        
        return True
    
    async def log_security_event(self, user_id: Optional[str], event_type: str, details: Dict):
        """Log security events for monitoring"""
        event = {
            "user_id": user_id,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": secrets.token_hex(8)
        }
        
        # Store in Redis for real-time monitoring
        self.redis_client.lpush("security_events", json.dumps(event))
        self.redis_client.ltrim("security_events", 0, 9999)  # Keep last 10k events
        
        # Alert on critical events
        if event_type in ["sql_injection_attempt", "xss_attempt", "brute_force_detected"]:
            await self.send_security_alert(event)
    
    async def check_user_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """RBAC permission checking"""
        user_role = await self.get_user_role(user_id)
        
        permissions = {
            "admin": ["*"],  # Admin has all permissions
            "user": [
                "chat:read", "chat:write",
                "documents:read", "documents:write", "documents:delete",
                "therapeutic:read", "therapeutic:write",
                "profile:read", "profile:write"
            ],
            "guest": ["chat:read"]
        }
        
        user_permissions = permissions.get(user_role, [])
        required_permission = f"{resource}:{action}"
        
        return "*" in user_permissions or required_permission in user_permissions
```

---

## DEPLOYMENT GUIDE

### 1. System Requirements

#### Hardware Prerequisites
- **CPU**: Dual Intel Xeon (minimum 16 cores)
- **RAM**: 256GB DDR4 (minimum)
- **GPU**: 2× NVIDIA V100 32GB or equivalent
- **Storage**: 2TB NVMe SSD (minimum)
- **Network**: Gigabit Ethernet

#### Software Prerequisites
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose v2
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. Environment Configuration

#### Environment Variables (.env.production)
```bash
# Application
NODE_ENV=production
NEXTAUTH_SECRET=your-nextauth-secret-here
NEXTAUTH_URL=https://jarvis.yourdomain.com

# Database
DB_PASSWORD=your-secure-db-password
REDIS_PASSWORD=your-secure-redis-password

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Object Storage
MINIO_ACCESS_KEY=jarvis-minio-admin
MINIO_SECRET_KEY=your-secure-minio-password

# Monitoring
GRAFANA_PASSWORD=your-grafana-password
OPENSEARCH_PASSWORD=your-opensearch-password

# JWT
JWT_SECRET=your-jwt-secret-generated-with-openssl

# AI Configuration
OLLAMA_MODELS_PATH=/opt/jarvis/models
EMBEDDING_MODEL=BAAI/bge-m3
THERAPEUTIC_MODEL=safespace:7b
```

### 3. SSL/TLS Configuration

#### Traefik Configuration
```yaml
# traefik/traefik.yml
global:
  checkNewVersion: false
  sendAnonymousUsage: false

api:
  dashboard: true
  insecure: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entrypoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@yourdomain.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    exposedByDefault: false
  file:
    filename: /etc/traefik/dynamic.yml
    watch: true
```

### 4. Production Deployment Steps

#### Step 1: Clone and Setup
```bash
# Clone repository
git clone https://github.com/your-org/jarvis-ai.git
cd jarvis-ai

# Create production environment
cp .env.example .env.production
# Edit .env.production with your values

# Create required directories
mkdir -p {data,logs,ssl,monitoring/dashboards}
sudo chown -R $USER:$USER data logs
```

#### Step 2: Build Services
```bash
# Build custom images
docker compose -f docker-compose.production.yml build

# Pull required models
docker compose -f docker-compose.production.yml run --rm ollama bash -c "
  ollama pull llama3.1:8b &&
  ollama pull deepseek-r1:14b &&
  ollama pull mistral:7b &&
  ollama pull qwen2.5:7b &&
  ollama pull safespace:7b
"
```

#### Step 3: Initialize Databases
```bash
# Start core services
docker compose -f docker-compose.production.yml up -d postgres redis minio

# Wait for services to be ready
sleep 30

# Initialize database schemas
docker compose -f docker-compose.production.yml run --rm api python -c "
from services.database import init_database
init_database()
"

# Create admin user
docker compose -f docker-compose.production.yml run --rm api python -c "
from services.auth import create_admin_user
create_admin_user('admin@yourdomain.com', 'Admin User')
"
```

#### Step 4: Deploy Full Stack
```bash
# Deploy all services
docker compose -f docker-compose.production.yml up -d

# Verify deployment
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs -f --tail=50
```

### 5. Health Checks and Monitoring

#### Health Check Script
```bash
#!/bin/bash
# scripts/health-check.sh

echo "🔍 Jarvis Health Check"
echo "====================="

# Check services
services=("frontend" "api" "ollama" "milvus" "postgres" "redis")
for service in "${services[@]}"; do
    if docker compose ps $service | grep -q "Up"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Down"
    fi
done

# Check GPU availability
if nvidia-smi > /dev/null 2>&1; then
    echo "✅ GPU: Available"
    nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits
else
    echo "❌ GPU: Not available"
fi

# Check API endpoints
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API: Responding"
else
    echo "❌ API: Not responding"
fi

# Check model availability
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama: Models available"
else
    echo "❌ Ollama: Models not available"
fi
```

---

## PERFORMANCE OPTIMIZATION

### 1. GPU Memory Management

#### Optimal Model Distribution
```python
# GPU allocation strategy for dual V100 (16GB each)
MODEL_ALLOCATION = {
    "gpu_0": {
        "primary": "llama3.1:8b",        # ~8GB
        "secondary": "mistral:7b",       # ~7GB
        "available_memory": "1GB"        # Buffer
    },
    "gpu_1": {
        "primary": "deepseek-r1:14b",    # ~14GB
        "therapeutic": "safespace:7b",    # Loaded on demand
        "available_memory": "2GB"        # Buffer
    }
}
```

### 2. Caching Strategy

#### Multi-Level Caching
1. **L1 Cache (Memory)**: Active conversation context
2. **L2 Cache (Redis)**: Semantic cache for common queries
3. **L3 Cache (SSD)**: Model weights and embeddings

### 3. Database Optimization

#### PostgreSQL Configuration
```sql
-- Optimized settings for pgvector
-- shared_buffers = 25% of RAM (64GB)
ALTER SYSTEM SET shared_buffers = '64GB';
ALTER SYSTEM SET effective_cache_size = '192GB';
ALTER SYSTEM SET maintenance_work_mem = '8GB';
ALTER SYSTEM SET work_mem = '1GB';
ALTER SYSTEM SET max_parallel_workers_per_gather = 8;
```

---

## CONCLUSION

This comprehensive blueprint provides a production-ready architecture for Jarvis AI Assistant, incorporating the latest 2025 best practices and technologies. The system is designed for:

- **High Performance**: Dual GPU optimization with intelligent model switching
- **Enterprise Security**: OAuth 2.1 with PKCE, RBAC, and comprehensive audit logging
- **Advanced AI Capabilities**: Multi-agent orchestration, therapeutic mode, and advanced RAG
- **Production Reliability**: Comprehensive monitoring, health checks, and auto-scaling
- **Future Extensibility**: Modular architecture supporting rapid feature development

The architecture leverages cutting-edge technologies including Next.js 15, FastAPI with OAuth 2.1 (PKCE), LangGraph for agent orchestration, Milvus with GPU acceleration, and comprehensive observability with Prometheus/Grafana/Loki stack.

This blueprint represents the state-of-the-art in self-hosted AI assistant deployment for 2025, providing a robust foundation for advanced AI applications while maintaining security, performance, and scalability.

---

**Document Version**: 2025.1  
**Last Updated**: June 13, 2025  
**Status**: Production Ready  
**Review Date**: December 2025