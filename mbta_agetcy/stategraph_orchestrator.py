"""
StateGraph-based Orchestrator for MBTA Agntcy
Replaces manual orchestration with LangGraph workflow
"""
import os
from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
from dataclasses import dataclass
import asyncio
import httpx
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """
    The state that flows through the StateGraph.
    Each node can read from and write to this state.
    """
    # Input
    user_message: str
    conversation_id: str
    intent: str
    confidence: float
    
    # Agent execution tracking
    messages: Annotated[Sequence[BaseMessage], operator.add]
    agents_to_call: list[str]
    agents_called: list[str]
    
    # Results from agents
    alerts_result: dict | None
    stops_result: dict | None
    planner_result: dict | None
    
    # Final output
    final_response: str
    should_end: bool


# ============================================================================
# AGENT NODES - Each agent is a node in the graph
# ============================================================================

@dataclass
class AgentConfig:
    name: str
    url: str
    port: int


# Agent configurations
AGENTS = {
    "mbta-alerts": AgentConfig("mbta-alerts", "http://localhost", 8001),
    "mbta-stops": AgentConfig("mbta-stops", "http://localhost", 8003),
    "mbta-route-planner": AgentConfig("mbta-route-planner", "http://localhost", 8002),
}


async def call_agent_api(agent_name: str, message: str) -> dict:
    """Call an agent via A2A protocol"""
    agent = AGENTS[agent_name]
    url = f"{agent.url}:{agent.port}/a2a/message"
    
    payload = {
        "type": "request",
        "payload": {
            "message": message,
            "conversation_id": "stategraph-session"
        },
        "metadata": {
            "source": "stategraph-orchestrator",
            "agent": agent_name
        }
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


# ============================================================================
# NODE FUNCTIONS - Each function is a node in the graph
# ============================================================================

async def classify_intent_node(state: AgentState) -> AgentState:
    """
    First node: Classify user intent using LLM
    This determines which path the graph will take
    """
    with tracer.start_as_current_span("classify_intent_node") as span:
        span.set_attribute("user_message", state["user_message"])
        
        # Intent classification logic (simplified - use your existing LLM handler)
        message = state["user_message"].lower()
        
        if any(word in message for word in ["alert", "delay", "issue", "problem"]):
            intent = "alerts"
            confidence = 0.9
        elif any(word in message for word in ["how do i get", "route", "directions", "travel"]):
            intent = "trip_planning"
            confidence = 0.9
        elif any(word in message for word in ["stop", "station", "find", "near"]):
            intent = "stop_info"
            confidence = 0.85
        else:
            intent = "general"
            confidence = 0.6
        
        span.set_attribute("intent", intent)
        span.set_attribute("confidence", confidence)
        
        return {
            **state,
            "intent": intent,
            "confidence": confidence,
            "messages": [HumanMessage(content=state["user_message"])]
        }


async def alerts_agent_node(state: AgentState) -> AgentState:
    """Node: Call alerts agent"""
    with tracer.start_as_current_span("alerts_agent_node"):
        result = await call_agent_api("mbta-alerts", state["user_message"])
        
        return {
            **state,
            "alerts_result": result,
            "agents_called": state.get("agents_called", []) + ["mbta-alerts"],
            "messages": [AIMessage(content=f"Alerts: {result.get('response', 'No alerts')}", name="alerts-agent")]
        }


async def stops_agent_node(state: AgentState) -> AgentState:
    """Node: Call stops agent"""
    with tracer.start_as_current_span("stops_agent_node"):
        result = await call_agent_api("mbta-stops", state["user_message"])
        
        return {
            **state,
            "stops_result": result,
            "agents_called": state.get("agents_called", []) + ["mbta-stops"],
            "messages": [AIMessage(content=f"Stops: {result.get('response', 'No stops found')}", name="stops-agent")]
        }


async def planner_agent_node(state: AgentState) -> AgentState:
    """Node: Call route planner agent"""
    with tracer.start_as_current_span("planner_agent_node"):
        # Enhanced message with stops data if available
        message = state["user_message"]
        if state.get("stops_result"):
            # Add stops context to help planner
            message += f"\n[Context: Stop data available]"
        
        result = await call_agent_api("mbta-route-planner", message)
        
        return {
            **state,
            "planner_result": result,
            "agents_called": state.get("agents_called", []) + ["mbta-route-planner"],
            "messages": [AIMessage(content=f"Route: {result.get('response', 'No route found')}", name="planner-agent")]
        }


async def synthesize_response_node(state: AgentState) -> AgentState:
    """
    Final node: Synthesize all agent responses into final answer
    """
    with tracer.start_as_current_span("synthesize_response_node"):
        responses = []
        
        # Collect all agent responses
        if state.get("alerts_result"):
            responses.append(state["alerts_result"].get("response", ""))
        
        if state.get("stops_result"):
            responses.append(state["stops_result"].get("response", ""))
        
        if state.get("planner_result"):
            responses.append(state["planner_result"].get("response", ""))
        
        # Simple synthesis (you can enhance this with LLM)
        final_response = "\n\n".join(filter(None, responses))
        
        return {
            **state,
            "final_response": final_response,
            "should_end": True
        }


# ============================================================================
# ROUTING FUNCTIONS - Conditional edges that decide next node
# ============================================================================

def route_after_intent(state: AgentState) -> Literal["alerts", "stops", "planner", "synthesize"]:
    """
    Conditional edge after intent classification.
    Decides which agent(s) to call based on intent.
    """
    intent = state["intent"]
    
    if intent == "alerts":
        return "alerts"
    elif intent == "stop_info":
        return "stops"
    elif intent == "trip_planning":
        # Trip planning needs stops first
        return "stops"
    else:
        # General query - call all agents
        return "alerts"


def route_after_stops(state: AgentState) -> Literal["planner", "synthesize"]:
    """
    Conditional edge after stops node.
    If trip planning intent, go to planner. Otherwise synthesize.
    """
    if state["intent"] == "trip_planning":
        return "planner"
    else:
        return "synthesize"


def route_after_alerts(state: AgentState) -> Literal["stops", "synthesize"]:
    """
    Conditional edge after alerts node.
    For general queries, continue to stops. Otherwise synthesize.
    """
    if state["intent"] == "general":
        return "stops"
    else:
        return "synthesize"


def route_after_planner(state: AgentState) -> Literal["synthesize"]:
    """Always go to synthesis after planner"""
    return "synthesize"


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_mbta_graph() -> StateGraph:
    

    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("alerts", alerts_agent_node)
    workflow.add_node("stops", stops_agent_node)
    workflow.add_node("planner", planner_agent_node)
    workflow.add_node("synthesize", synthesize_response_node)
    
    # Set entry point
    workflow.set_entry_point("classify_intent")
    
    # Add conditional edges based on intent
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "alerts": "alerts",
            "stops": "stops",
            "planner": "planner",
            "synthesize": "synthesize"
        }
    )
    
    # Routing from alerts
    workflow.add_conditional_edges(
        "alerts",
        route_after_alerts,
        {
            "stops": "stops",
            "synthesize": "synthesize"
        }
    )
    
    # Routing from stops
    workflow.add_conditional_edges(
        "stops",
        route_after_stops,
        {
            "planner": "planner",
            "synthesize": "synthesize"
        }
    )
    
    # Routing from planner
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "synthesize": "synthesize"
        }
    )
    
    # End after synthesis
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()


# ============================================================================
# MAIN ORCHESTRATOR FUNCTION
# ============================================================================

class StateGraphOrchestrator:
    """Main orchestrator using LangGraph StateGraph"""
    
    def __init__(self):
        self.graph = build_mbta_graph()
    
    async def process_message(self, user_message: str, conversation_id: str) -> dict:
        """
        Process a user message through the StateGraph.
        
        Args:
            user_message: The user's query
            conversation_id: Unique conversation identifier
            
        Returns:
            dict with final response and metadata
        """
        with tracer.start_as_current_span("stategraph_orchestrator") as span:
            span.set_attribute("conversation_id", conversation_id)
            
            # Initial state
            initial_state: AgentState = {
                "user_message": user_message,
                "conversation_id": conversation_id,
                "intent": "",
                "confidence": 0.0,
                "messages": [],
                "agents_to_call": [],
                "agents_called": [],
                "alerts_result": None,
                "stops_result": None,
                "planner_result": None,
                "final_response": "",
                "should_end": False
            }
            
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract results
            span.set_attribute("intent", final_state["intent"])
            span.set_attribute("agents_called", ",".join(final_state["agents_called"]))
            
            return {
                "response": final_state["final_response"],
                "intent": final_state["intent"],
                "confidence": final_state["confidence"],
                "agents_called": final_state["agents_called"],
                "metadata": {
                    "conversation_id": conversation_id,
                    "graph_execution": "completed"
                }
            }
    
    def visualize_graph(self, output_path: str = "graph_visualization.png"):
        """
        Generate a visualization of the graph structure.
        Requires: pip install pygraphviz
        """
        try:
            from IPython.display import Image, display
            graph_image = self.graph.get_graph().draw_mermaid_png()
            
            with open(output_path, "wb") as f:
                f.write(graph_image)
            
            print(f"Graph visualization saved to {output_path}")
        except ImportError:
            print("Install pygraphviz for visualization: pip install pygraphviz")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """Test the StateGraph orchestrator"""
    orchestrator = StateGraphOrchestrator()
    
    # Test queries
    test_queries = [
        "Are there Red Line delays?",
        "Find stops near Harvard",
        "How do I get from Park Street to MIT?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        result = await orchestrator.process_message(query, f"test-{hash(query)}")
        
        print(f"\nIntent: {result['intent']} (confidence: {result['confidence']})")
        print(f"Agents Called: {', '.join(result['agents_called'])}")
        print(f"\nResponse:\n{result['response']}")


if __name__ == "__main__":
    asyncio.run(main())