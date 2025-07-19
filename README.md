# Membase FastAPI

A FastAPI wrapper for the Membase SDK, providing RESTful endpoints for interacting with the decentralized AI memory layer.

## Features

- **Agent Management**: Register agents and manage blockchain-based permissions
- **AIP Integration**: Advanced agent communication and intelligent routing
- **Task Coordination**: Create, join, and complete tasks with rewards
- **Memory/Conversations**: Store and retrieve AI conversation histories
- **Auto-upload to Hub**: Automatic synchronization with decentralized storage
- **API Key Authentication**: Optional API key protection
- **Interactive Documentation**: Built-in Swagger UI and ReDoc

## Installation

1. Install membase SDK (if not already installed):
```bash
cd ..
pip install -e .
```

2. Install FastAPI dependencies:
```bash
cd membase-api
pip install -r requirements.txt
```

## Configuration

1. Copy and edit the `.env` file:
```bash
cp .env .env.local
```

2. Update the environment variables:
```env
# Required: Your blockchain credentials
MEMBASE_ID=your-agent-id
MEMBASE_ACCOUNT=0xYourWalletAddress
MEMBASE_SECRET_KEY=0xYourPrivateKey

# Optional: API configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-secret-api-key  # Optional API key for protection

# Storage
CHROMA_PERSIST_DIR=./chroma_db

# AIP Configuration
ENABLE_AIP=true
```

## Running the API

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access the interactive documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## API Endpoints

### Health Check
```bash
GET /health
```

### Agents
- `POST /api/v1/agents/register` - Register a new agent on blockchain
- `GET /api/v1/agents/{agent_id}` - Get agent information
- `POST /api/v1/agents/buy-auth` - Buy authorization between agents
- `GET /api/v1/agents/{agent_id}/has-auth/{target_id}` - Check authorization

#### AIP Agent Features (when ENABLE_AIP=true)
- `POST /api/v1/agents/create` - Create an AIP agent with LLM capabilities
- `POST /api/v1/agents/{agent_id}/query` - Process queries with advanced options
- `POST /api/v1/agents/{agent_id}/message` - Send messages between agents
- `PUT /api/v1/agents/{agent_id}/prompt` - Update agent system prompt
- `GET /api/v1/agents/active` - List active AIP agents
- `DELETE /api/v1/agents/{agent_id}/stop` - Stop an AIP agent

### Tasks
- `POST /api/v1/tasks/create` - Create a new task
- `POST /api/v1/tasks/{task_id}/join` - Join a task
- `POST /api/v1/tasks/{task_id}/finish` - Mark task as finished
- `GET /api/v1/tasks/{task_id}` - Get task information

### Memory (Conversations)
- `POST /api/v1/memory/conversations` - Create new conversation
- `GET /api/v1/memory/conversations` - List all conversations
- `GET /api/v1/memory/conversations/{conversation_id}` - Get conversation messages
- `POST /api/v1/memory/conversations/{conversation_id}/messages` - Add messages
- `DELETE /api/v1/memory/conversations/{conversation_id}` - Clear conversation
- `DELETE /api/v1/memory/conversations/{conversation_id}/messages/{index}` - Delete specific message
- `POST /api/v1/memory/conversations/{conversation_id}/upload` - Manually upload to hub

### Knowledge Base
- `POST /api/v1/knowledge/documents` - Add documents
- `GET /api/v1/knowledge/documents/search` - Search documents
- `PUT /api/v1/knowledge/documents` - Update documents
- `DELETE /api/v1/knowledge/documents` - Delete documents
- `GET /api/v1/knowledge/documents/stats` - Get statistics
- `POST /api/v1/knowledge/documents/optimal-threshold` - Find optimal search threshold
- `DELETE /api/v1/knowledge/documents/all` - Clear all documents
- `POST /api/v1/knowledge/documents/upload` - Upload to hub

### Intelligent Routing (when ENABLE_AIP=true)
- `POST /api/v1/route` - Intelligently route requests to appropriate handlers
- `GET /api/v1/route/categories` - List available routing categories
- `POST /api/v1/route/agent` - Route specifically to agents
- `POST /api/v1/route/function` - Route specifically to functions

## Usage Examples

### 1. Register an Agent
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/agents/register",
    json={"agent_id": "alice"}
)
print(response.json())
```

### 2. Create a Conversation and Add Messages
```python
# Create conversation
conv_response = requests.post(
    "http://localhost:8000/api/v1/memory/conversations",
    json={"conversation_id": "chat-001"}
)

# Add message
msg_response = requests.post(
    "http://localhost:8000/api/v1/memory/conversations/chat-001/messages",
    json={
        "messages": {
            "name": "user",
            "content": "Hello, AI assistant!",
            "role": "user"
        }
    }
)
```

### 3. Create and Query AIP Agent
```python
# Create AIP agent
agent_response = requests.post(
    "http://localhost:8000/api/v1/agents/create",
    json={
        "agent_id": "assistant",
        "description": "A helpful AI assistant"
    }
)

# Query the agent
query_response = requests.post(
    "http://localhost:8000/api/v1/agents/assistant/query",
    json={
        "query": "What is Python?",
        "use_tool_call": True
    }
)
```

### 4. Use Intelligent Routing
```python
# Route a request
route_response = requests.post(
    "http://localhost:8000/api/v1/route",
    json={
        "request": "Calculate tax on $5000 income",
        "top_k": 2
    }
)
# Returns best handlers for the request
```

### 5. Create and Manage Tasks
```python
# Create task
task_response = requests.post(
    "http://localhost:8000/api/v1/tasks/create",
    json={
        "task_id": "analyze-data-001",
        "price": 100000
    }
)

# Join task
join_response = requests.post(
    "http://localhost:8000/api/v1/tasks/analyze-data-001/join",
    json={"agent_id": "alice"}
)
```

## Authentication

If `API_KEY` is set in the environment, include it in your requests:

```python
headers = {"X-API-Key": "your-secret-api-key"}
response = requests.get(
    "http://localhost:8000/api/v1/memory/conversations",
    headers=headers
)
```

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `201`: Created
- `202`: Accepted (for async operations)
- `400`: Bad Request
- `401`: Unauthorized (missing/invalid API key)
- `404`: Not Found
- `500`: Internal Server Error

Error responses include a detail message:
```json
{
    "detail": "Error description here"
}
```

## Docker Support

Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t membase-api .
docker run -p 8000:8000 --env-file .env membase-api
```

## AIP Integration

The API includes optional AIP (Agent Interoperability Protocol) features that add:

- **Advanced Agent Communication**: Agents can send messages to each other
- **Intelligent Routing**: Automatically route requests to the best handler
- **Dynamic Configuration**: Update agent prompts and behavior on the fly

### Enabling AIP Features

Set `ENABLE_AIP=true` in your `.env` file

### AIP Usage Example

```python
# Create an intelligent agent
response = requests.post(
    "http://localhost:8000/api/v1/agents/create",
    json={
        "agent_id": "trading_agent",
        "description": "A cryptocurrency trading assistant"
    }
)

# Query the agent
response = requests.post(
    "http://localhost:8000/api/v1/agents/trading_agent/query",
    json={
        "query": "What's the current BTC price?",
        "conversation_id": "trading-session-1",
        "use_tool_call": True
    }
)

# Send inter-agent message
response = requests.post(
    "http://localhost:8000/api/v1/agents/trading_agent/message",
    json={
        "target_agent_id": "analyst_agent",
        "message": "Should we buy BTC now?"
    }
)
```

## Development Tips

1. **Enable Debug Logging**: Set `LOG_LEVEL=DEBUG` in `.env`
2. **Auto-reload**: The development server auto-reloads on code changes
3. **Test Endpoints**: Use the Swagger UI at `/docs` for testing
4. **Monitor Hub Uploads**: Check logs for background upload status
5. **AIP Development**: Set `ENABLE_AIP=false` to disable AIP features during development

## Troubleshooting

### Connection Issues
- Verify blockchain RPC endpoints are accessible
- Check that membase hub URL is correct
- Ensure wallet has sufficient balance for transactions

### Authentication Errors
- Verify `MEMBASE_ACCOUNT` and `MEMBASE_SECRET_KEY` are correct
- Ensure private key format includes `0x` prefix
- Check that the account is registered on-chain

### Knowledge Base Issues
- Ensure `CHROMA_PERSIST_DIR` is writable
- Check disk space for vector storage
- Verify ChromaDB is properly installed

## License

This project follows the same license as the Membase SDK.