from pydantic import BaseModel, Field
from typing import Optional


class RegisterAgentRequest(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "alice"
            }
        }


class RegisterAgentResponse(BaseModel):
    success: bool
    message: str
    agent_id: str
    address: Optional[str] = None


class BuyAuthRequest(BaseModel):
    buyer_id: str = Field(..., description="ID of the buyer agent")
    seller_id: str = Field(..., description="ID of the seller agent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "buyer_id": "alice",
                "seller_id": "bob"
            }
        }


class BuyAuthResponse(BaseModel):
    success: bool
    message: str
    transaction_hash: Optional[str] = None


class AgentInfoResponse(BaseModel):
    agent_id: str
    address: Optional[str] = None
    is_registered: bool


class AuthCheckResponse(BaseModel):
    agent_id: str
    target_id: str
    has_auth: bool
    message: str