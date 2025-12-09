"""
Anthropic Agent with Native MCP Tool Integration

This example demonstrates proper MCP integration where:
1. Claude receives the user's prompt
2. Claude sees available MCP tools in its tool schema
3. Claude automatically decides when to call MCP tools
4. Claude receives tool results and blends them into its response

This is the recommended pattern for MCP integration.
"""

import asyncio
import os
import json
from typing import Optional
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPAwareAgent:
    """
    An agent that integrates Claude with MCP tools.
    Claude automatically calls MCP tools when needed based on user requests.
    """
    
    def __init__(self, api_key: Optional[str] = None, mcp_server_path: str = "../../src/agent_mcp.py"):
        """
        Initialize the MCP-aware agent.
        
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
        self.mcp_tools = []
    
    async def start_mcp_connection(self):
        """Start connection to the MCP server and retrieve available tools."""
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
        
        # Get available tools from MCP server
        tools_result = await self.mcp_session.list_tools()
        self.mcp_tools = tools_result.tools if tools_result else []
        
        print(f"✓ Connected to NANDA Registry MCP server")
        print(f"✓ Available tools: {len(self.mcp_tools)}")
        for tool in self.mcp_tools:
            print(f"  - {tool.name}")
    
    async def close_mcp_connection(self):
        """Close connection to the MCP server."""
        if self.mcp_session:
            await self.session_context.__aexit__(None, None, None)
            await self.stdio_context.__aexit__(None, None, None)
            print("✓ Disconnected from MCP server")
    
    def convert_mcp_tools_to_anthropic_format(self) -> list[dict]:
        """
        Convert MCP tool schemas to Anthropic's tool format.
        
        Returns:
            List of tool definitions in Anthropic's format
        """
        anthropic_tools = []
        
        for tool in self.mcp_tools:
            # Convert MCP tool schema to Anthropic format
            tool_def = {
                "name": tool.name,
                "description": tool.description or f"Tool: {tool.name}",
            }
            
            # Convert input schema if available
            if tool.inputSchema:
                tool_def["input_schema"] = tool.inputSchema
            
            anthropic_tools.append(tool_def)
        
        return anthropic_tools
    
    async def process_message(
        self, 
        user_message: str, 
        conversation_history: list = None,
        max_iterations: int = 5
    ) -> str:
        """
        Process a user message, allowing Claude to automatically call MCP tools as needed.
        
        Args:
            user_message: The user's input message
            conversation_history: Optional conversation history
            max_iterations: Maximum number of tool-calling iterations
            
        Returns:
            Claude's final response
        """
        if conversation_history is None:
            conversation_history = []
        
        # Convert MCP tools to Anthropic format
        tools = self.convert_mcp_tools_to_anthropic_format()
        
        # Build message history
        messages = conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        print(f"\n💬 User: {user_message}")
        
        # Agentic loop: let Claude call tools as needed
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Call Claude with available tools
            response = self.anthropic.messages.create(
                model="claude-haiku-4-5",
                max_tokens=4096,
                system="""You are an intelligent agent coordinator with access to the NANDA Registry.
                
You have tools to interact with the registry:
- register_agent: Register new agents
- list_agents: List all registered agents
- search_agents: Search for agents by capabilities, domain, or query
- get_agent: Get details for a specific agent by ID
- update_agent: Update agent information
- delete_agent: Delete an agent
- get_agent_facts: Get detailed facts about an agent
- health_check: Check system health

When users ask about agents, use these tools to look up information. You don't need special syntax like @agent-name - just understand the user's intent and call the appropriate tools.""",
                messages=messages,
                tools=tools
            )
            
            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                print(f"\n🔧 Claude is using tools (iteration {iteration})...")
                
                # Process each tool use
                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id
                        
                        print(f"   Calling: {tool_name}({json.dumps(tool_input, indent=2)})")
                        
                        # Call the MCP tool
                        try:
                            mcp_result = await self.mcp_session.call_tool(
                                tool_name,
                                arguments=tool_input
                            )
                            
                            # Extract text content from MCP result
                            if mcp_result and mcp_result.content:
                                result_text = ""
                                for content in mcp_result.content:
                                    if hasattr(content, 'text'):
                                        result_text += content.text
                                    elif isinstance(content, str):
                                        result_text += content
                                
                                print(f"   ✓ Result: {result_text[:100]}...")
                                
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": result_text
                                })
                            else:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps({"error": "No result from tool"})
                                })
                        
                        except Exception as e:
                            print(f"   ✗ Error: {e}")
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps({"error": str(e)})
                            })
                
                # Add assistant's response (with tool use) and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                
                # Continue the loop to let Claude process the tool results
                continue
            
            elif response.stop_reason == "end_turn":
                # Claude is done, extract the final text response
                final_text = ""
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        final_text += content_block.text
                
                return final_text
            
            else:
                # Unexpected stop reason
                print(f"⚠️  Unexpected stop reason: {response.stop_reason}")
                break
        
        # If we hit max iterations, return what we have
        print(f"⚠️  Reached maximum iterations ({max_iterations})")
        final_text = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                final_text += content_block.text
        return final_text or "Maximum iterations reached without completing the request."
    
    async def chat_loop(self):
        """Run an interactive chat loop."""
        print("\n" + "="*70)
        print("MCP-Aware Claude - Native Tool Integration")
        print("="*70)
        print("\nClaude can automatically call MCP tools based on your requests.")
        print("Try asking about agents naturally - no special syntax needed!")
        print("\nExamples:")
        print("  - 'What agents are registered?'")
        print("  - 'Tell me about financial-analyst-001'")
        print("  - 'Search for agents with financial capabilities'")
        print("\nType 'quit' or 'exit' to end the conversation.\n")
        
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
                
                # Process message (Claude will call tools automatically)
                response = await self.process_message(user_input, conversation_history)
                
                # Update conversation history (keep the full message history)
                # Note: conversation_history is already updated in process_message
                # We just need to keep track for context
                
                # Display response
                print(f"\n🤖 Claude: {response}")
        
        finally:
            await self.close_mcp_connection()


async def example_queries():
    """Run several example queries demonstrating automatic tool use."""
    print("\n" + "="*70)
    print("Example: Natural Language Queries with Automatic Tool Calling")
    print("="*70 + "\n")
    
    agent = MCPAwareAgent()
    
    try:
        await agent.start_mcp_connection()
        
        examples = [
            "What agents are currently registered?",
            "Tell me about the agent with ID financial-analyst-001",
            "Search for agents that can help with data analysis",
            "Is the registry system healthy?",
        ]
        
        for query in examples:
            print("\n" + "-"*70)
            response = await agent.process_message(query)
            print(f"\n🤖 Claude: {response}\n")
            print("-"*70)
            
            # Small delay between queries
            await asyncio.sleep(1)
    
    finally:
        await agent.close_mcp_connection()


async def main():
    """Main entry point with example selection."""
    print("\nNANDA Registry - MCP Native Tool Integration")
    print("="*70)
    print("\nChoose an example:")
    print("1. Interactive chat (Claude calls tools automatically)")
    print("2. Run example queries")
    print("q. Quit")
    
    choice = input("\nEnter your choice (1-2 or q): ").strip()
    
    if choice == '1':
        agent = MCPAwareAgent()
        await agent.chat_loop()
    elif choice == '2':
        await example_queries()
    elif choice.lower() == 'q':
        print("Goodbye! 👋")
    else:
        print("Invalid choice. Please run again and select 1-2 or q.")


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
