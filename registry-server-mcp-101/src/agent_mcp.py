"""
NANDA Registry MCP Server
Exposes agent registration, discovery, and facts functionality via Model Context Protocol
"""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional
try:
    from .services import RegistryService
except ImportError:
    # Fallback for when running directly with fastmcp CLI
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from services import RegistryService

# Initialize FastMCP server
mcp = FastMCP("NANDA Registry Server")

# Initialize registry service (shared business logic)
registry = RegistryService()


# Add health check resource for MCP client transport
@mcp.resource("health://check")
def health_resource() -> str:
    """Health check resource for monitoring"""
    result = registry.health_check()
    return f"Status: {result.get('status', 'unknown')}, MongoDB: {result.get('mongodb', 'unknown')}"


# Add health check resource for HTTP/SSE transport
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse(registry.health_check())


@mcp.tool()
def register_agent(
    agent_id: str,
    agent_url: str,
    capabilities: list[str] = None,
    domain: str = "general",
    specialization: str = "general",
    description: str = None,
    modalities: list[str] = None,
    languages: list[str] = None,
    streaming: bool = False,
    batch: bool = True
) -> dict:
    """
    Register a new agent with the NANDA registry.
    
    Args:
        agent_id: Unique identifier for the agent
        agent_url: URL endpoint for the agent
        capabilities: List of agent capabilities (default: ["chat"])
        domain: Agent domain (default: "general")
        specialization: Agent specialization (default: "general")
        description: Agent description (auto-generated if not provided)
        modalities: Supported modalities (default: ["text"])
        languages: Supported languages (default: ["en"])
        streaming: Whether agent supports streaming (default: False)
        batch: Whether agent supports batch processing (default: True)
    
    Returns:
        Dictionary with registration status and agent details
    """
    try:
        return registry.register_agent(
            agent_id=agent_id,
            agent_url=agent_url,
            capabilities=capabilities,
            domain=domain,
            specialization=specialization,
            description=description,
            modalities=modalities,
            languages=languages,
            streaming=streaming,
            batch=batch
        )
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def list_agents(status: Optional[str] = None) -> dict:
    """
    List all registered agents.
    
    Args:
        status: Optional status filter
    
    Returns:
        Dictionary containing list of agents and count
    """
    return registry.list_agents(status=status)


@mcp.tool()
def search_agents(
    capabilities: Optional[str] = None,
    domain: Optional[str] = None,
    query: Optional[str] = None
) -> dict:
    """
    Search for agents by capabilities, domain, or query string.
    
    Args:
        capabilities: Filter by capabilities
        domain: Filter by domain
        query: Search term for agent_id or agent_url
    
    Returns:
        Dictionary containing matching agents and count
    """
    return registry.search_agents(
        capabilities=capabilities,
        domain=domain,
        query=query
    )


@mcp.tool()
def get_agent(agent_id: str) -> dict:
    """
    Get details for a specific agent by agent_id.
    
    Args:
        agent_id: The unique identifier of the agent
    
    Returns:
        Agent details dictionary
    """
    try:
        return registry.get_agent(agent_id=agent_id)
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def update_agent(agent_id: str, agent_url: Optional[str] = None) -> dict:
    """
    Update agent information.
    
    Args:
        agent_id: The unique identifier of the agent to update
        agent_url: New agent URL (optional)
    
    Returns:
        Dictionary with update status
    """
    try:
        return registry.update_agent(agent_id=agent_id, agent_url=agent_url)
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def delete_agent(agent_id: str) -> dict:
    """
    Delete an agent from the registry.
    
    Args:
        agent_id: The unique identifier of the agent to delete
    
    Returns:
        Dictionary with deletion status
    """
    try:
        return registry.delete_agent(agent_id=agent_id)
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_agent_facts(username: str) -> dict:
    """
    Get agent facts by username from the facts database.
    
    Args:
        username: The username/agent_name to lookup
    
    Returns:
        Agent facts dictionary
    """
    try:
        return registry.get_agent_facts(username=username)
    except ValueError as e:
        return {"status": "error", "message": str(e)}


# For running via MCP protocol
if __name__ == "__main__":
    mcp.run()
