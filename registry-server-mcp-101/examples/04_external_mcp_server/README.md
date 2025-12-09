# Stage 04: External MCP Server

## Overview

This stage demonstrates **production deployment** by separating the MCP server from the client application.

## Concept

Instead of starting the MCP server inside the client script (stdio), we run the MCP server as a separate service via HTTP/SSE and connect to it from the client.

## Key Improvement over Stage 03

**Stage 03 (Embedded Server)**:
```python
# MCP server runs inside the Python script via stdio
server_params = StdioServerParameters(
    command="python",
    args=["src/agent_mcp.py"]
)
# Tightly coupled - server dies when script ends
```

**Stage 04 (External Server)**:
```python
# MCP server runs in separate process via HTTP/SSE
## Deployment Examples

### Local Development

**Terminal 1: Server**
```bash
export ATLAS_URL="mongodb+srv://..."
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080
```

**Terminal 2: Client**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python examples/04_external_mcp_server/external_mcp_client.py
```

# Connects via HTTP
mcp_server_url = "http://localhost:8080/sse"
# Loosely coupled - server independent of client
```

## Architecture

```
Terminal 1 (Server):                Terminal 2 (Client):
┌──────────────────────┐           ┌──────────────────────┐
│  MCP Server          │           │  Claude Client       │
│  (agent_mcp.py)      │           │                      │
│                      │           │  ┌────────────────┐  │
│  • HTTP/SSE on 8080  │◄──────────┤  │ MCP Connection │  │
│  • MongoDB           │           │  └────────────────┘  │
│  • 8 tools exposed   │   HTTP    │                      │
│  • Always running    │           │  ┌────────────────┐  │
└──────────────────────┘           │  │ A2A Client     │  │
                                   │  └────────────────┘  │
                                   │                      │
                                   │  Claude orchestrates │
                                   └──────────────────────┘
```

## Files

### Server: Use FastMCP CLI
**Purpose**: Start the MCP server via HTTP/SSE transport

**Command**:
```bash
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080
```

**Features**:
- Uses existing `src/agent_mcp.py` without modification
- Serves via HTTP/SSE on configurable port (default: 8080)
- Independent process - runs continuously
- Can be deployed on separate machine
- Built into FastMCP - no wrapper script needed

### `external_mcp_client.py`
**Purpose**: Client that connects to external MCP server

**Features**:
- Connects via HTTP/SSE instead of stdio
- Same A2A communication as Stage 03
- Loosely coupled from server
- Can connect to remote MCP servers

**Usage**:
```bash
python 04_external_mcp_server/external_mcp_client.py
```

## Advantages

✅ **Separation of Concerns**
- Server and client are independent
- Server can serve multiple clients
- Client doesn't manage server lifecycle

✅ **Scalability**
- Server can be deployed separately
- Can run on different machines
- Load balancing possible

✅ **Reliability**
- Server keeps running between client sessions
- Client crashes don't affect server
- Server can be monitored/restarted independently

✅ **Production Ready**
- Standard HTTP/SSE transport
- Can be containerized
- Works with reverse proxies

✅ **Development Friendly**
- Start server once, use many times
- Easier debugging
- Faster iteration

## Comparison with Stage 03

| Aspect | Stage 03 (stdio) | Stage 04 (HTTP/SSE) |
|--------|------------------|---------------------|
| **Server Location** | Inside client script | Separate process |
| **Connection** | stdio (local only) | HTTP/SSE (network) |
| **Lifecycle** | Tied to client | Independent |
| **Clients** | One at a time | Multiple concurrent |
| **Deployment** | Single machine | Distributed possible |
| **Network** | Local only | Can be remote |
| **Production** | ✅ | ✅✅✅ |

## When to Use This Stage

- ✅ **Production Deployment**: Server needs to run independently
- ✅ **Multiple Clients**: Several clients connect to same server
- ✅ **Distributed Systems**: Server and clients on different machines
- ✅ **Container Deployment**: Docker, Kubernetes, etc.
- ✅ **Long-Running Server**: Server stays up between client sessions

## Running the Example

### Prerequisites

```bash
# Install dependencies (same as Stage 03)
pip install -r ../requirements-examples.txt

# Set environment variables
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Step 1: Start the Server (Terminal 1)

```bash
# From the repository root
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/nanda-registry"
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080
```

You should see FastMCP starting the server:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

**What this does:**
- `python -m fastmcp run` - Runs the FastMCP CLI
- `src/agent_mcp.py` - Path to your MCP server file
- `--transport sse` - Use HTTP/SSE transport instead of stdio
- `--port 8080` - Listen on port 8080

The server is now running at `http://localhost:8080/sse` and waiting for client connections.

### Step 2: Run the Client (Terminal 2)

```bash
# From the repository root
export ANTHROPIC_API_KEY="sk-ant-..."
python examples/04_external_mcp_server/external_mcp_client.py

# Or specify a custom server URL
python examples/04_external_mcp_server/external_mcp_client.py --server-url http://localhost:3000/sse
```

The client will connect to the server running in Terminal 1.

### Example Session

**Terminal 1 (Server)**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)

[Server logs appear here as requests come in]
INFO:     127.0.0.1:56789 - "GET /sse HTTP/1.1" 200 OK
```

**Terminal 2 (Client)**:
```
======================================================================
External MCP Server - A2A Agent Communication
======================================================================

🔗 Connecting to MCP server at http://localhost:8080/sse...
✓ Connected to external NANDA Registry MCP server
✓ Available MCP tools: 8

Connected to external MCP server!
Claude can discover agents via MCP and communicate via A2A.

Examples:
  - 'Ask agent data-scientist-761966 to list its capabilities'
  - 'Tell financial-analyst-001 to analyze my portfolio'

You: What agents are registered?

💬 User: What agents are registered?

🔧 Claude is using tools (iteration 1)...
   Calling: list_agents({})
   ✓ Result: Found 3 agents...

🤖 Claude: I found 3 registered agents:
[... agent details ...]
```

## Key Differences from Stage 03

### Connection Setup

**Stage 03 (stdio)**:
```python
from mcp.client.stdio import stdio_client

# Start server as subprocess
server_params = StdioServerParameters(
    command="python",
    args=["src/agent_mcp.py"],
    env={"ATLAS_URL": atlas_url}
)

stdio_context = stdio_client(server_params)
read, write = await stdio_context.__aenter__()
```

**Stage 04 (HTTP/SSE)**:
```python
from mcp.client.sse import sse_client

# Connect to running server
mcp_server_url = "http://localhost:8080/sse"

sse_client = sse_client(mcp_server_url)
read, write = await sse_client.__aenter__()
```

### Server Startup

**Stage 03**:
- Server starts automatically when client runs
- Server stops when client exits
- One server per client

**Stage 04**:
- Server starts manually in separate terminal
- Server keeps running after client exits
- One server serves multiple clients

## Production Deployment

### Docker Deployment

**Dockerfile for Server**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/agent_mcp.py src/

ENV ATLAS_URL=""
EXPOSE 8080

CMD ["python", "-m", "fastmcp", "run", "src/agent_mcp.py", \
     "--transport", "sse", "--port", "8080"]
```

**Dockerfile for Client**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-examples.txt .
RUN pip install -r requirements-examples.txt

COPY examples/04_external_mcp_server/external_mcp_client.py .

ENV ANTHROPIC_API_KEY=""
ENV MCP_SERVER_URL="http://mcp-server:8080/sse"

CMD ["python", "external_mcp_client.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.server
    ports:
      - "8080:8080"
    environment:
      - ATLAS_URL=${ATLAS_URL}
    restart: unless-stopped

  client:
    build:
      context: .
      dockerfile: Dockerfile.client
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - MCP_SERVER_URL=http://mcp-server:8080/sse
    depends_on:
      - mcp-server
```

### Kubernetes Deployment

**Server Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: nanda/mcp-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: ATLAS_URL
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: atlas-url
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
spec:
  selector:
    app: mcp-server
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

## Configuration Options

### Server Port
```bash
# Default port 8080
python start_mcp_server.py

# Custom port
python start_mcp_server.py --port 3000
```

### Client Connection
```python
# Local server
agent = ExternalMCPAgent(
    mcp_server_url="http://localhost:8080/sse"
)

# Remote server
agent = ExternalMCPAgent(
    mcp_server_url="http://mcp-server.example.com:8080/sse"
)

# With authentication (if implemented)
agent = ExternalMCPAgent(
    mcp_server_url="http://mcp-server.example.com:8080/sse",
    auth_token="your-token-here"
)
```

## Troubleshooting

### "Failed to connect to MCP server"

**Problem**: Client can't reach server

**Solutions**:
1. Check server is running:
   ```bash
   # In Terminal 1, you should see server logs
   ```

2. Verify port is correct:
   ```bash
   # Client default: http://localhost:8080/sse
   # Server default: port 8080
   ```

3. Check firewall:
   ```bash
   # Make sure port 8080 is open
   ```

### "Server crashes"

**Problem**: Server exits unexpectedly

**Solutions**:
1. Check environment variables:
   ```bash
   echo $ATLAS_URL
   ```

2. Check MongoDB connection:
   ```bash
   # Verify MongoDB is accessible
   ```

3. Check logs for errors

### "Connection refused"

**Problem**: Network issue

**Solutions**:
1. Ensure server is running
2. Check correct host/port
3. Verify no firewall blocking
4. Try `127.0.0.1` instead of `localhost`

## Monitoring

### Server Health Check
```bash
# Use the health_check tool via client
You: Check the server health

# Or directly via HTTP
curl http://localhost:8080/health
```

### Server Logs
```bash
# Server logs appear in Terminal 1
# Monitor for errors, requests, performance
```

### Metrics (Future Enhancement)
- Request count
- Response time
- Error rate
- Active connections

## Security Considerations

### Production Checklist

- [ ] Use HTTPS instead of HTTP
- [ ] Implement authentication (API keys, OAuth)
- [ ] Add rate limiting
- [ ] Enable CORS properly
- [ ] Use environment variables for secrets
- [ ] Monitor access logs
- [ ] Set up alerts
- [ ] Use reverse proxy (nginx, Caddy)

### Example with nginx

```nginx
server {
    listen 80;
    server_name mcp.example.com;

    location /sse {
        proxy_pass http://localhost:8080/sse;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        
        # SSE specific
        proxy_buffering off;
        proxy_cache off;
    }
}
```

## Next Steps

1. **Deploy to Cloud**: AWS, GCP, Azure
2. **Add Authentication**: Secure your server
3. **Implement Monitoring**: Track performance
4. **Scale Horizontally**: Multiple server instances
5. **Add Caching**: Improve performance
6. **Implement Webhooks**: Event-driven architecture

## Learn More

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [SSE (Server-Sent Events)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [HTTP vs stdio transports](https://modelcontextprotocol.io/docs/concepts/transports)

## Progression

```
Stage 01: Regex extraction
    ↓
Stage 02: Native tool calling
    ↓
Stage 03: A2A communication (stdio)
    ↓
Stage 04: External server (HTTP/SSE) ✓ You are here
```

---

**Previous Stage**: [Stage 03 - A2A Agent Communication](../03_a2a_agent_communication/README.md)

**Main Examples**: [Examples Overview](../README.md)
