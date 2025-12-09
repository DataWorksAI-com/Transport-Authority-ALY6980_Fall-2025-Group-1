# NANDA Registry Server

A centralized registry service for discovering and managing NANDA (Network of Autonomous Distributed Agents) agents. The registry enables agents to register themselves, discover other agents by capabilities, and facilitate agent-to-agent (A2A) communication.

## What is the NANDA Registry?

The NANDA Registry is a service that provides:

- **Agent Registration**: Agents can register themselves with their capabilities, domains, and endpoints
- **Agent Discovery**: Find agents by capabilities, domains, or text search
- **AgentFacts Management**: Rich metadata storage for each agent including skills, certifications, and performance data
- **A2A Communication Support**: Provides agent URLs for direct agent-to-agent communication
- **MongoDB Persistence**: Scalable storage for agent data and facts

## Available Interfaces

The registry provides two interfaces:

1. **FastAPI REST API**: Traditional HTTP REST API for web-based integrations
2. **MCP Server**: Model Context Protocol server for AI agent integrations using FastMCP

## Examples

See the [`examples/`](examples/) directory for complete integration examples:

### Anthropic Claude Integration Examples

1. **`a2a_agent_communication.py`** ⭐ **RECOMMENDED**
   - Full agent coordination with MCP discovery + A2A protocol communication
   - Claude discovers agents via MCP tools and communicates with them via A2A
   - Natural language queries like "Ask agent-123 to analyze this data"
   - See [`A2A_COMMUNICATION.md`](examples/A2A_COMMUNICATION.md) for detailed documentation

2. **`mcp_native_tool_calling.py`** ⭐ **RECOMMENDED**
   - Proper MCP integration - lets Claude automatically call tools
   - Natural language queries without special syntax
   - Interactive chat mode with agentic loop

3. **`simple_agent_lookup.py`**
   - Minimal example showing manual pattern matching
   - Detects `@agent-name` mentions and looks up agents via MCP

4. **`anthropic_agent_example.py`**
   - Full-featured interactive agent with conversation history
   - Manual pattern matching approach (not recommended for production)

See [`examples/README.md`](examples/README.md) for complete documentation and comparisons.

## Architecture

The registry consists of three main components:

1. **Registry Server** (`agentIndex.py`): FastAPI REST API for agent registration, discovery, and management
2. **AgentFacts Server** (`agentFactsServer.py`): FastAPI REST API for serving detailed agent metadata
3. **MCP Server** (`agent_mcp.py`): FastMCP server exposing all functionality via Model Context Protocol

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NANDA Agent   │    │  Registry API   │    │ AgentFacts API  │
│                 │───▶│   (Port 6900)   │───▶│   (Port 8000)   │
│ Registers Self  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   MongoDB       │    │   MongoDB       │
                       │ (Agent Index)   │    │ (Agent Facts)   │
                       └─────────────────┘    └─────────────────┘
                                    ▲
                                    │
                       ┌────────────┴──────────┐
                       │    MCP Server         │
                       │   (agent_mcp.py)      │
                       │  FastMCP Interface    │
                       └───────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- MongoDB Atlas account or local MongoDB instance
- [uv](https://docs.astral.sh/uv/) package manager (optional, recommended)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd registry-server
```

2. **Install dependencies:**

**Using uv (recommended):**
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
source .venv/bin/activate
```

**Using pip:**
```bash
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Or install from pyproject.toml
pip install -e .
```

3. **Set up environment variables:**
```bash
export ATLAS_URL="mongodb+srv://username:password@cluster.mongodb.net/"
```

### Running the Servers

#### Option 1: FastAPI REST Servers

4. **Start the FastAPI services:**
```bash
# Start the registry server (port 6900)
python src/agentIndex.py

# In another terminal, start the AgentFacts server (port 8000)
python src/agentFactsServer.py
```

#### Option 2: MCP Server (for AI Agents)

4. **Start the MCP server:**
```bash
# Run the MCP server
uv run fastmcp run src/agent_mcp.py --transport sse --port 8080

# Alternative run using python
python src/agent_mcp.py
```

### Verify Installation

```bash
# Check registry health
curl http://localhost:6900/health

# Check AgentFacts server health
curl http://localhost:8000/health

# Check MCP server health
curl http://localhost:8080/health
```

## MCP Server (FastMCP)

The MCP server exposes all registry functionality via the Model Context Protocol, making it easy to integrate with AI agents and LLM applications.

### Available MCP Tools

The MCP server provides the following tools:

- **register_agent**: Register a new agent with the registry
- **list_agents**: List all registered agents (with optional status filter)
- **search_agents**: Search for agents by capabilities, domain, or query string
- **get_agent**: Get details for a specific agent by agent_id
- **update_agent**: Update agent information
- **delete_agent**: Delete an agent from the registry
- **get_agent_facts**: Get agent facts by username from the facts database

And one resource:
- **health://check**: Check the health status of the registry and database connections

### Using the MCP Server

#### With Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "nanda-registry": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jsolis/Code/registry-server",
        "run",
        "python",
        "src/agent_mcp.py"
      ],
      "env": {
        "ATLAS_URL": "mongodb+srv://username:password@cluster.mongodb.net/"
      }
    }
  }
}
```

#### With Other MCP Clients

The MCP server can be used with any MCP-compatible client. It communicates via stdio and follows the Model Context Protocol specification.

Example using the MCP SDK:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure server connection
server_params = StdioServerParameters(
    command="python",
    args=["src/agent_mcp.py"],
    env={"ATLAS_URL": "your-mongodb-url"}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Call MCP tools
        result = await session.call_tool("register_agent", {
            "agent_id": "my-agent-001",
            "agent_url": "http://localhost:8080",
            "capabilities": ["chat", "analysis"]
        })
        print(result)
```

### MCP Tool Examples

#### Register an Agent

```python
# Tool: register_agent
# Arguments:
{
  "agent_id": "financial-analyst-001",
  "agent_url": "http://192.168.1.100:8080",
  "capabilities": ["financial_analysis", "equity_research"],
  "domain": "finance",
  "specialization": "financial_analysis",
  "description": "Senior financial analyst with 15+ years experience"
}
```

#### Search for Agents

```python
# Tool: search_agents
# Arguments:
{
  "query": "financial"
}
```

#### Get Agent Details

```python
# Tool: get_agent
# Arguments:
{
  "agent_id": "financial-analyst-001"
}
```

## API Reference

### Registry API (Port 6900)

#### Register an Agent
```bash
POST /register
```

**Payload:**
```json
{
  "agent_id": "financial-analyst-001",
  "agent_url": "http://192.168.1.100:8080",
  "capabilities": ["financial_analysis", "equity_research", "portfolio_analysis"],
  "domain": "finance",
  "specialization": "financial_analysis",
  "description": "Senior financial analyst with 15+ years experience",
  "modalities": ["text"],
  "languages": ["en"],
  "streaming": false,
  "batch": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Agent registered successfully",
  "agent_id": "financial-analyst-001",
  "id": "507f1f77bcf86cd799439011"
}
```

#### List All Agents
```bash
GET /list
```

#### Search Agents
```bash
# Search by capabilities
GET /search?capabilities=financial_analysis,portfolio_analysis

# Search by domain
GET /search?domain=finance

# Text search
GET /search?q=financial

# Combined search
GET /search?capabilities=data_analysis&domain=finance&q=senior
```

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "financial-analyst-001",
      "agent_url": "http://192.168.1.100:8080",
      "agentFactsURL": "http://localhost:8000/@financial_analyst_001.json"
    }
  ],
  "count": 1,
  "query": {
    "capabilities": "financial_analysis",
    "domain": "finance",
    "search_term": null
  }
}
```

#### Get Specific Agent
```bash
GET /lookup/{agent_id}
```

#### Update Agent
```bash
PUT /update/{agent_id}
```

#### Delete Agent
```bash
DELETE /agents/{agent_id}
```

### AgentFacts API (Port 8000)

#### Get Agent Facts
```bash
GET /@{agent_id}.json
```

**Response:**
```json
{
  "username": "financial_analyst_001",
  "agent_name": "financial-analyst-001",
  "description": "Senior financial analyst with 15+ years experience",
  "capabilities": {
    "modalities": ["text"],
    "streaming": false,
    "batch": true
  },
  "skills": [
    {
      "id": "financial_analysis",
      "description": "Expert financial analysis capability",
      "inputModes": ["text"],
      "outputModes": ["text"],
      "supportedLanguages": ["en"],
      "latencyBudgetMs": 2000,
      "maxTokens": 4000
    }
  ],
  "evaluations": {
    "performanceScore": 92.0
  },
  "certification": {
    "level": "Certified",
    "issuer": "Your Authority"
  }
}
```

## Usage Examples

### Basic Agent Registration

```bash
curl -X POST http://localhost:6900/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "data-scientist-001",
    "agent_url": "http://192.168.1.101:8080",
    "capabilities": ["data_analysis", "machine_learning", "visualization"],
    "domain": "data_science",
    "specialization": "machine_learning",
    "description": "Expert data scientist specializing in ML model development"
  }'
```

### Agent Discovery Workflow

```bash
# 1. Find agents with specific capabilities
curl "http://localhost:6900/search?capabilities=machine_learning"

# 2. Get detailed agent information
curl http://localhost:6900/lookup/data-scientist-001

# 3. Access rich AgentFacts
curl http://localhost:8000/@data_scientist_001.json
```

### Agent-to-Agent Communication

```bash
# Agent A discovers Agent B
AGENT_B_URL=$(curl -s "http://localhost:6900/search?capabilities=financial_analysis" | jq -r '.agents[0].agent_url')

# Agent A communicates with Agent B
curl -X POST ${AGENT_B_URL}/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "text": "Can you analyze this financial report?",
      "type": "text"
    },
    "role": "user",
    "conversation_id": "analysis_session_001"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_URL` | MongoDB connection string | Required |
| `AGENT_FACTS_API_URL` | AgentFacts creation endpoint | `https://join39.org/api/public-agent-facts` |
| `AGENT_FACTS_BASE_URL` | AgentFacts retrieval base URL | `https://list39.org` |

### Switching to Local AgentFacts Storage

By default, the registry uses external services (`list39.org`) for AgentFacts storage. To use local storage:

#### Option 1: Environment Variables (Recommended)

```bash
export AGENT_FACTS_API_URL="http://localhost:8000/api/agent-facts"
export AGENT_FACTS_BASE_URL="http://localhost:8000"
```

#### Option 2: Code Modification

Update lines 88-109 in `src/agentIndex.py`:

```python
# Replace hardcoded URLs with local endpoints
AGENT_FACTS_API_URL = os.getenv("AGENT_FACTS_API_URL", "http://localhost:8000/api/agent-facts")
AGENT_FACTS_BASE_URL = os.getenv("AGENT_FACTS_BASE_URL", "http://localhost:8000")
```

#### Add POST Endpoint to AgentFactsServer

Add this to `src/agentFactsServer.py`:

```python
@app.post("/api/agent-facts")
def create_agent_facts(agent_facts: dict):
    """Create new agent facts"""
    try:
        result = facts.insert_one(agent_facts)
        return {
            "status": "success", 
            "message": "Agent facts created successfully",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent facts: {str(e)}")
```

### Benefits of Local Storage

- **Privacy**: Complete control over agent data
- **Performance**: Faster access without external API calls
- **Customization**: Modify agent facts schema as needed
- **Offline Operation**: Works without internet connectivity

## Deployment

[Registry Deployment Documentation](deploy/README.md)

