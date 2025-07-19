"""Pydantic models for routing endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class RouteRequest(BaseModel):
    request: str = Field(..., description="The request to route")
    top_k: int = Field(3, description="Maximum number of routing results", ge=1, le=10)
    routing_type: Optional[Literal["all", "agent", "function"]] = Field(
        "all", 
        description="Type of routing: all, agent-only, or function-only"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "request": "Calculate the tax on $5000 income",
                "top_k": 2,
                "routing_type": "all"
            }
        }


class RouteResult(BaseModel):
    category_name: str = Field(..., description="Name of the category/handler")
    category_type: Literal["agent", "function", "server"] = Field(
        ..., 
        description="Type of the category"
    )
    confidence: Optional[Literal["high", "medium", "low"]] = Field(
        None, 
        description="Confidence level of the routing decision"
    )
    reasoning: Optional[str] = Field(
        None, 
        description="Explanation of the routing decision"
    )
    score: Optional[float] = Field(
        None, 
        description="Numeric score (0-1) of the routing match",
        ge=0, 
        le=1
    )


class RouteResponse(BaseModel):
    routes: List[RouteResult] = Field(
        ..., 
        description="List of routing results, ordered by relevance"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "routes": [
                    {
                        "category_name": "TaxCalculatorAgent",
                        "category_type": "agent",
                        "confidence": "high",
                        "reasoning": "Request involves tax calculation",
                        "score": 0.95
                    },
                    {
                        "category_name": "calculate_tax",
                        "category_type": "function",
                        "confidence": "medium",
                        "reasoning": "Generic calculation function",
                        "score": 0.72
                    }
                ]
            }
        }


class RouteCategoryInfo(BaseModel):
    name: str = Field(..., description="Category name")
    type: str = Field(..., description="Category type")
    description: str = Field(..., description="Category description")
    available: bool = Field(..., description="Whether the category is available")