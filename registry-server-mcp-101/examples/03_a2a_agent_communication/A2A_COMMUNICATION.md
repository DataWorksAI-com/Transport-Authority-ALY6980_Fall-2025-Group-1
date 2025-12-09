# A2A Agent Communication Pattern

## The Complete Agent Coordination Stack

This example demonstrates the **full stack** of agent coordination in the NANDA ecosystem:

```
User Request
    ↓
Claude (Anthropic)
    ↓
MCP Tools (Discovery)  ←→  A2A Protocol (Communication)
    ↓                           ↓
Registry Database          Target Agent
```

## Architecture

### Layer 1: MCP Tools (Agent Discovery)
- **Purpose**: Find and look up agents in the registry
- **Tools**: `get_agent`, `search_agents`, `list_agents`
- **Returns**: Agent metadata including URL

### Layer 2: A2A Protocol (Agent Communication)
- **Purpose**: Actually communicate with the discovered agent
- **Method**: HTTP/HTTPS with A2A protocol messages
- **Returns**: Agent's response to your request

### Layer 3: Claude Integration
- **Purpose**: Orchestrate the entire flow naturally
- **Approach**: Claude decides when to discover vs. communicate
- **Result**: Seamless multi-agent interaction

## How It Works

### Example Query
```
User: "Ask agent data-scientist-001 to explain clustering algorithms"
```

### Step-by-Step Flow

1. **Claude receives the query**
   - Sees available tools: MCP tools + `send_a2a_message`
   - Understands the user wants to communicate with a specific agent

2. **Agent Discovery (MCP)**
   ```
   Claude calls: get_agent(agent_id="data-scientist-001")
   
   MCP returns: {
     "agent_id": "data-scientist-001",
     "name": "Data Science Expert",
     "url": "https://ds-agent.example.com",
     ...
   }
   ```

3. **A2A Communication**
   ```
   Claude calls: send_a2a_message(
     agent_url="https://ds-agent.example.com",
     message="Explain clustering algorithms"
   )
   
   Code:
   - Appends "/a2a" to URL if needed
   - Fetches agent card from the agent
   - Creates A2A client
   - Sends message via A2A protocol
   - Returns agent's response
   ```

4. **Response Integration**
   ```
   Claude receives the A2A response and formats it:
   
   "I asked the Data Science Expert agent about clustering algorithms. 
   Here's what they said: [agent response]"
   ```

## Key Patterns

### Pattern 1: Single Agent Communication
```python
# User query
"Ask financial-analyst-001 to analyze my portfolio"

# Claude's tool calls
1. get_agent(agent_id="financial-analyst-001")
2. send_a2a_message(agent_url=result.url, message="Analyze portfolio")
```

### Pattern 2: Multi-Agent Workflow
```python
# User query
"Find all data science agents and ask the top one about machine learning"

# Claude's tool calls
1. search_agents(tags=["data-science"])
2. get_agent(agent_id=results[0].agent_id)
3. send_a2a_message(agent_url=result.url, message="Tell me about ML")
```

### Pattern 3: Context-Aware Conversations
```python
# User query 1
"Ask agent-123 to analyze this data"

# Claude calls
context_id = generate_uuid()
send_a2a_message(agent_url=url, message="Analyze this data", context_id=context_id)

# User query 2 (follow-up)
"Ask them to focus on outliers"

# Claude calls (same context)
send_a2a_message(agent_url=url, message="Focus on outliers", context_id=context_id)
```

## Tool Design

### MCP Tools (Provided by Server)
These are defined in `src/agent_mcp.py` and exposed via MCP:

```python
- register_agent
- list_agents
- search_agents
- get_agent
- update_agent
- delete_agent
- get_agent_facts
- health_check
```

### Local Tools (Handled by Python Code)
These are NOT in the MCP server - handled locally in the example:

```python
{
  "name": "send_a2a_message",
  "description": "Send a message to an agent using the A2A protocol...",
  "input_schema": {
    "type": "object",
    "properties": {
      "agent_url": {"type": "string"},
      "message": {"type": "string"},
      "context_id": {"type": "string"}
    }
  }
}
```

**Why separate?**
- MCP tools = Registry operations (database)
- Local tools = Protocol operations (HTTP/A2A)
- Separation of concerns

## A2A Message Structure

### Outgoing Message
```python
Message(
    role=Role.user,
    parts=[Part(root=TextPart(text="Your message here"))],
    message_id="uuid-here",
    context_id="conversation-uuid"  # optional
)
```

### A2A Protocol Flow
```
1. Get Agent Card (/.well-known/agent.json)
   └─> Agent metadata, capabilities, endpoints

2. Create A2A Client
   └─> Initialize with httpx client and agent card

3. Send Message (POST /a2a)
   └─> SendMessageRequest with Message object

4. Receive Response
   └─> SendMessageResponse with agent's reply
```

## Implementation Details

### URL Normalization
```python
# Input: "https://agent.example.com"
# Output: "https://agent.example.com/a2a"

# Input: "https://agent.example.com/"
# Output: "https://agent.example.com/a2a"

# Input: "https://agent.example.com/a2a"
# Output: "https://agent.example.com/a2a" (no change)
```

### Error Handling
```python
try:
    response = await send_a2a_message(agent_url, message)
    return response
except httpx.TimeoutException:
    return {"error": "Agent did not respond in time"}
except httpx.ConnectError:
    return {"error": "Could not connect to agent"}
except Exception as e:
    return {"error": str(e)}
```

### Response Extraction
```python
# A2A responses are complex nested objects
# Extract text from parts:

response_text = ""
if hasattr(response.root, 'result'):
    result = response.root.result
    if hasattr(result, 'artifact') and result.artifact:
        for part in result.artifact.parts:
            if hasattr(part.root, 'text'):
                response_text += part.root.text
```

## Comparison with Other Examples

### vs. mcp_native_tool_calling.py
| Feature | Native Tool Calling | A2A Communication |
|---------|-------------------|-------------------|
| Purpose | Registry operations | Agent communication |
| Protocols | MCP only | MCP + A2A |
| Scope | Discovery/metadata | Discovery + messaging |
| Use Case | Query registry | Coordinate agents |

### vs. simple_agent_lookup.py
| Feature | Simple Lookup | A2A Communication |
|---------|---------------|-------------------|
| Pattern | Manual regex | Claude decides |
| Tools | MCP only | MCP + A2A |
| Communication | No | Yes |
| Flexibility | Low | High |

## Example Use Cases

### 1. Agent Consultation
```
"Ask the financial analyst agent for investment advice"
→ Looks up agent → Sends A2A message → Returns advice
```

### 2. Multi-Agent Coordination
```
"Find a data scientist and ask them to analyze this dataset"
→ Searches registry → Gets top agent → Sends data via A2A
```

### 3. Agent Capability Discovery
```
"Ask agent-123 what it can do"
→ Gets agent info → Asks via A2A → Returns capabilities
```

### 4. Sequential Agent Workflow
```
"Ask agent-001 to analyze data, then ask agent-002 to visualize results"
→ Two-step workflow with different agents
```

## Required Dependencies

```txt
# From pyproject.toml
fastmcp>=2.0.0
pymongo>=4.6.0
anthropic>=0.7.0
mcp>=1.0.0
a2a-sdk>=0.1.0
httpx>=0.27.0
```

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."
export ATLAS_URL="mongodb+srv://..."

# Optional
export LOG_LEVEL="INFO"
```

## Running the Example

```bash
# Install dependencies
uv pip install -r examples/requirements-examples.txt

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export ATLAS_URL="mongodb+srv://..."

# Run interactive mode
python examples/a2a_agent_communication.py

# Choose option 1 for interactive chat
```

## Example Session

```
A2A-Aware Claude - Agent Communication via A2A Protocol
======================================================================

Examples:
  - 'Ask agent data-scientist-001 to list its capabilities'
  - 'Tell financial-analyst-001 to analyze my portfolio'

You: What agents are registered?

🤖 Claude: I can see there are 3 agents currently registered:
- data-scientist-001: Data Science Expert
- financial-analyst-001: Financial Analysis Agent  
- marketing-agent-123: Marketing Campaign Manager

You: Ask the data scientist to explain machine learning

🔧 Claude is using tools...
   Calling: get_agent({"agent_id": "data-scientist-001"})
   ✓ Result: Found agent at https://ds-agent.example.com

📡 Sending A2A message to: https://ds-agent.example.com/a2a
   Message: Explain machine learning concepts...
   ✓ Got agent card: Data Science Expert
   ✓ Received response from agent

🤖 Claude: I asked the Data Science Expert agent about machine learning.
They explained: "Machine learning is a subset of AI that enables systems
to learn and improve from experience without being explicitly programmed..."
```

## Next Steps

1. **Extend with more A2A features**
   - Streaming responses
   - File attachments
   - Context management

2. **Add agent orchestration**
   - Multi-agent workflows
   - Agent pipelines
   - Result aggregation

3. **Implement caching**
   - Cache agent cards
   - Connection pooling
   - Response caching

## Learn More

- [MCP Documentation](https://modelcontextprotocol.io/)
- [A2A Protocol](https://github.com/a2aproject)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [FastMCP Guide](https://github.com/jlowin/fastmcp)
