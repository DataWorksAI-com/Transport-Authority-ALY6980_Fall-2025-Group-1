# Anthropic Agent Examples

This directory contains examples showing the **evolution** of integrating Anthropic's Claude with the NANDA Registry MCP server, organized into three progressive stages.

## 📁 Folder Structure

## 📁 Folder Structure

```
examples/
├── 01_regex_extraction/              # Stage 1: Learning
│   ├── simple_agent_lookup.py
│   ├── anthropic_agent_example.py
│   └── README.md
│
├── 02_mcp_tool_calling/              # Stage 2: Production Discovery ⭐
│   ├── mcp_native_tool_calling.py
│   ├── NATIVE_TOOL_CALLING.txt
│   ├── COMPARISON.txt
│   ├── FLOW_DIAGRAM.txt
│   └── README.md
│
├── 03_a2a_agent_communication/       # Stage 3: Multi-Agent ⭐⭐⭐
│   ├── a2a_agent_communication.py
│   ├── A2A_COMMUNICATION.md
│   ├── A2A_ARCHITECTURE.txt
│   ├── QUICKSTART_A2A.md
│   └── README.md
│
├── 📁 04_external_mcp_server/                 # Stage 4: Production Deployment ⭐⭐⭐⭐
│   ├── external_mcp_client.py        (Connect from Terminal 2)
│   ├── README.md
│   └── STAGE_04_SUMMARY.md
│   # Server: Run src/agent_mcp.py with FastMCP CLI (Terminal 1)
│
├── requirements-examples.txt         # Shared dependencies
├── test_examples.py                  # Test script
├── EVOLUTION.md                      # Detailed evolution comparison
├── FOLDER_STRUCTURE.md               # Structure guide
└── README.md                         # This file
```

## 🎯 Quick Start - Which Stage Should I Use?

| Your Goal | Use This Stage | Command |
|-----------|----------------|---------|
| **Learning MCP basics** | Stage 01 | `python 01_regex_extraction/simple_agent_lookup.py` |
| **Registry queries** | Stage 02 ⭐ | `python 02_mcp_tool_calling/mcp_native_tool_calling.py` |
| **Agent communication** | Stage 03 ⭐⭐⭐ | `python 03_a2a_agent_communication/a2a_agent_communication.py` |
| **Production deployment** | Stage 04 ⭐⭐⭐⭐ | Terminal 1: `python -m fastmcp run src/agent_mcp.py --transport sse --port 8080`<br>Terminal 2: `python 04_external_mcp_server/external_mcp_client.py` |

## 📚 The Four Stages

### Stage 01: Regex Extraction
**Pattern**: Manual detection with regex → Manual MCP calls

📂 `01_regex_extraction/`

**What it demonstrates:**
- Basic MCP client connection
- Regex pattern matching (`@agent-name`)
- Manual tool calling
- Simple output formatting

**Files:**
- `simple_agent_lookup.py` - Minimal example (~100 lines)
- `anthropic_agent_example.py` - Full interactive agent (~300 lines)

**When to use:**
- Learning MCP basics
- Quick prototyping
- Testing MCP connection

**Limitations:**
- ❌ Requires special syntax (`@agent-name`)
- ❌ Claude doesn't see tools
- ❌ Not production-ready

[📖 Read Stage 01 README](01_regex_extraction/README.md)

---

### Stage 02: MCP Tool Calling ⭐
**Pattern**: Natural language → Claude sees tools → Claude decides → Tool execution

📂 `02_mcp_tool_calling/`

**What it demonstrates:**
- Native MCP integration (the standard pattern)
- Tool schema conversion
- Agentic loop with multiple tool calls
- Natural language queries

**Files:**
- `mcp_native_tool_calling.py` - Production-ready example (~250 lines)
- `NATIVE_TOOL_CALLING.txt` - Detailed explanation
- `COMPARISON.txt` - Visual comparisons
- `FLOW_DIAGRAM.txt` - Architecture diagrams

**When to use:**
- Production registry operations
- Agent discovery and search
- Natural language interface
- Standard MCP pattern

**Key improvement:**
```python
# Before (Stage 01): User MUST use "@financial-analyst-001"
# After (Stage 02): User CAN say "Tell me about the financial analyst"
```

[📖 Read Stage 02 README](02_mcp_tool_calling/README.md)

---

### Stage 03: A2A Agent Communication ⭐⭐⭐
**Pattern**: Natural language → Claude orchestrates → MCP discovery + A2A communication → Agent response

📂 `03_a2a_agent_communication/`

**What it demonstrates:**
- Complete agent coordination
- Multi-protocol integration (MCP + A2A)
- Agent discovery via MCP
- Agent communication via A2A protocol
- Context-aware conversations

**Files:**
- `a2a_agent_communication.py` - Full coordination (~400 lines)
- `A2A_COMMUNICATION.md` - Complete guide
- `A2A_ARCHITECTURE.txt` - Visual architecture
- `QUICKSTART_A2A.md` - Quick start guide

**When to use:**
- Agent-to-agent communication
- Multi-agent workflows
- Production systems
- Complete agent coordination

**Key improvement:**
```python
# Stage 02: Can only discover agents
"Get details for agent-123"  # ✅ Works

# Stage 03: Can discover AND communicate
"Ask agent-123 to analyze this data"  # ✅ Works!
```

[📖 Read Stage 03 README](03_a2a_agent_communication/README.md)

---

### Stage 04: External MCP Server ⭐⭐⭐⭐
**Pattern**: Separate server/client → HTTP/SSE connection → Distributed deployment

📂 `04_external_mcp_server/`

**What it demonstrates:**
- MCP server as independent service
- HTTP/SSE transport (instead of stdio)
- Server-client separation
- Production deployment patterns
- Multiple concurrent clients

**Files:**
- `start_mcp_server.py` - Start MCP server on HTTP/SSE
- `external_mcp_client.py` - Client connecting to external server
- `README.md` - Complete deployment guide

**When to use:**
- Production deployments
- Multiple clients connecting to same server
- Distributed systems (server and clients on different machines)
- Docker/Kubernetes deployments
- Long-running server processes

**Key improvement:**
```python
# Stage 03: Server embedded in client (stdio)
# Server starts/stops with client

# Stage 04: Server independent (HTTP/SSE)
# Terminal 1: python start_mcp_server.py  ← Runs continuously
# Terminal 2: python external_mcp_client.py  ← Connects to server
# Server keeps running after client exits!
```

**Architecture:**
```
Terminal 1              Terminal 2              Terminal 3
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ MCP Server  │◄───────┤  Client 1   │        │  Client 2   │
│             │  HTTP  │             │        │             │
│ Port 8080   │◄───────┼─────────────┼────────┤             │
└─────────────┘        └─────────────┘        └─────────────┘
     │
     ▼
  MongoDB
```

[📖 Read Stage 04 README](04_external_mcp_server/README.md)

---

## 🎓 Learning Path

### Beginner (1-2 hours)
1. Start with **Stage 01** to understand MCP basics
2. Read the code in `simple_agent_lookup.py`
3. Run it and see how manual pattern matching works

### Intermediate (2-3 hours)
1. Move to **Stage 02** to see proper MCP integration
2. Compare with Stage 01 using `COMPARISON.txt`
3. Run `mcp_native_tool_calling.py` and explore natural language queries

### Advanced (3-4 hours)
1. Explore **Stage 03** for complete agent coordination
2. Study `A2A_ARCHITECTURE.txt` to understand multi-protocol integration
3. Run `a2a_agent_communication.py` and test agent communication

### Expert
1. Read `EVOLUTION.md` for comprehensive comparison
2. Build your own integration using Stage 03 as template
3. Extend with custom tools and workflows

## 🚀 Running the Examples

### Prerequisites
```bash
# Install dependencies
pip install -r requirements-examples.txt

# Or with uv
uv pip install -r requirements-examples.txt

# Set environment variables
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Run Any Stage
```bash
# Stage 01
python 01_regex_extraction/simple_agent_lookup.py
python 01_regex_extraction/anthropic_agent_example.py

# Stage 02 ⭐
python 02_mcp_tool_calling/mcp_native_tool_calling.py

# Stage 03 ⭐⭐⭐
python 03_a2a_agent_communication/a2a_agent_communication.py

# Stage 04 ⭐⭐⭐⭐ (requires 2 terminals)
# Terminal 1:
python 04_external_mcp_server/start_mcp_server.py --port 8080

# Terminal 2:
python 04_external_mcp_server/external_mcp_client.py
```

## 📊 Feature Comparison

| Feature | Stage 01 | Stage 02 | Stage 03 | Stage 04 |
|---------|----------|----------|----------|----------|
| **Syntax** | `@agent-name` | Natural | Natural | Natural |
| **Who Decides** | Regex | Claude | Claude | Claude |
| **MCP Tools** | ✅ Manual | ✅ Native | ✅ Native | ✅ Native |
| **A2A Communication** | ❌ | ❌ | ✅ | ✅ |
| **Multi-Step** | ❌ | ✅ | ✅ | ✅ |
| **Agentic Loop** | ❌ | ✅ | ✅ | ✅ |
| **Server Type** | N/A | Embedded (stdio) | Embedded (stdio) | External (HTTP) |
| **Multiple Clients** | ❌ | ❌ | ❌ | ✅ |
| **Distributed** | ❌ | ❌ | ❌ | ✅ |
| **Production Ready** | ❌ | ✅ | ✅ | ✅✅✅ |
| **Complexity** | Low | Medium | High | High |
| **Flexibility** | Low | High | Highest | Highest |
| **Lines of Code** | ~100-300 | ~250 | ~400 | ~450 |

## 📖 Example Queries by Stage

### Stage 01 (Regex)
```
Input: "@financial-analyst-001"
Input: "Tell me about @data-scientist-001"
```

### Stage 02 (MCP Native) ⭐
```
Input: "What agents are registered?"
Input: "Search for data science agents"
Input: "Tell me about the financial analyst agent"
Input: "Get details for agent-123"
```

### Stage 03 (MCP + A2A) ⭐⭐⭐
```
Input: "What agents are available?"  # Discovery
Input: "Ask agent data-scientist-001 to explain machine learning"  # Communication
Input: "Tell financial-analyst-001 to analyze my portfolio"  # Communication
Input: "Find a data scientist and ask them to help with clustering"  # Both!
```

### Stage 04 (External Server) ⭐⭐⭐⭐
```
# Same queries as Stage 03, but:
# - Server runs independently in Terminal 1
# - Client connects via HTTP in Terminal 2
# - Multiple clients can connect simultaneously
# - Server persists between client sessions
```

## 🏗️ Architecture Progression

### Stage 01: Simple
```
User Input → Regex Match → MCP Call → Result
```

### Stage 02: Intelligent
```
User Input → Claude (sees tools) → Decides which tools → MCP Calls → Claude formats response
```

### Stage 03: Complete
```
User Input → Claude (orchestrator)
              ├─→ MCP Tools (discovery)
              │   └─→ Registry Database
              └─→ Local Tools (communication)
                  └─→ A2A Protocol
                      └─→ Target Agent
```

### Stage 04: Distributed
```
Terminal 1                    Terminal 2
┌─────────────┐              ┌─────────────┐
│ MCP Server  │              │   Client    │
│             │◄─── HTTP ────┤             │
│ Port 8080   │              │   Claude    │
│             │              │             │
│ ├─ MCP      │              │ ├─ MCP      │
│ └─ MongoDB  │              │ └─ A2A      │
└─────────────┘              └─────────────┘
     │                             │
     └────── Distributed ──────────┘
```

## 💡 Key Insights

### Why Four Stages?

1. **Stage 01 (Regex)**: Shows the naive approach
   - Easy to understand
   - Limited flexibility
   - Teaching tool

2. **Stage 02 (Native MCP)**: Shows the proper MCP pattern
   - Industry standard
   - Production ready for discovery
   - Foundation for advanced features

3. **Stage 03 (MCP + A2A)**: Shows complete agent coordination
   - Multi-protocol integration
   - Production ready for communication
   - Real-world multi-agent systems

4. **Stage 04 (External Server)**: Shows distributed deployment
   - Server-client separation
   - Multiple concurrent clients
   - Production scalability
   - Enterprise-ready architecture

### Common Misconception

❌ "I need to manually detect agent mentions with regex"
✅ "I should let Claude see the tools and decide when to call them"

### Best Practices

- **Learning**: Start with Stage 01, understand MCP basics
- **Discovery**: Use Stage 02 for registry operations
- **Communication**: Use Stage 03 for agent coordination
- **Development**: Stage 03 for rapid prototyping
- **Production**: Stage 04 for scalable deployments

## 📝 Additional Resources

### Detailed Documentation
- **[EVOLUTION.md](EVOLUTION.md)** - Complete evolution analysis with code comparisons
- **[test_examples.py](test_examples.py)** - Test script for all examples
- **[requirements-examples.txt](requirements-examples.txt)** - Shared dependencies

### Stage-Specific Docs
- **Stage 01**: See [01_regex_extraction/README.md](01_regex_extraction/README.md)
- **Stage 02**: See [02_mcp_tool_calling/README.md](02_mcp_tool_calling/README.md)
- **Stage 03**: See [03_a2a_agent_communication/README.md](03_a2a_agent_communication/README.md)

## 🔧 Prerequisites

### 1. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements-examples.txt

# Or with uv
uv pip install -r requirements-examples.txt
```

### 2. Set Environment Variables

```bash
# Required for all stages
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### 3. Verify MCP Server

```bash
# Ensure the MCP server exists
ls src/agent_mcp.py

# Test MCP server (optional)
python src/agent_mcp.py
```

## 🎬 Quick Examples

### Stage 01: Basic Lookup
```bash
python 01_regex_extraction/simple_agent_lookup.py

# Input: @financial-analyst-001
# Output: Agent details...
```

### Stage 02: Natural Language Discovery
```bash
python 02_mcp_tool_calling/mcp_native_tool_calling.py

# Choose option 1 for interactive chat
You: What agents are available?
Claude: I found 3 agents: [details]

You: Tell me about the data scientist
Claude: [automatically calls get_agent and provides info]
```

### Stage 03: Full Agent Communication
```bash
python 03_a2a_agent_communication/a2a_agent_communication.py

# Choose option 1 for interactive chat
You: Ask agent data-scientist-001 to explain machine learning

Claude: [discovers agent via MCP]
Claude: [communicates via A2A]
Claude: The agent explained: "Machine learning is..."
```

## 🐛 Troubleshooting

### Common Issues

**"ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**"ATLAS_URL not set"**
```bash
export ATLAS_URL="mongodb+srv://..."
```

**"No module named 'anthropic'"**
```bash
pip install -r requirements-examples.txt
```

**"Python version too old"**
```bash
# Requires Python 3.10+
python3 --version

# Use uv to manage versions
uv python install 3.12
```

**"MCP server connection failed"**
- Check that `src/agent_mcp.py` exists
- Verify MongoDB connection string
- Ensure Python 3.10+ is being used

**"Agent not found"**
- Register agents first using the REST API or MCP tools
- Check existing agents: `list_agents` tool

### Getting Help

1. Check stage-specific README files
2. Review `EVOLUTION.md` for detailed comparisons
3. Look at code examples in each stage
4. Verify environment variables are set

## 📚 Learning Resources

### For Beginners
1. Start with [Stage 01 README](01_regex_extraction/README.md)
2. Run `simple_agent_lookup.py` and read the code
3. Understand basic MCP concepts

### For Intermediate Users
1. Review [Stage 02 README](02_mcp_tool_calling/README.md)
2. Study `COMPARISON.txt` and `NATIVE_TOOL_CALLING.txt`
3. Run `mcp_native_tool_calling.py`
4. Experiment with natural language queries

### For Advanced Users
1. Explore [Stage 03 README](03_a2a_agent_communication/README.md)
2. Study `A2A_ARCHITECTURE.txt` and `A2A_COMMUNICATION.md`
3. Run `a2a_agent_communication.py`
4. Build custom multi-agent workflows

### External Resources
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [A2A Protocol](https://github.com/a2aproject)
- [FastMCP Guide](https://github.com/jlowin/fastmcp)

## 🤝 Contributing

To add new examples:
1. Choose appropriate stage folder
2. Follow existing code patterns
3. Add documentation
4. Update stage README
5. Test thoroughly

## 📄 License

See main repository [LICENSE](../LICENSE) file.

---

## Old Content Below (Deprecated)

> **Note**: The content below is deprecated. Please use the stage-based structure above.

### 2. Simple Agent Lookup (`simple_agent_lookup.py`)

A minimal example showing manual pattern matching and MCP tool calling.

```bash
python examples/simple_agent_lookup.py
```

**How it works:**
1. Regex detects `@agent-name` patterns in user input
2. Your code manually calls MCP `get_agent` tool
3. Agent context is added to Claude's prompt
4. Claude responds with the enhanced context

**Features:**
- Manual `@agent-name` detection with regex
- Direct MCP tool invocation
- Context enhancement for Claude
- Three example queries

**Use this when:**
- You need specific trigger patterns (like @mentions)
- You want explicit control over when tools are called
- Learning the basics of MCP tool calling

### 3. Interactive Agent Chat (`anthropic_agent_example.py`)

Full-featured interactive agent with manual pattern matching.

```bash
python examples/anthropic_agent_example.py
```

**Features:**
- Interactive chat loop with conversation history
- Advanced agent mention detection with filtering
- Multiple modes: interactive, single query, list agents
- Manual control over tool invocation

**Use this when:**
- You need the `@mention` pattern specifically
- You want full control over the interaction flow
- Building a chatbot with specific trigger patterns

## Comparison: Native Tool Calling vs Manual Pattern Matching

| Feature | Native Tool Calling | Manual Pattern Matching |
|---------|-------------------|------------------------|
| **Ease of Use** | ✅ Simplest - Claude decides | ⚠️ Requires regex patterns |
| **Flexibility** | ✅ Works with any query | ❌ Only works with specific patterns |
| **Maintenance** | ✅ Minimal - MCP handles changes | ⚠️ Update regex when patterns change |
| **User Experience** | ✅ Natural language | ⚠️ Users must learn syntax |
| **Tool Discovery** | ✅ Claude explores all tools | ❌ Limited to your code logic |
| **Error Handling** | ✅ Claude handles gracefully | ⚠️ You must handle errors |
| **MCP Standard** | ✅ Follows MCP best practices | ❌ Custom implementation |
| **Multi-turn Conversations** | ✅ Natural agentic flow | ⚠️ Requires manual state management |

**Recommendation:** Use **Native Tool Calling** (`mcp_native_tool_calling.py`) for most use cases. It's simpler, more maintainable, and follows MCP best practices.

## Quick Start

### Run the Recommended Example (Native Tool Calling)

```bash
# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export ATLAS_URL="mongodb+srv://..."

# Run the example
python examples/mcp_native_tool_calling.py

# Try queries like:
# - "What agents are registered?"
# - "Tell me about financial-analyst-001"
# - "Search for agents with financial capabilities"
```

## Prerequisites

### 1. Install Dependencies

```bash
pip install anthropic mcp python-dotenv
```

Or add to your `requirements.txt`:
```
anthropic>=0.7.0
mcp>=1.0.0
python-dotenv>=1.0.0
```

### 2. Set Environment Variables

Create a `.env` file in the project root or export these variables:

```bash
# Anthropic API Key (required)
export ANTHROPIC_API_KEY="sk-ant-..."

# MongoDB Connection String (required)
export ATLAS_URL="mongodb+srv://username:password@cluster.mongodb.net/"
```

### 3. Ensure MCP Server is Available

The examples assume the MCP server is at `src/agent_mcp.py`. Make sure you have:
- Created the MCP server (see main README.md)
- Have Python 3.10+ available
- Have the required packages installed

## Usage Patterns

### Pattern 1: Native Tool Calling (Recommended)

```python
import asyncio
from mcp_native_tool_calling import MCPAwareAgent

async def main():
    agent = MCPAwareAgent()
    await agent.start_mcp_connection()
    
    try:
        # Claude automatically calls MCP tools as needed
        response = await agent.process_message(
            "What agents are available for financial analysis?"
        )
        print(response)
    finally:
        await agent.close_mcp_connection()

asyncio.run(main())
```

### Pattern 2: Interactive Chat with Native Tools

```python
from mcp_native_tool_calling import MCPAwareAgent

async def main():
    agent = MCPAwareAgent()
    await agent.chat_loop()  # Claude calls tools automatically

asyncio.run(main())
```

### Pattern 3: Manual Pattern Matching (Legacy)

```python
from simple_agent_lookup import process_with_agent_context

async def main():
    # Only works with @agent-name syntax
    response = await process_with_agent_context(
        "Connect me with @financial-analyst-001"
    )
    print(response)

asyncio.run(main())
```

## How It Works

### Native Tool Calling Flow (Recommended)

```
1. User Request
   ↓
   "Tell me about financial-analyst-001"

2. MCP Connection
   ↓
   - Connect to MCP server
   - Retrieve available tools (list_tools)
   - Convert to Anthropic format

3. Claude API Call
   ↓
   - Send user message + tool schemas
   - Claude analyzes request
   - Claude decides: "I need get_agent tool"

4. Tool Execution
   ↓
   - Claude returns tool_use with:
     • tool_name: "get_agent"
     • arguments: {"agent_id": "financial-analyst-001"}
   - Your code calls MCP server
   - Return result to Claude

5. Claude Response
   ↓
   - Claude receives tool result
   - Blends information into natural response
   - Returns final answer to user
```

### Manual Pattern Matching Flow (Legacy)

```
1. User Request
   ↓
   "Connect with @financial-analyst-001"

2. Pattern Detection
   ↓
   - Regex: @([\w\-]+)
   - Extract: ["financial-analyst-001"]

3. Manual Tool Call
   ↓
   - Your code calls get_agent
   - Receive agent information

4. Context Enhancement
   ↓
   - Add agent info to prompt
   - Send enhanced prompt to Claude

5. Claude Response
   ↓
   - Claude sees agent context
   - Generates response
```

**Key Difference:** In native tool calling, **Claude decides** when to call tools. In manual pattern matching, **your code decides** based on regex.

## Customization

### Modify Agent Detection

Edit the `extract_agent_mentions` function to customize the pattern:

```python
# Allow only specific formats
pattern = re.compile(r'@(agent-[\w\-]+)')

# Allow mentions with domains
pattern = re.compile(r'@([\w\-]+(?:\.[\w\-]+)*)')
```

### Add More Context

Enhance the agent context with additional information:

```python
agent_context += f"  - Capabilities: {agent_info.get('capabilities', [])}\n"
agent_context += f"  - Domain: {agent_info.get('domain', 'unknown')}\n"
```

### Use Different MCP Tools

The examples use `get_agent`, but you can also use:

```python
# Search for agents by capability
result = await session.call_tool(
    "search_agents",
    arguments={"query": "financial"}
)

# List all available agents
result = await session.call_tool(
    "list_agents",
    arguments={}
)
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

Get your API key from https://console.anthropic.com/ and set it:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "ATLAS_URL not set"

Set your MongoDB connection string:
```bash
export ATLAS_URL="mongodb+srv://..."
```

### "No module named 'anthropic'"

Install the Anthropic SDK:
```bash
pip install anthropic
```

### "No module named 'mcp'"

Install the MCP SDK:
```bash
pip install mcp
```

### Agent Not Found

Make sure the agent is registered in your MongoDB database. You can:
1. Register agents via the REST API
2. Use the MCP `register_agent` tool
3. Check existing agents with `list_agents`

### MCP Server Connection Issues

Ensure:
- Python 3.10+ is being used
- `src/agent_mcp.py` exists and is accessible
- Required packages (fastmcp, pymongo) are installed
- MongoDB connection is valid

## Next Steps

1. **Start Simple**: Run `simple_agent_lookup.py` to understand the basics
2. **Try Interactive**: Run `anthropic_agent_example.py` for a full experience
3. **Customize**: Modify the examples for your specific use case
4. **Integrate**: Incorporate the patterns into your application

## Learn More

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [NANDA Registry Main README](../README.md)
