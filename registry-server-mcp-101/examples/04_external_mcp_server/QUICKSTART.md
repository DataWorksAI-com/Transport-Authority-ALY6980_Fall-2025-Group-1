# Stage 04 Quick Start Guide

## 🚀 Get Started in 2 Minutes

### What You'll Do

Run the MCP server in one terminal, and connect to it from a client in another terminal.

## Prerequisites

```bash
# 1. Install dependencies
pip install -r examples/requirements-examples.txt

# 2. Set environment variables
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/nanda-registry"
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Two Terminal Workflow

### Terminal 1: Start the Server

```bash
# From the repository root directory
cd /path/to/registry-server

# Start the MCP server with FastMCP CLI
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

✅ **Server is now running!** Leave this terminal open.

### Terminal 2: Run the Client

Open a **new terminal** window:

```bash
# From the repository root directory
cd /path/to/registry-server

# Run the client
python examples/04_external_mcp_server/external_mcp_client.py
```

**Expected output:**
```
======================================================================
External MCP Server - A2A Agent Communication
======================================================================

🔗 Connecting to MCP server at http://localhost:8080/sse...
✓ Connected to external NANDA Registry MCP server
✓ Available MCP tools: 8

Connected to external MCP server!
Claude can discover agents via MCP and communicate via A2A.

You: 
```

✅ **Client connected!** You can now chat with Claude.

## Try These Queries

```
You: What agents are registered?
You: Tell me about the financial analyst agent
You: Ask agent-123 to explain its capabilities
You: Search for data science agents
```

## What's Happening?

```
Terminal 1 (Server)              Terminal 2 (Client)
┌─────────────────┐             ┌─────────────────┐
│ FastMCP CLI     │             │ Claude Client   │
│                 │   HTTP/SSE  │                 │
│ agent_mcp.py    │◄────────────┤ MCP Connection  │
│                 │             │                 │
│ MongoDB Atlas   │             │ A2A Protocol    │
│ (8 tools)       │             │                 │
└─────────────────┘             └─────────────────┘
```

**Key Points:**
- Server runs continuously (doesn't restart with client)
- Multiple clients can connect simultaneously
- Client can disconnect/reconnect anytime
- Server process is independent

## Stop the Server

In **Terminal 1**, press `Ctrl+C`:

```
^C
INFO:     Shutting down
INFO:     Finished server process [12345]
```

## Troubleshooting

### "Command not found: fastmcp"

**Solution:**
```bash
pip install fastmcp>=2.0.0
python -m fastmcp --help  # Verify installation
```

### "Can't find agent_mcp.py"

**Solution:** Make sure you're running from the repository root:
```bash
pwd  # Should show /path/to/registry-server
ls src/agent_mcp.py  # Should exist
```

### "Connection refused"

**Solution:** Make sure the server is running in Terminal 1 before starting the client in Terminal 2.

### "ATLAS_URL not set"

**Solution:**
```bash
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/nanda-registry"
```

### "ANTHROPIC_API_KEY not set"

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Next Steps

1. **Read the full guide**: `04_external_mcp_server/README.md`
2. **Deploy with Docker**: See README for Dockerfile examples
3. **Scale with Kubernetes**: See README for K8s manifests
4. **Compare with Stage 03**: See `STAGE_04_SUMMARY.md`

## Command Reference

### Start Server (Terminal 1)
```bash
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080
```

### Run Client (Terminal 2)
```bash
python examples/04_external_mcp_server/external_mcp_client.py

# Or connect to a custom server URL
python examples/04_external_mcp_server/external_mcp_client.py --server-url http://localhost:3000/sse
```

### Custom Port
```bash
# Server with custom port
python -m fastmcp run src/agent_mcp.py --transport sse --port 3000

# Client connects to custom port using --server-url flag
python examples/04_external_mcp_server/external_mcp_client.py \
    --server-url http://localhost:3000/sse
```

### Remote Server
```bash
# Server on remote machine
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080 --host 0.0.0.0

# Client connects to remote server (edit external_mcp_client.py line 30)
mcp_server_url = "http://remote-server.example.com:8080/sse"
```

## Benefits Over Stage 03

| Feature | Stage 03 | Stage 04 |
|---------|----------|----------|
| **Server Lifecycle** | Tied to client | Independent |
| **Multiple Clients** | ❌ | ✅ |
| **Client Restarts** | Server restarts too | Server keeps running |
| **Distributed** | Same machine only | Can be remote |
| **Scalability** | Limited | High |

## That's It! 🎉

You now have a production-ready distributed MCP deployment with:
- ✅ Independent server process
- ✅ HTTP/SSE network transport
- ✅ Support for multiple clients
- ✅ Better scalability and reliability

**Happy coding!** 🚀
