# Stage 01: Regex Extraction

## Overview

This stage demonstrates the **basic approach** to agent integration using manual pattern matching with regular expressions.

## Concept

The examples in this stage detect special syntax (like `@agent-name`) using regex patterns and manually call MCP tools when matches are found.

## Pattern

```
User Input: "@agent-123"
     ↓
Regex Match: Extract "agent-123"
     ↓
Manual MCP Call: get_agent("agent-123")
     ↓
Display Result
```

## Files

### `simple_agent_lookup.py`
**Purpose**: Minimal example showing the basic pattern

**Features**:
- Regex pattern matching for `@agent-name`
- Single MCP tool call
- Simple output display
- ~100 lines of code

**Use Case**: Learning, quick prototyping

**Example**:
```bash
python 01_regex_extraction/simple_agent_lookup.py

# Input: @financial-analyst-001
# Output: Agent details...
```

### `anthropic_agent_example.py`
**Purpose**: Full-featured interactive agent with manual pattern matching

**Features**:
- Regex pattern matching for `@agent-name`
- Conversation history
- Multiple interaction modes
- Claude integration (but not for tool calling)
- ~300 lines of code

**Use Case**: More sophisticated interface, still learning

**Example**:
```bash
python 01_regex_extraction/anthropic_agent_example.py

# Input: Tell me about @data-scientist-001
# Output: Looking up @data-scientist-001...
#         Found: [agent details]
```

## Advantages

✅ Simple to understand
✅ Good for learning MCP basics
✅ Quick to implement
✅ Direct control over flow

## Limitations

❌ Requires special syntax (`@agent-name`)
❌ Claude doesn't see available tools
❌ Not flexible - can only do what's explicitly coded
❌ User has to learn the syntax
❌ Not production-ready for complex use cases

## When to Use This Stage

- **Learning**: Understanding basic MCP concepts
- **Prototyping**: Quick proof of concept
- **Testing**: Validating MCP server connection
- **Simple Needs**: Just need basic agent lookup

## Next Steps

Move to **Stage 02** to see how native MCP tool calling eliminates the need for regex patterns and special syntax.

## Running the Examples

### Prerequisites
```bash
# Install dependencies
pip install -r ../requirements-examples.txt

# Set environment variables
export ATLAS_URL="mongodb+srv://..."
export ANTHROPIC_API_KEY="sk-ant-..."  # For anthropic_agent_example.py only
```

### Simple Lookup
```bash
python 01_regex_extraction/simple_agent_lookup.py

# Enter text with @agent-name mentions
```

### Full Interactive Agent
```bash
python 01_regex_extraction/anthropic_agent_example.py

# Choose mode:
# 1. Interactive chat with @agent-name detection
# 2. Single query mode
# 3. Batch agent lookup
```

## Key Concepts Demonstrated

1. **MCP Client Connection**: Using stdio to connect to MCP server
2. **Tool Calling**: Manually calling MCP tools
3. **Pattern Matching**: Using regex to extract agent mentions
4. **Basic Integration**: Combining MCP with user input

## Code Pattern

```python
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. Define regex pattern
AGENT_MENTION_PATTERN = r'@([\w-]+)'

# 2. Extract mentions
def extract_agent_mentions(text: str) -> list[str]:
    return re.findall(AGENT_MENTION_PATTERN, text)

# 3. Connect to MCP
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # 4. Manual tool call for each match
        mentions = extract_agent_mentions(user_input)
        for agent_id in mentions:
            result = await session.call_tool("get_agent", {
                "agent_id": agent_id
            })
```

## Progression

```
Stage 01 (You are here)
    ↓
Stage 02: Remove regex, let Claude call tools
    ↓
Stage 03: Add A2A communication
```

---

**Next Stage**: [Stage 02 - MCP Tool Calling](../02_mcp_tool_calling/README.md)
