"""
A2A Agent Communication Example

This example builds upon the native MCP tool calling and adds the ability to:
1. Detect when the user is asking an agent to do something
2. Look up the agent via MCP get_agent tool
3. Communicate with the agent using the A2A protocol

Example queries:
- "Ask agent data-scientist-761966 to tell me which data science techniques it can apply"
- "Tell financial-analyst-001 to analyze my portfolio"
- "Request from marketing-agent-123 to create a campaign"
"""

import asyncio
import os
import json
from typing import Optional
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import MessageSendParams, SendMessageRequest, Message, Role, TextPart, Part
from uuid import uuid4


class A2AAwareAgent:
    """
    An agent that integrates Claude with MCP tools AND A2A communication.
    
    Flow:
    1. Claude sees MCP tools and a local send_a2a_message tool
    2. User asks something like "Ask agent-123 to do X"
    3. Claude calls get_agent to look up the agent
    4. Claude calls send_a2a_message with the agent URL and message
    5. This code communicates with the agent via A2A protocol
    """
    
    def __init__(self, api_key: Optional[str] = None, mcp_server_path: str = "../../src/agent_mcp.py"):
        """
        Initialize the A2A-aware agent.
        
        Args:
            api_key: Anthropic API key
            mcp_server_path: Path to the MCP server script
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
        
        self.anthropic = Anthropic(api_key=self.api_key)
        self.mcp_server_path = mcp_server_path
        self.mcp_session = None
        self.mcp_tools = []
        self.httpx_client = None
    
    async def start(self):
        """Start MCP connection and HTTP client."""
        await self.start_mcp_connection()
        self.httpx_client = httpx.AsyncClient(timeout=30.0)
    
    async def stop(self):
        """Stop connections."""
        await self.close_mcp_connection()
        if self.httpx_client:
            await self.httpx_client.aclose()
    
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
        
        self.stdio_context = stdio_client(server_params)
        read, write = await self.stdio_context.__aenter__()
        
        self.session_context = ClientSession(read, write)
        self.mcp_session = await self.session_context.__aenter__()
        await self.mcp_session.initialize()
        
        # Get available tools from MCP server
        tools_result = await self.mcp_session.list_tools()
        self.mcp_tools = tools_result.tools if tools_result else []
        
        print(f"✓ Connected to NANDA Registry MCP server")
        print(f"✓ Available MCP tools: {len(self.mcp_tools)}")
    
    async def close_mcp_connection(self):
        """Close connection to the MCP server."""
        if self.mcp_session:
            await self.session_context.__aexit__(None, None, None)
            await self.stdio_context.__aexit__(None, None, None)
            print("✓ Disconnected from MCP server")
    
    def convert_mcp_tools_to_anthropic_format(self) -> list[dict]:
        """Convert MCP tool schemas to Anthropic's tool format."""
        anthropic_tools = []
        
        for tool in self.mcp_tools:
            tool_def = {
                "name": tool.name,
                "description": tool.description or f"Tool: {tool.name}",
            }
            
            if tool.inputSchema:
                tool_def["input_schema"] = tool.inputSchema
            
            anthropic_tools.append(tool_def)
        
        return anthropic_tools
    
    def get_local_tools(self) -> list[dict]:
        """
        Define local tools that are NOT in the MCP server.
        These are handled by this Python code directly.
        """
        return [
            {
                "name": "send_a2a_message",
                "description": "Send a message to an agent using the A2A protocol. Use this after looking up an agent's URL via get_agent. The agent_url should end with '/a2a' - if it doesn't, this tool will append it automatically.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_url": {
                            "type": "string",
                            "description": "The URL of the agent to communicate with (from get_agent result)"
                        },
                        "message": {
                            "type": "string",
                            "description": "The message to send to the agent"
                        },
                        "context_id": {
                            "type": "string",
                            "description": "Optional context ID for multi-turn conversations"
                        }
                    },
                    "required": ["agent_url", "message"]
                }
            }
        ]
    
    async def send_a2a_message(
        self,
        agent_url: str,
        message: str,
        context_id: Optional[str] = None
    ) -> dict:
        """
        Send a message to an agent via A2A protocol.
        
        Args:
            agent_url: The agent's URL (will append /a2a if not present)
            message: The message to send
            context_id: Optional context ID for multi-turn conversations
            
        Returns:
            Dictionary with the agent's response
        """
        # Ensure URL ends with /a2a
        if not agent_url.endswith('/a2a'):
            if agent_url.endswith('/'):
                agent_url += 'a2a'
            else:
                agent_url += '/a2a'
        
        print(f"\n📡 Sending A2A message to: {agent_url}")
        print(f"   Message: {message[:100]}...")
        
        try:
            # Get agent card
            base_url = agent_url.replace('/a2a', '')
            resolver = A2ACardResolver(
                httpx_client=self.httpx_client,
                base_url=base_url
            )
            agent_card = await resolver.get_agent_card()
            
            print(f"   ✓ Got agent card: {agent_card.name}")
            
            # Create A2A client
            client = A2AClient(
                httpx_client=self.httpx_client,
                agent_card=agent_card,
                url=base_url
            )
            
            # Prepare message
            message_obj = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=message))],
                message_id=str(uuid4()),
                context_id=context_id
            )
            
            # Send message
            params = MessageSendParams(message=message_obj)
            request = SendMessageRequest(id=str(uuid4()), params=params)
            
            response = await client.send_message(request)
            
            print(f"   ✓ Received response from agent")
            
            # Extract text from response
            response_text = ""
            if hasattr(response.root, 'result'):
                result = response.root.result
                if hasattr(result, 'artifact') and result.artifact:
                    for part in result.artifact.parts:
                        if hasattr(part.root, 'text'):
                            response_text += part.root.text
            
            return {
                "status": "success",
                "agent_name": agent_card.name,
                "response": response_text or str(response.model_dump(mode='json', exclude_none=True)),
                "full_response": response.model_dump(mode='json', exclude_none=True)
            }
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to communicate with agent via A2A"
            }
    
    async def process_message(
        self,
        user_message: str,
        conversation_history: list = None,
        max_iterations: int = 10
    ) -> str:
        """
        Process a user message with Claude, allowing it to call both MCP tools
        and local A2A communication tools.
        """
        if conversation_history is None:
            conversation_history = []
        
        # Combine MCP tools and local tools
        mcp_tools = self.convert_mcp_tools_to_anthropic_format()
        local_tools = self.get_local_tools()
        all_tools = mcp_tools + local_tools
        
        # Build message history
        messages = conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        print(f"\n💬 User: {user_message}")
        
        # Agentic loop
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Call Claude with all available tools
            response = self.anthropic.messages.create(
                model="claude-haiku-4-5",
                max_tokens=4096,
                system="""You are an intelligent agent coordinator with access to the NANDA Registry and A2A communication capabilities.

You have two types of tools:

1. MCP Registry Tools (for agent discovery):
   - register_agent, list_agents, search_agents, get_agent
   - update_agent, delete_agent, get_agent_facts, health_check

2. A2A Communication Tool (for talking to agents):
   - send_a2a_message: Send messages to agents via A2A protocol

When users ask you to communicate with an agent (e.g., "Ask agent-123 to do X"), follow this pattern:
1. Use get_agent to look up the agent and get its URL
2. Use send_a2a_message with the agent's URL and the user's request

Be natural and conversational. You don't need special syntax - just understand the user's intent.""",
                messages=messages,
                tools=all_tools
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
                        
                        # Check if it's a local tool or MCP tool
                        if tool_name == "send_a2a_message":
                            # Handle local A2A tool
                            try:
                                result = await self.send_a2a_message(
                                    agent_url=tool_input.get("agent_url"),
                                    message=tool_input.get("message"),
                                    context_id=tool_input.get("context_id")
                                )
                                
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(result)
                                })
                            except Exception as e:
                                print(f"   ✗ Error: {e}")
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps({"error": str(e)})
                                })
                        else:
                            # Handle MCP tool
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
                
                # Add assistant's response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                
                # Continue the loop
                continue
            
            elif response.stop_reason == "end_turn":
                # Claude is done
                final_text = ""
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        final_text += content_block.text
                
                return final_text
            
            else:
                print(f"⚠️  Unexpected stop reason: {response.stop_reason}")
                break
        
        # If we hit max iterations
        print(f"⚠️  Reached maximum iterations ({max_iterations})")
        final_text = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                final_text += content_block.text
        return final_text or "Maximum iterations reached."
    
    async def chat_loop(self):
        """Run an interactive chat loop."""
        print("\n" + "="*70)
        print("A2A-Aware Claude - Agent Communication via A2A Protocol")
        print("="*70)
        print("\nClaude can discover agents via MCP and communicate with them via A2A!")
        print("\nExamples:")
        print("  - 'Ask agent data-scientist-761966 to list its capabilities'")
        print("  - 'Tell financial-analyst-001 to analyze my portfolio'")
        print("  - 'Request from agent-123 to help with data analysis'")
        print("\nType 'quit' or 'exit' to end the conversation.\n")
        
        conversation_history = []
        
        await self.start()
        
        try:
            while True:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye! 👋")
                    break
                
                if not user_input:
                    continue
                
                # Process message
                response = await self.process_message(user_input, conversation_history)
                
                # Display response
                print(f"\n🤖 Claude: {response}")
        
        finally:
            await self.stop()


async def example_queries():
    """Run example queries demonstrating A2A communication."""
    print("\n" + "="*70)
    print("Example: Agent Communication via A2A Protocol")
    print("="*70 + "\n")
    
    agent = A2AAwareAgent()
    
    try:
        await agent.start()
        
        examples = [
            "What agents are currently registered?",
            "Get the details for agent data-scientist-001",
            "Ask agent financial-analyst-001 to analyze a sample portfolio",
        ]
        
        for query in examples:
            print("\n" + "-"*70)
            response = await agent.process_message(query)
            print(f"\n🤖 Claude: {response}\n")
            print("-"*70)
            
            await asyncio.sleep(1)
    
    finally:
        await agent.stop()


async def main():
    """Main entry point."""
    print("\nNANDA Registry - A2A Agent Communication")
    print("="*70)
    print("\nChoose an example:")
    print("1. Interactive chat (with A2A communication)")
    print("2. Run example queries")
    print("q. Quit")
    
    choice = input("\nEnter your choice (1-2 or q): ").strip()
    
    if choice == '1':
        agent = A2AAwareAgent()
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
        exit(1)
    
    asyncio.run(main())
