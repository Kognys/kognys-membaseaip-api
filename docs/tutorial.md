# Membase API Tutorial

This tutorial provides a comprehensive guide to using the Membase API, which combines blockchain-based agent management, decentralized memory storage, and AI capabilities.

## Table of Contents
1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [API Endpoints Guide](#api-endpoints-guide)
4. [Working with Agents](#working-with-agents)
5. [Managing Tasks](#managing-tasks)
6. [Memory & Conversations](#memory--conversations)
7. [Knowledge Base](#knowledge-base)
8. [AIP Integration](#aip-integration)
9. [Practical Examples](#practical-examples)

## Overview

The Membase API is a FastAPI-based REST service that provides:

- **Blockchain Integration**: Register agents and manage permissions on-chain
- **Decentralized Storage**: Persistent memory and knowledge storage with automatic hub synchronization
- **AI Capabilities**: Optional AIP integration for LLM-powered agents and intelligent routing
- **Task Management**: Create and manage blockchain-based tasks with rewards

## Core Concepts

### Membase SDK
The API wraps the Membase Python SDK, which provides:
- `MultiMemory`: Manages multiple conversation threads
- `ChromaKnowledgeBase`: Vector storage for document retrieval
- `membase_chain`: Blockchain interface for on-chain operations

### Blockchain Identity
Agents have two types of identity:
1. **On-chain registration**: Permanent blockchain record (via `/agents/register`)
2. **AIP agents**: Live AI agents with LLM capabilities (via `/agents/create`)

### Storage Architecture
- **Conversations**: Stored in memory with automatic hub backup
- **Knowledge**: Vector embeddings stored in ChromaDB
- **Hub**: Decentralized storage backend for persistence

## API Endpoints Guide

### Authentication
If `API_KEY` is configured, include it in requests:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/...
```

### Base URL
All endpoints are prefixed with `/api/v1`

## Working with Agents

### 1. Blockchain Agent Registration

Register an agent on the blockchain to establish identity:

```bash
POST /api/v1/agents/register
{
    "agent_id": "alice"
}
```

This creates a permanent on-chain record linking the agent ID to a blockchain address.

### 2. Get Agent Information

```bash
GET /api/v1/agents/alice
```

Returns the agent's blockchain address and registration status.

### 3. Agent Authorization

Allow one agent to access another's data:

```bash
POST /api/v1/agents/buy-auth
{
    "buyer_id": "alice",
    "seller_id": "bob"
}
```

### 4. Check Authorization

```bash
GET /api/v1/agents/alice/has-auth/bob
```

## Managing Tasks

Tasks are blockchain-based work units with rewards.

### 1. Create a Task

```bash
POST /api/v1/tasks/create
{
    "task_id": "analyze-data-001",
    "price": 100000
}
```

### 2. Join a Task

```bash
POST /api/v1/tasks/analyze-data-001/join
{
    "agent_id": "alice"
}
```

### 3. Complete a Task

```bash
POST /api/v1/tasks/analyze-data-001/finish
{
    "agent_id": "alice"
}
```

### 4. Get Task Status

```bash
GET /api/v1/tasks/analyze-data-001
```

## Memory & Conversations

The memory system stores conversation histories with automatic persistence.

### 1. Create a Conversation

```bash
POST /api/v1/memory/conversations
{
    "conversation_id": "chat-2024"  # Optional, auto-generated if not provided
}
```

### 2. Add Messages

```bash
POST /api/v1/memory/conversations/chat-2024/messages
{
    "messages": {
        "name": "user",
        "content": "Hello, how can AI help with data analysis?",
        "role": "user"
    }
}
```

Or add multiple messages:
```bash
{
    "messages": [
        {
            "name": "user",
            "content": "What is machine learning?",
            "role": "user"
        },
        {
            "name": "assistant",
            "content": "Machine learning is...",
            "role": "assistant"
        }
    ]
}
```

### 3. Retrieve Messages

```bash
GET /api/v1/memory/conversations/chat-2024
GET /api/v1/memory/conversations/chat-2024?recent_n=10  # Last 10 messages
```

### 4. List All Conversations

```bash
GET /api/v1/memory/conversations
```

### 5. Clear a Conversation

Remove all messages from a conversation (conversation still exists):

```bash
DELETE /api/v1/memory/conversations/chat-2024
```

### 6. Delete a Specific Message

Delete a message by its index (0-based):

```bash
DELETE /api/v1/memory/conversations/chat-2024/messages/3
```

### 7. Manual Hub Upload

Trigger manual upload to decentralized storage:

```bash
POST /api/v1/memory/conversations/chat-2024/upload
```

Returns immediately with 202 Accepted status while upload happens in background.

## Knowledge Base

The knowledge base provides vector search capabilities for documents.

### 1. Add Documents

```bash
POST /api/v1/knowledge/documents
{
    "documents": {
        "content": "Python is a versatile programming language...",
        "metadata": {
            "category": "programming",
            "language": "python"
        }
    },
    "strict": true  # Enable duplicate checking
}
```

### 2. Search Documents

```bash
GET /api/v1/knowledge/documents/search?query=What is Python&top_k=5&similarity_threshold=0.7
```

With filters:
```bash
GET /api/v1/knowledge/documents/search?query=programming&metadata_filter={"category":"programming"}
```

### 3. Update Documents

```bash
PUT /api/v1/knowledge/documents
{
    "documents": {
        "doc_id": "doc_123",
        "content": "Updated content...",
        "metadata": {"updated": true}
    }
}
```

### 4. Delete Documents

```bash
DELETE /api/v1/knowledge/documents?doc_ids=doc_123
DELETE /api/v1/knowledge/documents?doc_ids=["doc_123","doc_456"]
```

### 5. Get Statistics

```bash
GET /api/v1/knowledge/documents/stats
```

### 6. Find Optimal Search Threshold

```bash
POST /api/v1/knowledge/documents/optimal-threshold
{
    "query": "machine learning",
    "min_threshold": 0.5,
    "max_threshold": 0.9,
    "step": 0.1
}
```

## AIP Integration

When `ENABLE_AIP=true`, advanced AI features become available.

### 1. Create an AIP Agent

```bash
POST /api/v1/agents/create
{
    "agent_id": "assistant",
    "description": "A helpful AI assistant",
    "default_conversation_id": "main-chat"
}
```

This creates a live AI agent that can:
- Process queries using LLMs (OpenAI by default)
- Maintain conversation context
- Communicate with other agents
- Use tools and functions

### 2. Query an AIP Agent

```bash
POST /api/v1/agents/assistant/query
{
    "query": "Explain quantum computing",
    "conversation_id": "physics-chat",
    "use_history": true,
    "use_tool_call": true,
    "recent_n_messages": 10
}
```

### 3. Inter-Agent Communication

```bash
POST /api/v1/agents/assistant/message
{
    "target_agent_id": "researcher",
    "action": "ask",
    "message": "Can you find papers on quantum computing?"
}
```

### 4. Update Agent Prompt

```bash
PUT /api/v1/agents/assistant/prompt
{
    "system_prompt": "You are a quantum physics expert. Be precise and technical."
}
```

### 5. List Active Agents

```bash
GET /api/v1/agents/active
```

### 6. Stop an Agent

```bash
DELETE /api/v1/agents/assistant/stop
```

### 7. Intelligent Routing

Route requests to the most appropriate handler:

```bash
POST /api/v1/route
{
    "request": "Calculate the tax on $5000",
    "top_k": 3
}
```

Response shows the best agents/functions for the task:
```json
{
    "routes": [
        {
            "category_name": "TaxCalculatorAgent",
            "category_type": "agent",
            "confidence": "high",
            "reasoning": "Request involves tax calculation",
            "score": 0.95
        }
    ]
}
```

## Practical Examples

### Example 1: Building a Chatbot with Memory

```python
import requests

API_URL = "http://localhost:8000/api/v1"

# 1. Create an AIP agent
agent = requests.post(f"{API_URL}/agents/create", json={
    "agent_id": "chatbot",
    "description": "Customer support chatbot"
}).json()

# 2. Create a conversation
conv = requests.post(f"{API_URL}/memory/conversations", json={
    "conversation_id": "support-123"
}).json()

# 3. Process user query
response = requests.post(f"{API_URL}/agents/chatbot/query", json={
    "query": "I need help with my order",
    "conversation_id": "support-123",
    "use_history": True
}).json()

print(response["response"])
```

### Example 2: Building a Knowledge-Enhanced Assistant

```python
# 1. Add knowledge documents
requests.post(f"{API_URL}/knowledge/documents", json={
    "documents": [
        {
            "content": "Our return policy allows returns within 30 days...",
            "metadata": {"topic": "returns", "category": "policy"}
        },
        {
            "content": "Shipping takes 3-5 business days...",
            "metadata": {"topic": "shipping", "category": "policy"}
        }
    ]
})

# 2. Search for relevant information
results = requests.get(
    f"{API_URL}/knowledge/documents/search",
    params={"query": "return policy", "top_k": 3}
).json()

# 3. Use results in agent response
context = "\n".join([r["content"] for r in results["results"]])
response = requests.post(f"{API_URL}/agents/chatbot/query", json={
    "query": "What is your return policy?",
    "system_prompt": f"Use this context to answer: {context}"
}).json()
```

### Example 3: Multi-Agent Collaboration

```python
# 1. Create multiple agents
researcher = requests.post(f"{API_URL}/agents/create", json={
    "agent_id": "researcher",
    "description": "Research specialist"
}).json()

writer = requests.post(f"{API_URL}/agents/create", json={
    "agent_id": "writer", 
    "description": "Content writer"
}).json()

# 2. Researcher gathers information
research = requests.post(f"{API_URL}/agents/researcher/query", json={
    "query": "Research the latest trends in AI"
}).json()

# 3. Send findings to writer
response = requests.post(f"{API_URL}/agents/researcher/message", json={
    "target_agent_id": "writer",
    "message": f"Here are my findings: {research['response']}"
}).json()

# 4. Writer creates content
article = requests.post(f"{API_URL}/agents/writer/query", json={
    "query": "Write an article based on the research you received"
}).json()
```

## Best Practices

1. **Memory Management**
   - Use meaningful conversation IDs
   - Limit history with `recent_n_messages` for long conversations
   - Messages are auto-uploaded to hub for persistence

2. **Knowledge Base**
   - Add relevant metadata for better filtering
   - Use `optimal-threshold` endpoint to tune search accuracy
   - Consider chunking large documents

3. **AIP Agents**
   - Stop agents when not needed to free resources
   - Update prompts dynamically for different contexts
   - Use routing to automatically select the right agent

4. **Security**
   - Always use API keys in production
   - Register agents on blockchain for identity verification
   - Use authorization for agent-to-agent data access

## Configuration Tips

Key environment variables:
```env
# Required for blockchain
MEMBASE_ACCOUNT=0xYourAddress
MEMBASE_SECRET_KEY=0xYourPrivateKey

# Required for AIP features
OPENAI_API_KEY=sk-...
ENABLE_AIP=true

# Optional
API_KEY=your-api-key
CHROMA_PERSIST_DIR=./chroma_db
```

## Troubleshooting

1. **Agent not found**: Ensure the agent is created (AIP) or registered (blockchain)
2. **Memory not persisting**: Check hub connectivity and auto_upload settings
3. **Search returning no results**: Lower similarity_threshold or check embeddings
4. **AIP features not working**: Verify ENABLE_AIP=true and OpenAI API key

This tutorial covers the core functionality of the Membase API. For more details, check the interactive documentation at `/docs` when running the API.