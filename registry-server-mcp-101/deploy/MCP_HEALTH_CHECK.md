# MCP Server Health Check

## Important Note

The MCP (Model Context Protocol) server running on port 8080 does **NOT** have a traditional REST `/health` endpoint like the FastAPI services.

MCP is a protocol for AI model communication, not a REST API. It uses Server-Sent Events (SSE) for communication.

## How to Check MCP Service Health

### Option 1: Check if Port is Open (Recommended for Monitoring)

```bash
# Using netcat
nc -z -w5 45.79.190.57 8080 && echo "MCP server is running"

# Using curl (will get 404 but connection succeeds)
curl -s http://45.79.190.57:8080/ && echo "MCP server is responding"
```

### Option 2: Check Systemd Service Status

```bash
ssh -i nanda-registry-key root@45.79.190.57 'systemctl status nanda-agent-mcp'
```

### Option 3: Check Service Logs

```bash
ssh -i nanda-registry-key root@45.79.190.57 'journalctl -u nanda-agent-mcp -n 50'
```

### Option 4: Use MCP Client to Call health_check Tool

The MCP server exposes a `health_check` tool that can be called via MCP protocol:

```bash
# Using the external MCP client
cd examples/04_external_mcp_server
python external_mcp_client.py --server-url http://45.79.190.57:8080/sse

# Then in the client, call:
# health_check()
```

## Service Endpoints Summary

| Service | Port | Health Check Method |
|---------|------|-------------------|
| Agent Index | 6900 | `curl http://IP:6900/health` |
| Agent Facts | 8000 | `curl http://IP:8000/health` |
| Agent MCP | 8080 | `nc -z IP 8080` or use MCP client |

## Why No /health Endpoint for MCP?

MCP servers communicate via:
1. **SSE (Server-Sent Events)** - For streaming responses
2. **MCP Protocol** - Specific message format for tool calls

They don't expose traditional REST endpoints. The `/health` endpoint would be meaningless in MCP context.

## Monitoring Solutions

### 1. Port Check (Simple)
```bash
#!/bin/bash
if nc -z -w5 45.79.190.57 8080; then
    echo "MCP server UP"
else
    echo "MCP server DOWN"
fi
```

### 2. Service Status (More Reliable)
```bash
#!/bin/bash
ssh -i nanda-registry-key root@45.79.190.57 \
  'systemctl is-active --quiet nanda-agent-mcp && echo "UP" || echo "DOWN"'
```

### 3. MCP Protocol Check (Most Thorough)
Use the MCP client to actually call the `health_check` tool and verify MongoDB connectivity.

## Docker/Kubernetes Health Checks

In the deployment configurations:

**Docker**: Uses port check via `netstat` or `ss`
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "netstat -tln | grep 8080 || ss -tln | grep 8080"]
```

**Kubernetes**: Uses TCP socket probe
```yaml
livenessProbe:
  tcpSocket:
    port: 8080
```

These check if the port is listening, which is sufficient for service health.

## Testing MCP Server Functionality

To actually test if the MCP server is working:

```python
# examples/test_mcp_health.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def check_mcp_health():
    server_params = StdioServerParameters(
        command="fastmcp",
        args=["run", "src/agent_mcp.py", "--transport", "sse"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call health_check tool
            result = await session.call_tool("health_check", {})
            print(f"Health check result: {result}")
            return result

if __name__ == "__main__":
    asyncio.run(check_mcp_health())
```

## Conclusion

✅ **For FastAPI services (6900, 8000)**: Use `curl http://IP:PORT/health`

✅ **For MCP service (8080)**: Use `nc -z IP 8080` or check systemd status

🔧 **For detailed MCP health**: Use MCP client to call `health_check` tool
