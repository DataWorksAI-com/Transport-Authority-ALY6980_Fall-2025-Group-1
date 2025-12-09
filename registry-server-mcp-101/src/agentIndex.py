from fastapi import FastAPI, HTTPException
from typing import Optional
from .services import RegistryService

app = FastAPI(title="Simple NANDA Registry")

# Initialize registry service (shared business logic)
registry = RegistryService()
@app.get("/")
def root():
    return {"message": "Simple NANDA Registry", "status": "running"}

@app.post("/register")
def register_agent(agent_data: dict):
    """Register an agent with full capability data - supports both old and new schemas"""

    # Validate required fields
    if not agent_data.get("agent_id"):
        raise HTTPException(status_code=400, detail="agent_id is required")
    if not agent_data.get("agent_url"):
        raise HTTPException(status_code=400, detail="agent_url is required")

    # Extract agent capabilities and metadata
    capabilities = agent_data.get("capabilities", ["chat"])
    domain = agent_data.get("domain", "general")
    specialization = agent_data.get("specialization", "general")
    description = agent_data.get("description")
    modalities = agent_data.get("modalities", ["text"])
    languages = agent_data.get("languages", ["en"])
    streaming = agent_data.get("streaming", False)
    batch = agent_data.get("batch", True)

    try:
        return registry.register_agent(
            agent_id=agent_data["agent_id"],
            agent_url=agent_data["agent_url"],
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
        if "duplicate key" in str(e) or "already exists" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list")
def list_agents(status: Optional[str] = None):
    """List all agents"""
    return registry.list_agents(status=status)

@app.get("/search")
def search_agents(
    capabilities: Optional[str] = None,
    domain: Optional[str] = None,
    q: Optional[str] = None
):
    """Search agents by capabilities, domain, or query"""
    return registry.search_agents(
        capabilities=capabilities,
        domain=domain,
        query=q
    )

@app.get("/lookup/{agent_id}")
def get_agent(agent_id: str):
    """Get specific agent by agent_id"""
    try:
        return registry.get_agent(agent_id=agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/update/{agent_id}")
def update_agent_capabilities(agent_id: str, update_data: dict):
    """Update agent basic info (AgentFacts are managed externally)"""
    try:
        return registry.update_agent(
            agent_id=agent_id,
            agent_url=update_data.get("agent_url")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: str):
    """Delete agent from registry (AgentFacts managed externally)"""
    try:
        return registry.delete_agent(agent_id=agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/health")
def health_check():
    """Health check"""
    return registry.health_check()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6900)