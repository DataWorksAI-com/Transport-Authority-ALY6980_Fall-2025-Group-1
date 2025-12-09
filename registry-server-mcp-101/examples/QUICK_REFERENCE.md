# 🎯 Examples Quick Reference Guide

## 🚀 Quick Start - Choose Your Path

### "I'm new to MCP" → Stage 01
```bash
cd examples
python 01_regex_extraction/simple_agent_lookup.py

# Learn: Basic MCP concepts, manual tool calling
# Time: 30 minutes
```

### "I want to query the registry" → Stage 02 ⭐
```bash
cd examples
python 02_mcp_tool_calling/mcp_native_tool_calling.py

# Learn: Native tool calling, natural language
# Time: 1 hour
# Use: Production registry operations
```

### "I need agent communication" → Stage 03 ⭐⭐⭐
```bash
cd examples
python 03_a2a_agent_communication/a2a_agent_communication.py

# Learn: Multi-protocol integration, A2A
# Time: 2 hours
# Use: Production multi-agent systems
```

### "I need distributed deployment" → Stage 04 ⭐⭐⭐⭐
```bash
cd /path/to/registry-server  # Repository root

# Terminal 1: Start server
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080

# Terminal 2: Run client
python examples/04_external_mcp_server/external_mcp_client.py

# Learn: HTTP/SSE transport, server-client separation
# Time: 2 hours
# Use: Production distributed systems, Docker, K8s
```

## 📊 Stage Comparison (One Glance)

| Aspect | Stage 01 | Stage 02 | Stage 03 | Stage 04 |
|--------|----------|----------|----------|----------|
| **Pattern** | Regex | Native MCP | MCP + A2A | External |
| **Syntax** | @agent-name | Natural | Natural | Natural |
| **Complexity** | Low | Medium | High | High |
| **Production** | ❌ | ✅ | ✅ | ✅✅ |
| **Communication** | ❌ | ❌ | ✅ | ✅ |
| **Distributed** | ❌ | ❌ | ❌ | ✅ |
| **Recommended** | Learning | ⭐ Discovery | ⭐⭐⭐ Full | ⭐⭐⭐⭐ Production |

## 🎓 Learning Path (Step by Step)

```
Day 1: Understanding Basics (2 hours)
├─ 1. Read: examples/README.md
├─ 2. Run: 01_regex_extraction/simple_agent_lookup.py
├─ 3. Study: The code and comments
└─ 4. Read: 01_regex_extraction/README.md

Day 2: Native MCP Pattern (3 hours)
├─ 1. Read: 02_mcp_tool_calling/README.md
├─ 2. Review: COMPARISON.txt (Stage 01 vs 02)
├─ 3. Run: 02_mcp_tool_calling/mcp_native_tool_calling.py
└─ 4. Experiment: Natural language queries

Day 3: Multi-Agent Coordination (4 hours)
├─ 1. Read: 03_a2a_agent_communication/README.md
├─ 2. Study: A2A_ARCHITECTURE.txt
├─ 3. Run: 03_a2a_agent_communication/a2a_agent_communication.py
└─ 4. Test: Agent communication workflows

Day 4: Production Deployment (3 hours)
├─ 1. Read: 04_external_mcp_server/STAGE_04_SUMMARY.md
├─ 2. Study: 04_external_mcp_server/README.md
├─ 3. Terminal 1: Start server with FastMCP CLI
└─ 4. Terminal 2: Run external_mcp_client.py

Day 5: Distributed Deployment Deep Dive (Optional)
├─ 1. Read:[Registry Deployment Documentation](deploy/README.md)
├─ 2. Review: All technical documentation and code
├─ 3. Build: Deploy the 3 scenarios
└─ 4. Extend: Add new tools/features
```

## 💻 Example Commands

### Setup (One Time)
```bash
# Install dependencies
pip install -r examples/requirements-examples.txt

# Set environment
export ANTHROPIC_API_KEY="sk-ant-..."
export ATLAS_URL="mongodb+srv://..."
```

### Stage 01 Examples
```bash
# Minimal lookup
python 01_regex_extraction/simple_agent_lookup.py
# Input: @financial-analyst-001

# Full interactive
python 01_regex_extraction/anthropic_agent_example.py
# Choose mode, chat with agents
```

### Stage 02 Example (Recommended)
```bash
# Production-ready
python 02_mcp_tool_calling/mcp_native_tool_calling.py

# Try these queries:
# - "What agents are registered?"
# - "Search for data science agents"
# - "Tell me about agent-123"
```

### Stage 03 Example (Advanced)
```bash
# Full agent coordination
python 03_a2a_agent_communication/a2a_agent_communication.py

# Try these queries:
# - "What agents are available?"
# - "Ask agent-123 to explain machine learning"
# - "Tell the data scientist to analyze data"
```

### Stage 04 Example (Production)
```bash
# Terminal 1: Start HTTP/SSE server (from repository root)
python -m fastmcp run src/agent_mcp.py --transport sse --port 8080

# Terminal 2: Connect client (from repository root)
python examples/04_external_mcp_server/external_mcp_client.py

# Try these queries:
# - "What agents are registered?"
# - "Tell agent-123 to perform analysis"
# - "Search for data science agents"

# Note: Server stays running, client can restart
```




## 🐛 Common Issues

### "Missing dependencies"
```bash
pip install -r examples/requirements-examples.txt
```

### "Environment variables not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export ATLAS_URL="mongodb+srv://..."
```

### "Python version too old"
```bash
# Requires Python 3.10+
python3 --version
```

## 🎉 Success!

You now have a clear, organized, progressive learning path through MCP and the NANDA Registry examples!

**Start here**: `examples/README.md`
**Then**: Choose your stage based on your goal
**Learn**: Follow the progression 01 → 02 → 03 → 04

Happy coding! 🚀
