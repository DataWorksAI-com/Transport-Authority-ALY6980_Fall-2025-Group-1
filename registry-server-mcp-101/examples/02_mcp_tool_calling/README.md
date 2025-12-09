# Stage 02: MCP Tool Calling

## Overview

This stage demonstrates the **proper way** to integrate MCP with Claude by using native tool calling.

## Concept

Instead of manually detecting patterns, we let Claude see all available MCP tools and decide when to call them based on user intent.

## Pattern

```
User Input: "Tell me about the financial analyst agent"
     ↓
Claude sees available MCP tools
     ↓
Claude decides to call get_agent
     ↓
Claude receives result and formats response
```

## Key Improvement over Stage 01

**Stage 01 (Regex)**:
```python
# User MUST use: "@financial-analyst-001"
mentions = extract_agent_mentions(user_input)  # regex
for mention in mentions:
    result = await session.call_tool("get_agent", ...)
```

**Stage 02 (Native)**:
```python
# User can say: "Tell me about the financial analyst"
# Claude sees tools and decides what to do
tools = convert_mcp_tools_to_anthropic_format()
response = anthropic.messages.create(
    tools=tools,  # ← Claude decides when to call
    messages=[...]
)
```

## Files

### `mcp_native_tool_calling.py` ⭐ **RECOMMENDED**
**Purpose**: Demonstrates the standard MCP integration pattern

**Features**:
- Native MCP tool calling
- Natural language queries (no special syntax)
- Agentic loop (multiple tool calls)
- Interactive chat mode
- Proper tool schema conversion
- ~250 lines of code

**Use Case**: Production-ready registry operations

**Example**:
```bash
python 02_mcp_tool_calling/mcp_native_tool_calling.py

You: What agents are registered?
Claude: I found 3 agents: [lists agents]

You: Tell me about the data scientist agent
Claude: [calls get_agent automatically, provides details]
```

## Advantages

✅ Natural language - no special syntax
✅ Claude decides when to use tools
✅ Flexible and maintainable
✅ Standard MCP pattern
✅ Production-ready
✅ Multi-step workflows (agentic loop)

## How It Works

### 1. Tool Schema Conversion
```python
def convert_mcp_tools_to_anthropic_format(self) -> list[dict]:
    """Convert MCP tools to Anthropic's format"""
    anthropic_tools = []
    
    for tool in self.mcp_tools:
        tool_def = {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        }
        anthropic_tools.append(tool_def)
    
    return anthropic_tools
```

### 2. Agentic Loop
```python
while iteration < max_iterations:
    # Claude sees tools and decides what to do
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        tools=all_tools,
        messages=messages
    )
    
    # Check if Claude wants to call tools
    if response.stop_reason == "tool_use":
        # Execute tools and continue loop
        ...
    elif response.stop_reason == "end_turn":
        # Claude is done
        return final_response
```

### 3. Tool Execution
```python
for tool_use in response.content:
    if tool_use.type == "tool_use":
        # Call the MCP tool
        result = await session.call_tool(
            tool_use.name,
            tool_use.input
        )
        # Add result back to conversation
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": result
        })
```

## Documentation Files

### `NATIVE_TOOL_CALLING.txt`
Detailed explanation of the native tool calling pattern and why it's better than regex.

### `COMPARISON.txt`
Visual comparison between manual pattern matching (Stage 01) and native tool calling (Stage 02).

### `FLOW_DIAGRAM.txt`
ASCII diagrams showing the complete flow of native tool calling.

## When to Use This Stage

- ✅ **Registry Operations**: Querying the NANDA registry
- ✅ **Agent Discovery**: Finding and looking up agents
- ✅ **Production Systems**: Building reliable integrations
- ✅ **Learning MCP**: Understanding proper MCP patterns

## Limitations

⚠️ This stage focuses on **discovery** (finding agents) but doesn't communicate with them.

For actual agent-to-agent communication, see **Stage 03**.

## Running the Example

### Prerequisites
```bash
# Install dependencies
pip install -r ../requirements-examples.txt

# Set environment variables
export ATLAS_URL="mongodb+srv://..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Interactive Mode
```bash
python 02_mcp_tool_calling/mcp_native_tool_calling.py

# Choose option 1 for chat mode
# Ask natural language questions like:
# - "What agents are available?"
# - "Search for data science agents"
# - "Tell me about agent-123"
```

### Example Queries Mode
```bash
python 02_mcp_tool_calling/mcp_native_tool_calling.py

# Choose option 2 to run pre-defined examples
```

## Key Concepts Demonstrated

1. **Tool Schema Conversion**: MCP → Anthropic format
2. **Native Tool Calling**: Claude decides when to call tools
3. **Agentic Loop**: Multiple tool calls in sequence
4. **Tool Result Handling**: Processing and formatting results
5. **Natural Language**: No special syntax required

## Example Session

```
═══════════════════════════════════════════════════════════
MCP Native Tool Calling - Claude with NANDA Registry
═══════════════════════════════════════════════════════════

✓ Connected to NANDA Registry MCP server
✓ Available MCP tools: 8

Examples:
  - 'What agents are registered?'
  - 'Search for finance agents'
  - 'Get details for agent financial-analyst-001'

You: What agents do we have?

💬 User: What agents do we have?

🔧 Claude is using tools (iteration 1)...
   Calling: list_agents({})
   ✓ Result: Found 3 agents...

🤖 Claude: I can see there are currently 3 agents registered:

1. **data-scientist-001** - Data Science Expert
   Tags: data-science, machine-learning, analytics

2. **financial-analyst-001** - Financial Analysis Agent
   Tags: finance, analysis, reporting

3. **marketing-agent-123** - Marketing Campaign Manager
   Tags: marketing, campaigns, social-media

You: Tell me more about the data scientist

💬 User: Tell me more about the data scientist

🔧 Claude is using tools (iteration 1)...
   Calling: get_agent({"agent_id": "data-scientist-001"})
   ✓ Result: {"agent_id": "data-scientist-001"...}

🤖 Claude: The Data Science Expert (data-scientist-001) is a 
specialized agent for data analysis and machine learning tasks.

Details:
- URL: https://ds-agent.example.com
- Domain: data-science
- Tags: data-science, machine-learning, analytics
- Status: active

This agent can help with statistical analysis, machine learning
model development, and data visualization tasks.
```

## Comparison with Stage 01

| Aspect | Stage 01 (Regex) | Stage 02 (Native) |
|--------|------------------|-------------------|
| **Syntax** | @agent-name required | Natural language |
| **Who decides** | Developer (regex) | Claude (reasoning) |
| **Flexibility** | Fixed patterns | Understands intent |
| **Maintainability** | Hard to extend | Easy to add tools |
| **Production ready** | No | Yes |

## Next Steps

Move to **Stage 03** to add A2A protocol communication, enabling actual agent-to-agent messaging.

## Learn More

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [NATIVE_TOOL_CALLING.txt](./NATIVE_TOOL_CALLING.txt) - Detailed explanation
- [COMPARISON.txt](./COMPARISON.txt) - Visual comparisons

## Progression

```
Stage 01: Regex extraction
    ↓
Stage 02: Native tool calling (You are here)
    ↓
Stage 03: Add A2A communication
```

---

**Previous Stage**: [Stage 01 - Regex Extraction](../01_regex_extraction/README.md)

**Next Stage**: [Stage 03 - A2A Agent Communication](../03_a2a_agent_communication/README.md)
