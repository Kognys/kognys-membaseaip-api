"""AIP Router Service for intelligent request routing."""

import logging
import sys
import os
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

# Add aip-agent to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../aip-agent/src'))

from aip_agent.workflows.router.router_llm import LLMRouter, LLMRouterResult
from aip_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from aip_agent.agents.agent import Agent
from aip_agent.context import Context

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
    """Service for intelligent request routing using AIP router."""
    
    def __init__(self):
        self._router: Optional[LLMRouter] = None
        self._llm: Optional[OpenAIAugmentedLLM] = None
        self._initialized = False
        self._agents: List[Agent] = []
        self._functions: List[Callable] = []
        self._context: Optional[Context] = None
        
    async def initialize_router(self):
        """Initialize the LLM-based router."""
        if self._initialized:
            return
            
        try:
            # Initialize LLM
            if not settings.openai_api_key:
                raise RouterInitializationError("OpenAI API key not configured")
                
            self._llm = OpenAIAugmentedLLM(api_key=settings.openai_api_key)
            
            # Create context (minimal context for routing)
            self._context = Context()
            
            # Initialize router with empty lists (will be populated later)
            self._router = await LLMRouter.create(
                llm=self._llm,
                server_names=[],  # No MCP servers for now
                agents=self._agents,
                functions=self._functions,
                context=self._context
            )
            
            self._initialized = True
            logger.info("AIP Router Service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize router: {e}")
            raise RouterInitializationError(str(e))
    
    def add_agent(self, agent: Agent):
        """Add an agent to the routing categories."""
        if agent not in self._agents:
            self._agents.append(agent)
            if self._router:
                self._router.agents = self._agents
                self._router.initialized = False  # Force re-initialization
    
    def add_function(self, func: Callable, name: str = None, description: str = None):
        """Add a function to the routing categories."""
        # Wrap function with metadata if needed
        if name:
            func.__name__ = name
        if description:
            func.__doc__ = description
            
        if func not in self._functions:
            self._functions.append(func)
            if self._router:
                self._router.functions = self._functions
                self._router.initialized = False  # Force re-initialization
    
    async def route_request(self, request: str, top_k: int = 3, 
                           routing_type: str = "all") -> List[RouteResult]:
        """Route a request to appropriate handlers."""
        if not self._initialized:
            await self.initialize_router()
            
        try:
            results: List[LLMRouterResult] = []
            
            if routing_type == "all":
                results = await self._router.route(request, top_k)
            elif routing_type == "agent":
                results = await self._router.route_to_agent(request, top_k)
            elif routing_type == "function":
                results = await self._router.route_to_function(request, top_k)
            else:
                raise ValueError(f"Invalid routing type: {routing_type}")
            
            # Convert to our RouteResult format
            route_results = []
            for result in results:
                category_type = self._determine_category_type(result.result)
                category_name = self._get_category_name(result.result)
                
                route_results.append(RouteResult(
                    category_name=category_name,
                    category_type=category_type,
                    confidence=getattr(result, 'confidence', None),
                    reasoning=getattr(result, 'reasoning', None),
                    score=result.p_score
                ))
            
            return route_results
            
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
                "name": agent.name,
                "type": "agent",
                "description": agent.instruction if isinstance(agent.instruction, str) else "Agent",
                "available": True
            })
        
        # Add function categories
        for func in self._functions:
            categories.append({
                "name": func.__name__,
                "type": "function",
                "description": func.__doc__ or "Function",
                "available": True
            })
        
        return categories
    
    async def route_to_agent(self, request: str, top_k: int = 3) -> List[RouteResult]:
        """Route specifically to agents."""
        return await self.route_request(request, top_k, routing_type="agent")
    
    async def route_to_function(self, request: str, top_k: int = 3) -> List[RouteResult]:
        """Route specifically to functions."""
        return await self.route_request(request, top_k, routing_type="function")
    
    def _determine_category_type(self, result: Any) -> str:
        """Determine the category type from router result."""
        if isinstance(result, Agent):
            return "agent"
        elif isinstance(result, str):
            return "server"
        elif callable(result):
            return "function"
        else:
            return "unknown"
    
    def _get_category_name(self, result: Any) -> str:
        """Get the category name from router result."""
        if isinstance(result, Agent):
            return result.name
        elif isinstance(result, str):
            return result
        elif callable(result):
            return getattr(result, '__name__', 'function')
        else:
            return str(result)