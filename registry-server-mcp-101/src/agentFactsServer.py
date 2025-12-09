# agent_facts_server.py
from fastapi import FastAPI, HTTPException
from .services import RegistryService

app = FastAPI()

# Initialize registry service (shared business logic)
registry = RegistryService()

@app.get("/@{username}.json")
def get_agent_facts(username: str):
    try:
        return registry.get_agent_facts(username=username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/health")
def health_check():
    """Health check"""
    return registry.health_check()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)