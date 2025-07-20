"""AIP Router Service for intelligent request routing (simplified)."""

import logging
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from core.config import settings
from .exceptions import RouterInitializationError

logger = logging.getLogger(__name__)


class RouteResult:
    """Result of a routing operation."""
    def __init__(self, category_name: str, category_type: str, 
                 confidence: Optional[str] = None, reasoning: Optional[str] = None,
                 score: Optional[float] = None):
        self.category_name = category_name
        self.category_type = category_type
        self.confidence = confidence
        self.reasoning = reasoning
        self.score = score


class AIPRouterService:
    """Service for intelligent request routing (simplified)."""
    
    def __init__(self):
        self._initialized = False
        self._agents: List[Dict[str, str]] = []
        self._functions: List[Dict[str, Any]] = []
        
    async def initialize_router(self):
        """Initialize the simplified router."""
        if self._initialized:
            return
            
        try:
            self._initialized = True
            logger.info("AIP Router Service initialized (simplified mode)")
            
        except Exception as e:
            logger.error(f"Failed to initialize router: {e}")
            raise RouterInitializationError(str(e))
    
    def add_agent(self, agent_name: str, description: str = "Agent"):
        """Add an agent to the routing categories."""
        agent_info = {"name": agent_name, "description": description}
        if agent_info not in self._agents:
            self._agents.append(agent_info)
    
    def add_function(self, func_name: str, description: str = "Function"):
        """Add a function to the routing categories."""
        func_info = {"name": func_name, "description": description}
        if func_info not in self._functions:
            self._functions.append(func_info)
    
    async def route_request(self, request: str, top_k: int = 3, 
                           routing_type: str = "all") -> List[RouteResult]:
        """Route a request to appropriate handlers (simplified)."""
        if not self._initialized:
            await self.initialize_router()
            
        try:
            route_results = []
            
            # Simple routing - return first available categories
            if routing_type in ["all", "agent"] and self._agents:
                for i, agent in enumerate(self._agents[:top_k]):
                    route_results.append(RouteResult(
                        category_name=agent["name"],
                        category_type="agent",
                        confidence="medium",
                        reasoning=f"Routed to agent based on request: {request[:50]}...",
                        score=1.0 - (i * 0.1)  # Decreasing scores
                    ))
            
            if routing_type in ["all", "function"] and self._functions:
                for i, func in enumerate(self._functions[:top_k]):
                    route_results.append(RouteResult(
                        category_name=func["name"],
                        category_type="function",
                        confidence="medium",
                        reasoning=f"Routed to function based on request: {request[:50]}...",
                        score=1.0 - (i * 0.1)  # Decreasing scores
                    ))
            
            return route_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error routing request: {e}")
            raise
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get available routing categories."""
        if not self._initialized:
            await self.initialize_router()
            
        categories = []
        
        # Add agent categories
        for agent in self._agents:
            categories.append({
                "name": agent["name"],
                "type": "agent",
                "description": agent["description"],
                "available": True
            })
        
        # Add function categories
        for func in self._functions:
            categories.append({
                "name": func["name"],
                "type": "function",
                "description": func["description"],
                "available": True
            })
        
        return categories
    
    async def route_to_agent(self, request: str, top_k: int = 3) -> List[RouteResult]:
        """Route specifically to agents."""
        return await self.route_request(request, top_k, routing_type="agent")
    
    async def route_to_function(self, request: str, top_k: int = 3) -> List[RouteResult]:
        """Route specifically to functions."""
        return await self.route_request(request, top_k, routing_type="function")