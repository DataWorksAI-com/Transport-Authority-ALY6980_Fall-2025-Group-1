"""
NANDA Registry Service Layer
Shared business logic for agent registration and management
Used by both FastAPI and FastMCP implementations
"""

from pymongo import MongoClient
from datetime import datetime
from typing import Optional, Dict, List, Any
import os
import requests


class RegistryService:
    """Service class for agent registration and management operations."""
    
    def __init__(self, atlas_url: Optional[str] = None):
        """
        Initialize the registry service with MongoDB connections.
        
        Args:
            atlas_url: MongoDB Atlas connection string (defaults to ATLAS_URL env var)
        """
        self.atlas_url = atlas_url or os.getenv("ATLAS_URL")
        if not self.atlas_url:
            raise ValueError("ATLAS_URL must be provided or set as environment variable")
        
        # Agent Index DB
        self.index_client = MongoClient(self.atlas_url)
        self.index_db = self.index_client.nanda_private_registry
        self.agents = self.index_db.agents
        
        # Agent Facts DB
        self.facts_client = MongoClient(self.atlas_url)
        self.facts_db = self.facts_client.nanda_private_registry
        self.agent_facts = self.facts_db.agent_facts
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary database indexes."""
        try:
            self.agents.create_index("agent_id", unique=True, sparse=True)
        except Exception as e:
            print(f"Agent_id index already exists or creation failed: {e}")
    
    def _create_agent_facts_payload(
        self,
        agent_id: str,
        description: str,
        capabilities: List[str],
        modalities: List[str],
        languages: List[str],
        streaming: bool,
        batch: bool
    ) -> Dict[str, Any]:
        """
        Create payload for external AgentFacts API.
        
        Args:
            agent_id: Agent identifier
            description: Agent description
            capabilities: List of capabilities
            modalities: Supported modalities
            languages: Supported languages
            streaming: Streaming support
            batch: Batch processing support
            
        Returns:
            Dictionary payload for AgentFacts API
        """
        clean_username = agent_id.replace("-", "_")
        
        return {
            "username": clean_username,
            "agent_name": agent_id,
            "description": description,
            "capabilities": {
                "modalities": modalities,
                "streaming": streaming,
                "batch": batch
            },
            "skills": [
                {
                    "id": skill,
                    "description": f"Expert {skill.replace('_', ' ')} capability",
                    "inputModes": ["text"],
                    "outputModes": ["text"],
                    "supportedLanguages": languages,
                    "latencyBudgetMs": 2000,
                    "maxTokens": 4000
                } for skill in capabilities
            ],
            "evaluations": {
                "performanceScore": 92.0
            },
            "certification": {
                "level": "Certified",
                "issuer": "Your Authority"
            }
        }
    
    def _call_agent_facts_api(self, payload: Dict[str, Any], agent_id: str) -> str:
        """
        Call external AgentFacts API to create agent facts.
        
        Args:
            payload: AgentFacts payload
            agent_id: Agent identifier for logging
            
        Returns:
            AgentFacts URL (regardless of success/failure)
        """
        clean_username = agent_id.replace("-", "_")
        agent_facts_url = f"https://list39.org/@{clean_username}.json"
        
        try:
            response = requests.post(
                "https://join39.org/api/public-agent-facts",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"AgentFacts created successfully for {agent_id} (username: {clean_username})")
            else:
                print(f"AgentFacts creation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error calling AgentFacts API: {e}")
        
        return agent_facts_url
    
    def register_agent(
        self,
        agent_id: str,
        agent_url: str,
        capabilities: Optional[List[str]] = None,
        domain: str = "general",
        specialization: str = "general",
        description: Optional[str] = None,
        modalities: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        streaming: bool = False,
        batch: bool = True
    ) -> Dict[str, Any]:
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
            
        Raises:
            ValueError: If agent_id already exists or other validation errors
        """
        # Set defaults
        if capabilities is None:
            capabilities = ["chat"]
        if modalities is None:
            modalities = ["text"]
        if languages is None:
            languages = ["en"]
        if description is None:
            description = f"Expert {specialization} agent in {domain} domain"
        
        # Create agent document
        agent_dict = {
            "agent_id": agent_id,
            "agent_url": agent_url
        }
        
        # Create AgentFacts via external API
        agent_facts_payload = self._create_agent_facts_payload(
            agent_id=agent_id,
            description=description,
            capabilities=capabilities,
            modalities=modalities,
            languages=languages,
            streaming=streaming,
            batch=batch
        )
        
        # Call external API and get URL
        agent_dict["agentFactsURL"] = self._call_agent_facts_api(
            agent_facts_payload,
            agent_id
        )
        
        # Insert into MongoDB
        try:
            result = self.agents.insert_one(agent_dict)
            return {
                "status": "success",
                "message": "Agent registered successfully",
                "agent_id": agent_dict["agent_id"],
                "id": str(result.inserted_id)
            }
        except Exception as e:
            if "duplicate key" in str(e):
                raise ValueError("Agent ID already exists")
            raise ValueError(str(e))
    
    def list_agents(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        List all registered agents.
        
        Args:
            status: Optional status filter
        
        Returns:
            Dictionary containing list of agents and count
        """
        query = {}
        if status:
            query["status"] = status
        
        agent_list = list(self.agents.find(query, {"_id": 0}))
        
        return {
            "agents": agent_list,
            "count": len(agent_list)
        }
    
    def search_agents(
        self,
        capabilities: Optional[str] = None,
        domain: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for agents by capabilities, domain, or query string.
        
        Args:
            capabilities: Filter by capabilities
            domain: Filter by domain
            query: Search term for agent_id or agent_url
        
        Returns:
            Dictionary containing matching agents and count
        """
        search_query = {}
        
        if query:
            search_query["$or"] = [
                {"agent_id": {"$regex": query, "$options": "i"}},
                {"agent_url": {"$regex": query, "$options": "i"}}
            ]
        
        results = list(self.agents.find(search_query, {"_id": 0}))
        
        return {
            "agents": results,
            "count": len(results),
            "query": {
                "capabilities": capabilities,
                "domain": domain,
                "search_term": query
            },
            "note": "For detailed agent capabilities, check the agentFactsURL in each result"
        }
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get details for a specific agent by agent_id.
        
        Args:
            agent_id: The unique identifier of the agent
        
        Returns:
            Agent details dictionary
            
        Raises:
            ValueError: If agent not found
        """
        agent = self.agents.find_one({"agent_id": agent_id}, {"_id": 0})
        
        if not agent:
            raise ValueError("Agent not found")
        
        return agent
    
    def update_agent(
        self,
        agent_id: str,
        agent_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update agent information.
        
        Args:
            agent_id: The unique identifier of the agent to update
            agent_url: New agent URL (optional)
        
        Returns:
            Dictionary with update status
            
        Raises:
            ValueError: If agent not found
        """
        agent_update = {
            "updated_at": datetime.utcnow()
        }
        
        if agent_url:
            agent_update["agent_url"] = agent_url
        
        result = self.agents.update_one({"agent_id": agent_id}, {"$set": agent_update})
        
        if result.matched_count == 0:
            raise ValueError("Agent not found")
        
        return {
            "status": "success",
            "message": "Agent updated (for capabilities, update via external AgentFacts API)",
            "agent_updated": result.modified_count > 0,
            "note": "AgentFacts are managed externally at list39.org"
        }
    
    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete an agent from the registry.
        
        Args:
            agent_id: The unique identifier of the agent to delete
        
        Returns:
            Dictionary with deletion status
            
        Raises:
            ValueError: If agent not found
        """
        result = self.agents.delete_one({"agent_id": agent_id})
        
        if result.deleted_count == 0:
            raise ValueError("Agent not found")
        
        return {
            "status": "success",
            "message": "Agent deleted from registry",
            "agent_deleted": result.deleted_count > 0,
            "note": "AgentFacts at list39.org may still exist - manage separately if needed"
        }
    
    def get_agent_facts(self, username: str) -> Dict[str, Any]:
        """
        Get agent facts by username from the facts database.
        
        Args:
            username: The username/agent_name to lookup
        
        Returns:
            Agent facts dictionary
            
        Raises:
            ValueError: If agent facts not found
        """
        fact = self.agent_facts.find_one({"agent_name": username}, {"_id": 0})
        
        if not fact:
            raise ValueError("Agent facts not found")
        
        return fact
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the registry server and database connections.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Test MongoDB connections
            self.index_client.admin.command('ping')
            self.facts_client.admin.command('ping')
            return {
                "status": "healthy",
                "mongodb_index": "connected",
                "mongodb_facts": "connected"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
