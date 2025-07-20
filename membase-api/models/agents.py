from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


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
    transaction_hash: Optional[str] = None


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


# AIP-specific models
class QueryRequest(BaseModel):
    query: str = Field(..., description="The query to process")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    use_history: bool = Field(True, description="Whether to use conversation history")
    system_prompt: Optional[str] = Field(None, description="Override system prompt")
    recent_n_messages: int = Field(16, description="Number of recent messages to include")
    use_tool_call: bool = Field(True, description="Whether to allow tool calls")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's the weather like today?",
                "conversation_id": "session-123",
                "use_history": True,
                "use_tool_call": True
            }
        }


class QueryResponse(BaseModel):
    response: str
    conversation_id: str
    agent_id: str


class MessageRequest(BaseModel):
    target_agent_id: str = Field(..., description="ID of the target agent")
    action: str = Field("ask", description="Action type for the message")
    message: str = Field(..., description="Message content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_agent_id": "trading_agent",
                "action": "ask",
                "message": "What's the current BTC price?"
            }
        }


class MessageResponse(BaseModel):
    response: str
    source_agent: str
    target_agent: str


class UpdatePromptRequest(BaseModel):
    system_prompt: str = Field(..., description="New system prompt for the agent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_prompt": "You are a helpful financial advisor specializing in cryptocurrency."
            }
        }


class ActiveAgentInfo(BaseModel):
    agent_id: str
    status: str
    created_at: datetime
    description: str


class CreateAgentRequest(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    description: str = Field("AIP Agent", description="Agent description")
    default_conversation_id: Optional[str] = Field(None, description="Default conversation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "trading_agent",
                "description": "A specialized trading assistant",
                "default_conversation_id": "trading-session"
            }
        }