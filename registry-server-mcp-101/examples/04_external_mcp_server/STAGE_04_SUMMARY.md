# Stage 04: External MCP Server - Summary

## What's New in Stage 04?

Stage 04 takes the complete agent coordination from Stage 03 and adds **production-ready deployment** by separating the MCP server from the client.

## Key Innovation

### Stage 03 (Embedded Server)
```python
# Server runs inside the client script
# Tightly coupled - one server per client
```

### Stage 04 (External Server)
```python
# Server runs independently
# Loosely coupled - one server, many clients
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       STAGE 04 ARCHITECTURE                   │
└──────────────────────────────────────────────────────────────┘

Terminal 1: MCP Server              Terminal 2: Client 1
┌─────────────────────┐            ┌─────────────────────┐
│  start_mcp_server   │            │  external_mcp_      │
│                     │            │  client.py          │
│  ┌───────────────┐  │            │                     │
│  │  FastMCP      │  │◄───HTTP────┤  MCP Connection     │
│  │  HTTP/SSE     │  │            │  (SSE client)       │
│  │  Port 8080    │  │            │                     │
│  └───────┬───────┘  │            │  ┌───────────────┐  │
│          │          │            │  │  A2A Client   │  │
│  ┌───────▼───────┐  │            │  └───────────────┘  │
│  │  agent_mcp.py │  │            │                     │
│  │  (8 tools)    │  │            │  Claude orchestrates│
│  └───────┬───────┘  │            └─────────────────────┘
│          │          │
│  ┌───────▼───────┐  │            Terminal 3: Client 2
│  │  MongoDB      │  │            ┌─────────────────────┐
│  │  Atlas        │  │◄───HTTP────┤  Another client     │
│  └───────────────┘  │            │  can connect!       │
└─────────────────────┘            └─────────────────────┘
```

## Two Components

### 1. Server (`start_mcp_server.py`)
```bash
python 04_external_mcp_server/start_mcp_server.py --port 8080

# Starts FastMCP server via HTTP/SSE
# Keeps running until Ctrl+C
# Serves multiple clients
# Independent lifecycle
```

**What it does:**
- Starts the existing `src/agent_mcp.py` server
- Uses FastMCP's HTTP/SSE transport
- Exposes on `http://localhost:8080/sse`
- Handles concurrent connections

### 2. Client (`external_mcp_client.py`)
```bash
python 04_external_mcp_server/external_mcp_client.py

# Connects to external server via HTTP/SSE
# Same A2A functionality as Stage 03
# Can disconnect/reconnect
# Server keeps running
```

**What it does:**
- Connects to external MCP server
- Uses SSE client instead of stdio
- All Stage 03 functionality (MCP + A2A)
- Loosely coupled from server

## Workflow

### Step 1: Start Server (Once)
```bash
# Terminal 1 - From repository root
$ export ATLAS_URL="mongodb+srv://..."
$ fastmcp run src/agent_mcp.py --transport sse --port 8080

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)

# Server stays running...
```

### Step 2: Run Client (Many Times)
```bash
# Terminal 2 - From repository root
$ export ANTHROPIC_API_KEY="sk-ant-..."
$ python examples/04_external_mcp_server/external_mcp_client.py

🔗 Connecting to MCP server at http://localhost:8080/sse...
✓ Connected to external NANDA Registry MCP server
✓ Available MCP tools: 8

You: What agents are registered?
Claude: I found 3 agents...

You: quit

# Client exits, but server keeps running in Terminal 1!
```

### Step 3: Run Another Client (Optional)
```bash
# Terminal 3 - From repository root
$ export ANTHROPIC_API_KEY="sk-ant-..."
$ python examples/04_external_mcp_server/external_mcp_client.py

# Connects to same server!
# Both clients work simultaneously
```

## Benefits

### 1. Server Independence
- Server runs continuously
- Client crashes don't affect server
- Server can be restarted independently

### 2. Multiple Clients
- Many clients can connect
- Concurrent access supported
- Shared server resources

### 3. Distributed Deployment
- Server on one machine
- Clients on other machines
- Network-based communication

### 4. Production Ready
- Standard HTTP/SSE protocol
- Works with load balancers
- Can be containerized
- Monitoring-friendly

### 5. Development Friendly
- Start server once
- Run client many times
- Faster iteration
- Easier debugging

## Use Cases

### Development
```bash
# Start server once at beginning of day
Terminal 1: fastmcp run src/agent_mcp.py --transport sse --port 8080

# Run/test client multiple times
Terminal 2: python examples/04_external_mcp_server/external_mcp_client.py  # Test 1
Terminal 2: python examples/04_external_mcp_server/external_mcp_client.py  # Test 2
Terminal 2: python examples/04_external_mcp_server/external_mcp_client.py  # Test 3
```

### Production
```bash
# Deploy server as service (systemd, Docker, K8s)
Server: Always running on port 8080

# Clients connect from anywhere
Client 1: Web application
Client 2: CLI tool
Client 3: Background worker
Client 4: Monitoring tool
```

### Testing
```bash
# Server in CI/CD pipeline
docker run -p 8080:8080 mcp-server

# Multiple test clients
pytest test_client_1.py  # Connects to server
pytest test_client_2.py  # Connects to server
pytest test_client_3.py  # Connects to server
```

## Comparison

| Aspect | Stage 03 | Stage 04 |
|--------|----------|----------|
| **Server Start** | Automatic with client | Manual, separate |
| **Server Lifecycle** | Dies with client | Independent |
| **Transport** | stdio (local) | HTTP/SSE (network) |
| **Multiple Clients** | No | Yes |
| **Client Restarts** | Restarts server | Server keeps running |
| **Debugging** | Harder (coupled) | Easier (separate logs) |
| **Production** | ✅ Works | ✅✅✅ Better |
| **Scalability** | Limited | High |
| **Network** | Local only | Can be remote |

## Migration from Stage 03

### Change 1: Connection Type
```python
# Stage 03: stdio
from mcp.client.stdio import stdio_client
server_params = StdioServerParameters(...)
stdio_context = stdio_client(server_params)

# Stage 04: HTTP/SSE
from mcp.client.sse import sse_client
mcp_server_url = "http://localhost:8080/sse"
sse_context = sse_client(mcp_server_url)
```

### Change 2: Server Management
```python
# Stage 03: Client manages server
# Client starts server
# Client stops server

# Stage 04: Independent server
# Server runs separately
# Client just connects
```

### Change 3: Error Handling
```python
# Stage 04: Add connection error handling
try:
    await start_mcp_connection()
except Exception as e:
    print("Make sure server is running!")
    print("python start_mcp_server.py")
    raise
```

## Deployment Options

### Option 1: Local Development
```bash
# Both on same machine
Terminal 1: python start_mcp_server.py
Terminal 2: python external_mcp_client.py
```

### Option 2: Docker Compose
```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    ports:
      - "8080:8080"
  
  client:
    build: .
    environment:
      MCP_SERVER_URL: http://mcp-server:8080/sse
```

### Option 3: Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
spec:
  replicas: 3  # Multiple instances!
  # ... (see Stage 04 README for full example)
```

### Option 4: Linode Cloud Deployment
[Registry Deployment Documentation](deploy/README.md)


## Quick Start

```bash
# 1. Set environment variables
export ATLAS_URL="mongodb+srv://..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Start server (Terminal 1) - From repository root
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080

# 3. Run client (Terminal 2) - From repository root
python examples/04_external_mcp_server/external_mcp_client.py

# 4. Chat with agents!
You: What agents are available?
You: Ask agent-123 to help with analysis
```


## When to Use Stage 04

Use Stage 04 when you need:
- ✅ Production deployment
- ✅ Multiple clients
- ✅ Distributed architecture
- ✅ Container/K8s deployment
- ✅ Load balancing
- ✅ High availability
- ✅ Independent server lifecycle
- ✅ Easier monitoring

Use Stage 03 when:
- ⚠️ Simple single-client use case
- ⚠️ Prototyping/testing
- ⚠️ No need for server persistence

## Summary

**Stage 04** = **Stage 03** + **Production Deployment Pattern**

- Same functionality (MCP + A2A)
- Different architecture (External server)
- Better scalability
- More production-ready
- Industry-standard deployment
