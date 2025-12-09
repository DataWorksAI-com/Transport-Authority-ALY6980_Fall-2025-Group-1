"""
Simple Example: Anthropic Agent with Agent Lookup

This is a minimal example showing how to:
1. Detect @agent-name mentions in user prompts
2. Use the MCP server to look up agent information
3. Provide that context to Claude

Run with:
    python examples/simple_agent_lookup.py
"""

import asyncio
import os
import re
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def lookup_agent_via_mcp(agent_id: str) -> dict:
    """
    Look up an agent using the MCP server.
    
    Args:
        agent_id: The agent ID to look up (e.g., "financial-analyst-001")
        
    Returns:
        Dictionary with agent information or error status
    """
    atlas_url = os.getenv("ATLAS_URL")
    if not atlas_url:
        raise ValueError("ATLAS_URL environment variable is required")
    
    # Configure MCP server connection
    server_params = StdioServerParameters(
        command="python",
        args=["src/agent_mcp.py"],
        env={"ATLAS_URL": atlas_url}
    )
    
    # Connect to MCP server and call get_agent tool
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_agent",
                arguments={"agent_id": agent_id}
            )
            
            # Parse the result
            if result and result.content:
                import json
                agent_data = json.loads(result.content[0].text)
                return agent_data
            
            return {"status": "error", "message": "No response from MCP server"}


def extract_agent_mentions(text: str) -> list[str]:
    """
    Extract @agent-name mentions from text.
    
    Args:
        text: Input text to search
        
    Returns:
        List of agent IDs (without the @ symbol)
    """
    # Match @agent-name pattern (letters, numbers, hyphens, underscores)
    pattern = re.compile(r'@([\w\-]+)')
    matches = pattern.findall(text)
    
    # Filter out common non-agent mentions
    excluded = {'everyone', 'here', 'channel', 'all', 'team'}
    
    return [m for m in matches if m.lower() not in excluded]


async def process_with_agent_context(user_message: str) -> str:
    """
    Process a user message, looking up any mentioned agents and providing
    that context to Claude.
    
    Args:
        user_message: The user's input
        
    Returns:
        Claude's response
    """
    # Extract agent mentions
    agent_ids = extract_agent_mentions(user_message)
    
    # If agents are mentioned, look them up
    agent_context = ""
    if agent_ids:
        print(f"\n🔍 Detected agent mentions: {', '.join(agent_ids)}")
        
        agent_context = "\n\n--- Agent Information from Registry ---\n"
        
        for agent_id in agent_ids:
            try:
                print(f"   Looking up @{agent_id}...")
                agent_info = await lookup_agent_via_mcp(agent_id)
                
                if agent_info.get("status") != "error":
                    print(f"   ✓ Found @{agent_id}")
                    agent_context += f"\n@{agent_id}:\n"
                    agent_context += f"  - Agent URL: {agent_info.get('agent_url')}\n"
                    agent_context += f"  - AgentFacts URL: {agent_info.get('agentFactsURL', 'N/A')}\n"
                else:
                    print(f"   ✗ Agent @{agent_id} not found in registry")
                    agent_context += f"\n@{agent_id}: Not found in registry\n"
            
            except Exception as e:
                print(f"   ✗ Error looking up @{agent_id}: {e}")
                agent_context += f"\n@{agent_id}: Error during lookup\n"
        
        agent_context += "\n--- End of Agent Information ---\n\n"
    
    # Build the full prompt with agent context
    full_prompt = agent_context + user_message if agent_context else user_message
    
    # Call Claude
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system="You are an intelligent agent coordinator. When agents are mentioned using @agent-name syntax, you have access to their information from the NANDA Registry. Help users understand how to connect with and utilize these agents.",
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )
    
    return response.content[0].text


async def main():
    """Run example queries."""
    
    # Check environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("✗ ANTHROPIC_API_KEY environment variable not set")
        return
    
    if not os.getenv("ATLAS_URL"):
        print("✗ ATLAS_URL environment variable not set")
        return
    
    print("\n" + "="*70)
    print("Simple Agent Lookup Example")
    print("="*70 + "\n")
    
    # Example 1: Query with agent mention
    query1 = """
    I need help with financial analysis. Can you connect me with 
    @financial-analyst-001? What can this agent do?
    """
    
    print("Example 1: Single Agent Lookup")
    print("-" * 70)
    print(f"User: {query1.strip()}")
    print()
    
    response1 = await process_with_agent_context(query1)
    print(f"\nClaude: {response1}\n")
    
    print("\n" + "="*70 + "\n")
    
    # Example 2: Query with multiple agents
    query2 = """
    I need to build a data pipeline. Can I use @data-scientist-001 
    for data processing and @financial-analyst-001 for the analysis?
    """
    
    print("Example 2: Multiple Agent Lookup")
    print("-" * 70)
    print(f"User: {query2.strip()}")
    print()
    
    response2 = await process_with_agent_context(query2)
    print(f"\nClaude: {response2}\n")
    
    print("\n" + "="*70 + "\n")
    
    # Example 3: Query without agent mentions (should work normally)
    query3 = "What is the NANDA Registry?"
    
    print("Example 3: No Agent Mentions")
    print("-" * 70)
    print(f"User: {query3}")
    print()
    
    response3 = await process_with_agent_context(query3)
    print(f"\nClaude: {response3}\n")


if __name__ == "__main__":
    asyncio.run(main())
