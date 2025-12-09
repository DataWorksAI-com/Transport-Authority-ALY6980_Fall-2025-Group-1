"""
Example Anthropic Agent with MCP Integration

This example shows how to create an agent that:
1. Connects to the NANDA Registry MCP server
2. Detects @agent-name syntax in prompts
3. Calls get_agent to retrieve agent information
4. Uses the agent URL to communicate with other agents

Requirements:
- anthropic
- mcp (Model Context Protocol SDK)
- python-dotenv
"""

import asyncio
import os
import re
from typing import Optional
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentAwareClaude:
    """
    Claude agent that can discover and communicate with other agents
    via the NANDA Registry MCP server.
    """
    
    def __init__(self, api_key: Optional[str] = None, mcp_server_path: str = "src/agent_mcp.py"):
        """
        Initialize the agent-aware Claude instance.
        
        Args:
            api_key: Anthropic API key (reads from ANTHROPIC_API_KEY env var if not provided)
            mcp_server_path: Path to the MCP server script
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")
        
        self.anthropic = Anthropic(api_key=self.api_key)
        self.mcp_server_path = mcp_server_path
        self.mcp_session = None
        
        # Regex to match @agent-name syntax (but not @mentions in other contexts)
        # Matches @agent-name, @agent_name, @agent-123, etc.
        self.agent_mention_pattern = re.compile(r'@([\w\-]+(?:\-\d+)?)')
    
    async def start_mcp_connection(self):
        """Start connection to the MCP server."""
        atlas_url = os.getenv("ATLAS_URL")
        if not atlas_url:
            raise ValueError("ATLAS_URL environment variable is required")
        
        server_params = StdioServerParameters(
            command="python",
            args=[self.mcp_server_path],
            env={"ATLAS_URL": atlas_url}
        )
        
        # Store the context managers
        self.stdio_context = stdio_client(server_params)
        read, write = await self.stdio_context.__aenter__()
        
        self.session_context = ClientSession(read, write)
        self.mcp_session = await self.session_context.__aenter__()
        await self.mcp_session.initialize()
        
        print("✓ Connected to NANDA Registry MCP server")
    
    async def close_mcp_connection(self):
        """Close connection to the MCP server."""
        if self.mcp_session:
            await self.session_context.__aexit__(None, None, None)
            await self.stdio_context.__aexit__(None, None, None)
            print("✓ Disconnected from MCP server")
    
    def extract_agent_mentions(self, text: str) -> list[str]:
        """
        Extract agent mentions from text.
        
        Filters out common non-agent mentions like @everyone, @here, email addresses, etc.
        
        Args:
            text: Text to search for agent mentions
            
        Returns:
            List of agent IDs mentioned
        """
        matches = self.agent_mention_pattern.findall(text)
        
        # Filter out common non-agent patterns
        excluded_patterns = {
            'everyone', 'here', 'channel', 'all', 'team',
            'gmail', 'yahoo', 'hotmail', 'outlook'  # Common email domains
        }
        
        agent_ids = []
        for match in matches:
            # Skip if it's a common non-agent mention
            if match.lower() in excluded_patterns:
                continue
            
            # Skip if it looks like part of an email (has a dot after @)
            # This is a simple heuristic - adjust as needed
            agent_ids.append(match)
        
        return list(set(agent_ids))  # Remove duplicates
    
    async def lookup_agent(self, agent_id: str) -> Optional[dict]:
        """
        Look up an agent in the registry using the MCP server.
        
        Args:
            agent_id: The agent ID to look up
            
        Returns:
            Agent information dictionary or None if not found
        """
        if not self.mcp_session:
            raise RuntimeError("MCP connection not established. Call start_mcp_connection() first.")
        
        try:
            result = await self.mcp_session.call_tool(
                "get_agent",
                arguments={"agent_id": agent_id}
            )
            
            # Parse the result
            if result and isinstance(result.content, list) and len(result.content) > 0:
                # Extract text content from the result
                content = result.content[0]
                if hasattr(content, 'text'):
                    import json
                    agent_data = json.loads(content.text)
                    
                    if agent_data.get("status") == "error":
                        print(f"⚠️  Agent '{agent_id}' not found in registry")
                        return None
                    
                    return agent_data
            
            return None
            
        except Exception as e:
            print(f"✗ Error looking up agent '{agent_id}': {e}")
            return None
    
    async def process_message(self, user_message: str, conversation_history: list = None) -> str:
        """
        Process a user message, detecting and resolving agent mentions.
        
        Args:
            user_message: The user's input message
            conversation_history: Optional conversation history
            
        Returns:
            Claude's response
        """
        if conversation_history is None:
            conversation_history = []
        
        # Extract agent mentions
        agent_mentions = self.extract_agent_mentions(user_message)
        
        # Look up agents if any are mentioned
        agent_context = {}
        if agent_mentions:
            print(f"\n🔍 Detected agent mentions: {', '.join(agent_mentions)}")
            
            for agent_id in agent_mentions:
                agent_info = await self.lookup_agent(agent_id)
                if agent_info:
                    agent_context[agent_id] = agent_info
                    print(f"✓ Found agent: {agent_id} at {agent_info.get('agent_url')}")
        
        # Build the enhanced prompt with agent context
        enhanced_prompt = user_message
        
        if agent_context:
            context_text = "\n\n--- Agent Registry Information ---\n"
            context_text += "The following agents were mentioned and found in the NANDA Registry:\n\n"
            
            for agent_id, info in agent_context.items():
                context_text += f"@{agent_id}:\n"
                context_text += f"  - URL: {info.get('agent_url')}\n"
                context_text += f"  - AgentFacts: {info.get('agentFactsURL', 'N/A')}\n"
                context_text += "\n"
            
            context_text += "You can now communicate with these agents using their URLs.\n"
            context_text += "---\n\n"
            
            enhanced_prompt = context_text + user_message
        
        # Build message history
        messages = conversation_history + [
            {"role": "user", "content": enhanced_prompt}
        ]
        
        # Call Claude API
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            system="You are an intelligent agent coordinator. When users mention other agents using @agent-name syntax, you help them discover and communicate with those agents through the NANDA Registry. You understand agent URLs and can help orchestrate multi-agent interactions.",
            messages=messages
        )
        
        return response.content[0].text
    
    async def chat_loop(self):
        """Run an interactive chat loop."""
        print("\n" + "="*70)
        print("Agent-Aware Claude - NANDA Registry Integration")
        print("="*70)
        print("\nUse @agent-name to reference agents in the registry.")
        print("Type 'quit' or 'exit' to end the conversation.\n")
        
        conversation_history = []
        
        try:
            await self.start_mcp_connection()
            
            while True:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye! 👋")
                    break
                
                if not user_input:
                    continue
                
                # Process message
                response = await self.process_message(user_input, conversation_history)
                
                # Update conversation history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})
                
                # Keep only last 10 exchanges (20 messages)
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
                
                # Display response
                print(f"\nClaude: {response}")
        
        finally:
            await self.close_mcp_connection()


async def example_single_query():
    """Example of processing a single query with agent mentions."""
    print("\n" + "="*70)
    print("Example: Single Query with Agent Mentions")
    print("="*70 + "\n")
    
    agent = AgentAwareClaude()
    
    try:
        await agent.start_mcp_connection()
        
        # Example query mentioning agents
        query = """
        I need to analyze a financial report. Can you connect me with 
        @financial-analyst-001 and also check if @data-scientist-001 
        is available to help with the data visualization?
        """
        
        print(f"User Query:\n{query}\n")
        
        response = await agent.process_message(query)
        
        print(f"\nClaude Response:\n{response}\n")
    
    finally:
        await agent.close_mcp_connection()


async def example_list_agents():
    """Example of listing all available agents."""
    print("\n" + "="*70)
    print("Example: List All Available Agents")
    print("="*70 + "\n")
    
    agent = AgentAwareClaude()
    
    try:
        await agent.start_mcp_connection()
        
        # Call list_agents tool
        result = await agent.mcp_session.call_tool(
            "list_agents",
            arguments={}
        )
        
        import json
        if result and isinstance(result.content, list) and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, 'text'):
                agents_data = json.loads(content.text)
                
                print(f"Found {agents_data.get('count', 0)} agents:\n")
                
                for agent_info in agents_data.get('agents', []):
                    print(f"  @{agent_info.get('agent_id')}")
                    print(f"    URL: {agent_info.get('agent_url')}")
                    print(f"    Facts: {agent_info.get('agentFactsURL', 'N/A')}")
                    print()
    
    finally:
        await agent.close_mcp_connection()


async def main():
    """Main entry point with example selection."""
    import sys
    
    print("\nNANDA Registry - Anthropic Agent Example")
    print("="*70)
    print("\nChoose an example:")
    print("1. Interactive chat loop")
    print("2. Single query example")
    print("3. List all agents")
    print("q. Quit")
    
    choice = input("\nEnter your choice (1-3 or q): ").strip()
    
    if choice == '1':
        agent = AgentAwareClaude()
        await agent.chat_loop()
    elif choice == '2':
        await example_single_query()
    elif choice == '3':
        await example_list_agents()
    elif choice.lower() == 'q':
        print("Goodbye! 👋")
    else:
        print("Invalid choice. Please run again and select 1-3 or q.")


if __name__ == "__main__":
    # Check required environment variables
    required_vars = ["ANTHROPIC_API_KEY", "ATLAS_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("✗ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables and try again.")
        print("Example:")
        print('  export ANTHROPIC_API_KEY="your-api-key"')
        print('  export ATLAS_URL="mongodb+srv://..."')
        exit(1)
    
    asyncio.run(main())
