# Getting Started with A2A Agent Communication

## Overview

The `a2a_agent_communication.py` example demonstrates the **complete agent coordination workflow** by combining:
- **MCP Protocol** for agent discovery (via the NANDA Registry)
- **A2A Protocol** for agent-to-agent communication

This is the most sophisticated example, showing how Claude can orchestrate multi-agent interactions naturally.

## What You Need

### 1. Environment Variables
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/"
```

### 2. Dependencies
```bash
# Install all required packages
uv pip install -r examples/requirements-examples.txt
```

### 3. Running MCP Server
The example will start the MCP server automatically, but it needs to be accessible:
```bash
# Ensure src/agent_mcp.py is in the expected location
ls src/agent_mcp.py
```

## How to Run

### Interactive Chat Mode (Recommended)
```bash
python examples/a2a_agent_communication.py
```

Then select option `1` for interactive chat.

### Example Queries
```bash
# Discovery queries (MCP tools only)
"What agents are currently registered?"
"Search for data science agents"
"Get details for agent financial-analyst-001"

# Communication queries (MCP + A2A)
"Ask agent data-scientist-001 to list its capabilities"
"Tell financial-analyst-001 to analyze my portfolio"
"Request from marketing-agent-123 to create a campaign"
```

## How It Works

### User Query
```
"Ask agent data-scientist-001 to explain clustering algorithms"
```

### Claude's Workflow

**Step 1: Agent Discovery (MCP)**
```python
# Claude calls the MCP tool
get_agent(agent_id="data-scientist-001")

# Returns:
{
  "agent_id": "data-scientist-001",
  "name": "Data Science Expert",
  "url": "https://ds-agent.example.com",
  "tags": ["data-science", "ml"],
  ...
}
```

**Step 2: A2A Communication**
```python
# Claude calls the local tool
send_a2a_message(
  agent_url="https://ds-agent.example.com",
  message="Explain clustering algorithms"
)

# This code:
# 1. Adds /a2a to URL → https://ds-agent.example.com/a2a
# 2. Fetches agent card from /.well-known/agent.json
# 3. Creates A2A client
# 4. Sends message via A2A protocol
# 5. Returns agent's response
```

**Step 3: Response**
```
Claude: "I asked the Data Science Expert agent about clustering. 
They explained: Clustering is a technique for grouping..."
```

## Architecture

```
User Request
     ↓
Claude (decides what to do)
     ↓
     ├─→ MCP Tools (discovery)
     │   └─→ MongoDB Registry
     │
     └─→ Local Tools (communication)
         └─→ A2A Protocol
             └─→ Target Agent
```

## Key Features

### 1. Natural Language
No special syntax required. Claude understands intent:
- ❌ Old: `@agent-name do something`
- ✅ New: `Ask agent-name to do something`

### 2. Multi-Protocol
- **MCP**: Standardized tool calling for discovery
- **A2A**: Standardized messaging for communication

### 3. Flexible Workflows
Claude can chain multiple operations:
```
"Find all data science agents and ask the best one about ML"
  1. search_agents(tags=["data-science"])
  2. get_agent(agent_id=results[0].id)
  3. send_a2a_message(url=agent.url, message="Tell me about ML")
```

### 4. Context Management
Multi-turn conversations with the same agent:
```python
# First message
send_a2a_message(
  agent_url=url,
  message="Analyze this data",
  context_id="conv-123"
)

# Follow-up (same context)
send_a2a_message(
  agent_url=url,
  message="Focus on outliers",
  context_id="conv-123"  # Same context
)
```

## Tool Types

### MCP Tools (from server)
These are exposed by the MCP server:
- `register_agent`
- `list_agents`
- `search_agents`
- `get_agent` ← Returns agent URL
- `update_agent`
- `delete_agent`
- `get_agent_facts`
- `health_check`

### Local Tools (handled by Python)
These are NOT in the MCP server:
- `send_a2a_message` ← Communicates with agent

**Why separate?**
- MCP = Registry operations (database)
- Local = Protocol operations (HTTP/A2A)
- Clear separation of concerns

## Example Session

```
A2A-Aware Claude - Agent Communication via A2A Protocol
======================================================================

Claude can discover agents via MCP and communicate with them via A2A!

Examples:
  - 'Ask agent data-scientist-001 to list its capabilities'
  - 'Tell financial-analyst-001 to analyze my portfolio'

Type 'quit' or 'exit' to end the conversation.

You: What agents are available?

🔧 Claude is using tools (iteration 1)...
   Calling: list_agents({})
   ✓ Result: Found 3 agents

🤖 Claude: I found 3 registered agents:

1. **data-scientist-001** - Data Science Expert
   • Tags: data-science, machine-learning
   • URL: https://ds-agent.example.com

2. **financial-analyst-001** - Financial Analysis Agent
   • Tags: finance, analysis
   • URL: https://finance-agent.example.com

3. **marketing-agent-123** - Marketing Campaign Manager
   • Tags: marketing, campaigns
   • URL: https://marketing-agent.example.com

You: Ask the data scientist to explain machine learning

🔧 Claude is using tools (iteration 1)...
   Calling: get_agent({"agent_id": "data-scientist-001"})
   ✓ Result: Found agent at https://ds-agent.example.com

🔧 Claude is using tools (iteration 2)...
   Calling: send_a2a_message({"agent_url": "https://ds-agent.example.com", ...})

📡 Sending A2A message to: https://ds-agent.example.com/a2a
   Message: Please explain machine learning concepts...
   ✓ Got agent card: Data Science Expert
   ✓ Received response from agent

🤖 Claude: I asked the Data Science Expert agent about machine learning. 
They provided this explanation:

"Machine learning is a subset of artificial intelligence that enables 
systems to learn and improve from experience without being explicitly 
programmed. There are three main types:

1. Supervised Learning - Learning from labeled examples
2. Unsupervised Learning - Finding patterns in unlabeled data
3. Reinforcement Learning - Learning through trial and error

Common techniques include neural networks, decision trees, and 
clustering algorithms like k-means."

You: quit

Goodbye! 👋
```

## Troubleshooting

### "Missing required environment variables"
```bash
# Set both required variables
export ANTHROPIC_API_KEY="sk-ant-..."
export ATLAS_URL="mongodb+srv://..."
```

### "Could not connect to agent"
- Check that the agent URL is correct
- Verify the agent is running and accessible
- Ensure the agent implements the A2A protocol

### "Module not found: a2a"
```bash
# Install the A2A SDK
uv add a2a-sdk
# or
pip install a2a-sdk
```

### "Python version too old"
```bash
# Requires Python 3.10+
python3 --version

# Use uv to manage Python versions
uv python install 3.12
```

## Learn More

- **Architecture**: See [`A2A_ARCHITECTURE.txt`](A2A_ARCHITECTURE.txt) for visual diagrams
- **Deep Dive**: See [`A2A_COMMUNICATION.md`](A2A_COMMUNICATION.md) for detailed explanation
- **Examples**: See [`README.md`](README.md) for all example comparisons
- **MCP Protocol**: https://modelcontextprotocol.io/
- **A2A Protocol**: https://github.com/a2aproject
- **Anthropic**: https://docs.anthropic.com/

## Next Steps

1. **Try it out**: Run the interactive chat and experiment with queries
2. **Add agents**: Register more agents in your registry
3. **Extend**: Add more local tools for advanced coordination
4. **Deploy**: Connect to production agent endpoints

## Tips

- Start with simple discovery queries before trying communication
- Use natural language - Claude understands intent
- Check agent logs if A2A messages fail
- Use context IDs for multi-turn agent conversations
- Monitor tool calls with the printed output
