# Stage 03: A2A Agent Communication

## Overview

This stage demonstrates **complete agent coordination** by combining MCP for discovery with A2A protocol for actual agent-to-agent communication.

## Concept

Build upon Stage 02's native tool calling and add the ability to actually communicate with discovered agents using the A2A protocol.

## Pattern

```
User Input: "Ask agent-123 to analyze this data"
     ↓
Claude calls get_agent (MCP) → Gets agent URL
     ↓
Claude calls send_a2a_message (Local) → Sends message via A2A
     ↓
Agent responds via A2A protocol
     ↓
Claude formats response for user
```

## Key Improvement over Stage 02

**Stage 02 (Discovery Only)**:
```python
# Can only query the registry
"What agents are available?"
"Get details for agent-123"
# ❌ Cannot actually talk to agents
```

**Stage 03 (Discovery + Communication)**:
```python
# Can discover AND communicate
"Ask agent-123 to analyze this data"
"Tell the financial agent to process my request"
# ✅ Full agent coordination!
```

## Architecture

```
User Request
     ↓
Claude (Orchestrator)
     ↓
     ├─→ MCP Tools (Discovery)
     │   └─→ MongoDB Registry
     │       └─→ Returns agent URL
     │
     └─→ Local Tools (Communication)
         └─→ A2A Protocol
             └─→ Target Agent
                 └─→ Returns response
```

## Files

### `a2a_agent_communication.py` ⭐⭐⭐ **RECOMMENDED**
**Purpose**: Complete agent coordination with MCP + A2A

**Features**:
- Native MCP tool calling (from Stage 02)
- A2A protocol integration for agent communication
- Multi-protocol coordination (MCP + A2A)
- Natural language queries
- Context-aware conversations
- Interactive chat mode
- ~400 lines of code

**Use Case**: Production multi-agent systems

**Example**:
```bash
python 03_a2a_agent_communication/a2a_agent_communication.py

You: Ask agent data-scientist-001 to explain clustering

🔧 Claude calls get_agent...
   ✓ Found agent at https://ds-agent.example.com

📡 Sending A2A message...
   ✓ Received response from agent

🤖 Claude: I asked the Data Science Expert agent about 
clustering. They explained: "Clustering is a technique..."
```

## Two Types of Tools

### MCP Tools (Registry Operations)
Provided by the MCP server for agent discovery:

```python
- register_agent
- list_agents
- search_agents
- get_agent          ← Returns agent URL
- update_agent
- delete_agent
- get_agent_facts
- health_check
```

### Local Tools (Communication Operations)
Handled by Python code, not in MCP server:

```python
- send_a2a_message   ← Communicates with agent
```

**Why separate?**
- MCP = Database operations (registry)
- Local = Protocol operations (HTTP/A2A)
- Clean separation of concerns

## How It Works

### 1. Tool Definition
```python
def get_local_tools(self) -> list[dict]:
    return [
        {
            "name": "send_a2a_message",
            "description": "Send message to agent via A2A protocol",
            "input_schema": {
                "type": "object",
                "properties": {
                    "agent_url": {"type": "string"},
                    "message": {"type": "string"},
                    "context_id": {"type": "string"}
                }
            }
        }
    ]
```

### 2. A2A Communication
```python
async def send_a2a_message(self, agent_url, message, context_id=None):
    # 1. Normalize URL (add /a2a if needed)
    base_url = agent_url.replace('/a2a', '')
    
    # 2. Get agent card
    resolver = A2ACardResolver(httpx_client=self.httpx_client, base_url=base_url)
    agent_card = await resolver.get_agent_card()
    
    # 3. Create A2A client
    client = A2AClient(httpx_client=self.httpx_client, agent_card=agent_card, url=base_url)
    
    # 4. Prepare message
    message_obj = Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=message))],
        message_id=str(uuid4()),
        context_id=context_id
    )
    
    # 5. Send message
    params = MessageSendParams(message=message_obj)
    request = SendMessageRequest(id=str(uuid4()), params=params)
    response = await client.send_message(request)
    
    return response
```

### 3. Orchestration
```python
# Claude sees both MCP and local tools
all_tools = mcp_tools + local_tools

response = anthropic.messages.create(
    tools=all_tools,
    messages=[...]
)

# Handle tool calls
if tool_name == "send_a2a_message":
    # Local tool - handle directly
    result = await self.send_a2a_message(...)
else:
    # MCP tool - call via MCP session
    result = await session.call_tool(tool_name, arguments)
```

## Documentation Files

### `A2A_COMMUNICATION.md`
Comprehensive guide to A2A agent communication patterns, workflows, and examples.

### `A2A_ARCHITECTURE.txt`
Visual ASCII diagrams showing the complete architecture with MCP + A2A integration.

### `QUICKSTART_A2A.md`
Quick start guide with step-by-step instructions and troubleshooting.

## When to Use This Stage

- ✅ **Agent Communication**: Need to actually talk to agents
- ✅ **Multi-Agent Workflows**: Coordinating multiple agents
- ✅ **Production Systems**: Complete agent coordination
- ✅ **A2A Protocol**: Working with A2A-compliant agents

## Running the Example

### Prerequisites
```bash
# Install dependencies (includes a2a-sdk)
pip install -r ../requirements-examples.txt

# Set environment variables
export ATLAS_URL="mongodb+srv://..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Interactive Mode
```bash
python 03_a2a_agent_communication/a2a_agent_communication.py

# Choose option 1 for chat mode
# Ask questions like:
# - "Ask agent data-scientist-001 to explain ML"
# - "Tell the financial agent to analyze my portfolio"
# - "Request from marketing-agent to create a campaign"
```

## Key Concepts Demonstrated

1. **Multi-Protocol Integration**: MCP + A2A working together
2. **Tool Type Separation**: Server tools vs. local tools
3. **Agent Discovery**: Using MCP to find agents
4. **Agent Communication**: Using A2A to message agents
5. **Complete Orchestration**: Claude coordinates the entire workflow

## Example Session

```
═══════════════════════════════════════════════════════════
A2A-Aware Claude - Agent Communication via A2A Protocol
═══════════════════════════════════════════════════════════

✓ Connected to NANDA Registry MCP server
✓ Available MCP tools: 8

Examples:
  - 'Ask agent data-scientist-001 to list its capabilities'
  - 'Tell financial-analyst-001 to analyze my portfolio'

You: What agents are available?

🔧 Claude is using tools (iteration 1)...
   Calling: list_agents({})
   ✓ Result: Found 3 agents

🤖 Claude: I found 3 registered agents:

1. data-scientist-001 - Data Science Expert
2. financial-analyst-001 - Financial Analysis Agent
3. marketing-agent-123 - Marketing Campaign Manager

You: Ask the data scientist to explain machine learning

🔧 Claude is using tools (iteration 1)...
   Calling: get_agent({"agent_id": "data-scientist-001"})
   ✓ Result: Found agent at https://ds-agent.example.com

🔧 Claude is using tools (iteration 2)...
   Calling: send_a2a_message({
     "agent_url": "https://ds-agent.example.com",
     "message": "Please explain machine learning"
   })

📡 Sending A2A message to: https://ds-agent.example.com/a2a
   Message: Please explain machine learning...
   ✓ Got agent card: Data Science Expert
   ✓ Received response from agent

🤖 Claude: I asked the Data Science Expert agent about machine 
learning. They provided this explanation:

"Machine learning is a subset of artificial intelligence that 
enables systems to learn and improve from experience without 
being explicitly programmed. There are three main types:

1. Supervised Learning - Learning from labeled examples
2. Unsupervised Learning - Finding patterns in unlabeled data
3. Reinforcement Learning - Learning through trial and error

Common techniques include neural networks, decision trees, and 
clustering algorithms like k-means."

You: Ask them to give me a code example

🔧 Claude is using tools (iteration 1)...
   Calling: send_a2a_message({
     "agent_url": "https://ds-agent.example.com",
     "message": "Can you provide a code example?",
     "context_id": "previous-conversation-id"
   })

📡 Sending A2A message...
   ✓ Received response from agent

🤖 Claude: The agent provided this code example:

```python
from sklearn.cluster import KMeans
import numpy as np

# Sample data
X = np.array([[1, 2], [1, 4], [1, 0],
              [10, 2], [10, 4], [10, 0]])

# Create and fit model
kmeans = KMeans(n_clusters=2, random_state=0)
kmeans.fit(X)

# Predict clusters
labels = kmeans.labels_
print(labels)  # [0 0 0 1 1 1]
```
```

## Use Cases

### 1. Agent Consultation
```
"Ask the financial analyst agent for investment advice"
→ Discovers agent → Sends question → Returns advice
```

### 2. Multi-Agent Workflow
```
"Find a data scientist and ask them to analyze this dataset"
→ Searches → Gets top agent → Sends data → Returns analysis
```

### 3. Agent Capability Discovery
```
"Ask agent-123 what it can do"
→ Gets agent info → Asks capabilities → Returns list
```

### 4. Sequential Agent Tasks
```
"Ask agent-001 to analyze data, then ask agent-002 to visualize it"
→ Two-step workflow with different agents
```

## Comparison with Previous Stages

| Feature | Stage 01 | Stage 02 | Stage 03 |
|---------|----------|----------|----------|
| **Pattern** | Manual regex | Native MCP | Native MCP + A2A |
| **Syntax** | @agent-name | Natural | Natural |
| **Discovery** | ✅ | ✅ | ✅ |
| **Communication** | ❌ | ❌ | ✅ |
| **Protocols** | MCP | MCP | MCP + A2A |
| **Production** | ❌ | ✅ | ✅ |
| **Flexibility** | Low | High | Highest |

## A2A Protocol Details

### Message Structure
```python
Message(
    role=Role.user,
    parts=[Part(root=TextPart(text="Your message"))],
    message_id="uuid",
    context_id="optional-conversation-id"
)
```

### Protocol Flow
```
1. Get Agent Card (/.well-known/agent.json)
   └─> Agent metadata and capabilities

2. Create A2A Client
   └─> Initialize with httpx and agent card

3. Send Message (POST /a2a)
   └─> SendMessageRequest with Message

4. Receive Response
   └─> SendMessageResponse with agent's reply
```

## Dependencies

```txt
# Core dependencies
fastmcp>=2.0.0
pymongo>=4.6.0
anthropic>=0.7.0
mcp>=1.0.0

# A2A protocol (new in Stage 03)
a2a-sdk>=0.1.0
httpx>=0.27.0
```

## Learn More

- [A2A_COMMUNICATION.md](./A2A_COMMUNICATION.md) - Complete guide
- [A2A_ARCHITECTURE.txt](./A2A_ARCHITECTURE.txt) - Visual diagrams
- [QUICKSTART_A2A.md](./QUICKSTART_A2A.md) - Quick start guide
- [A2A Protocol](https://github.com/a2aproject)
- [MCP Documentation](https://modelcontextprotocol.io/)

## Progression

```
Stage 01: Regex extraction
    ↓
Stage 02: Native tool calling
    ↓
Stage 03: A2A communication (You are here) ✓
```

---

**Previous Stage**: [Stage 02 - MCP Tool Calling](../02_mcp_tool_calling/README.md)

**Next Stage**: [Stage 03 - External MCP Server](../04_external_mcp_server/README.md)
