"""Routing API endpoints for intelligent request routing."""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models.route import (
    RouteRequest,
    RouteResponse,
    RouteResult,
    RouteCategoryInfo
)
from core.dependencies import auth_dep
from core.config import settings

router = APIRouter(
    prefix="/route",
    tags=["routing"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)

if settings.enable_aip:
    from core.aip import AIPRouterService
    from core.aip.exceptions import RouterInitializationError
    
    # Create router service instance
    _router_service = None
    
    async def get_router_service():
        global _router_service
        if _router_service is None:
            _router_service = AIPRouterService()
            await _router_service.initialize_router()
        return _router_service
    
    @router.post("", response_model=RouteResponse)
    async def route_request(
        request: RouteRequest,
        router_service: AIPRouterService = Depends(get_router_service),
        _auth=auth_dep
    ):
        """
        Intelligently route a request to the most appropriate handler.
        
        This endpoint uses an LLM-based router to analyze the request and
        determine which agents, functions, or servers are best suited to handle it.
        """
        try:
            results = await router_service.route_request(
                request=request.request,
                top_k=request.top_k,
                routing_type=request.routing_type
            )
            
            route_results = [
                RouteResult(
                    category_name=result.category_name,
                    category_type=result.category_type,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    score=result.score
                )
                for result in results
            ]
            
            return RouteResponse(routes=route_results)
            
        except RouterInitializationError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Router service not available: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error routing request: {str(e)}"
            )
    
    @router.get("/categories", response_model=List[RouteCategoryInfo])
    async def get_routing_categories(
        router_service: AIPRouterService = Depends(get_router_service),
        _auth=auth_dep
    ):
        """
        Get all available routing categories.
        
        Returns a list of all agents, functions, and servers that can be
        routed to by the intelligent router.
        """
        try:
            categories = await router_service.get_categories()
            
            return [
                RouteCategoryInfo(
                    name=cat["name"],
                    type=cat["type"],
                    description=cat["description"],
                    available=cat["available"]
                )
                for cat in categories
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting categories: {str(e)}"
            )
    
    @router.post("/agent", response_model=RouteResponse)
    async def route_to_agent(
        request: RouteRequest,
        router_service: AIPRouterService = Depends(get_router_service),
        _auth=auth_dep
    ):
        """
        Route a request specifically to agents.
        
        This endpoint only considers agent categories when routing,
        useful when you know the request should be handled by an agent.
        """
        try:
            results = await router_service.route_to_agent(
                request=request.request,
                top_k=request.top_k
            )
            
            route_results = [
                RouteResult(
                    category_name=result.category_name,
                    category_type="agent",
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    score=result.score
                )
                for result in results
            ]
            
            return RouteResponse(routes=route_results)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error routing to agent: {str(e)}"
            )
    
    @router.post("/function", response_model=RouteResponse)
    async def route_to_function(
        request: RouteRequest,
        router_service: AIPRouterService = Depends(get_router_service),
        _auth=auth_dep
    ):
        """
        Route a request specifically to functions.
        
        This endpoint only considers function categories when routing,
        useful when you know the request should be handled by a function.
        """
        try:
            results = await router_service.route_to_function(
                request=request.request,
                top_k=request.top_k
            )
            
            route_results = [
                RouteResult(
                    category_name=result.category_name,
                    category_type="function",
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    score=result.score
                )
                for result in results
            ]
            
            return RouteResponse(routes=route_results)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error routing to function: {str(e)}"
            )
else:
    @router.get("/", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def routing_disabled():
        """Routing endpoints are disabled when AIP is not enabled."""
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIP routing is disabled. Set ENABLE_AIP=true to enable."
        )