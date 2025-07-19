from fastapi import APIRouter, HTTPException, status
from typing import Optional
from models.agents import (
    RegisterAgentRequest,
    RegisterAgentResponse,
    BuyAuthRequest,
    BuyAuthResponse,
    AgentInfoResponse,
    AuthCheckResponse
)
from core.dependencies import chain_dep, auth_dep

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)


@router.post("/register", response_model=RegisterAgentResponse)
async def register_agent(
    request: RegisterAgentRequest,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Register a new agent on the blockchain.
    
    This endpoint registers an agent with the specified ID on the Membase blockchain.
    The agent must not already be registered.
    """
    try:
        # Check if agent already exists
        existing_address = chain.get_agent(request.agent_id)
        if existing_address and existing_address != "0x0000000000000000000000000000000000000000":
            return RegisterAgentResponse(
                success=False,
                message=f"Agent {request.agent_id} is already registered",
                agent_id=request.agent_id,
                address=existing_address
            )
        
        # Register the agent
        result = chain.register(request.agent_id)
        
        if result:
            # Get the registered address
            address = chain.get_agent(request.agent_id)
            return RegisterAgentResponse(
                success=True,
                message=f"Agent {request.agent_id} registered successfully",
                agent_id=request.agent_id,
                address=address
            )
        else:
            return RegisterAgentResponse(
                success=False,
                message=f"Failed to register agent {request.agent_id}",
                agent_id=request.agent_id
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering agent: {str(e)}"
        )


@router.get("/{agent_id}", response_model=AgentInfoResponse)
async def get_agent_info(
    agent_id: str,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Get information about a specific agent.
    
    Returns the agent's blockchain address and registration status.
    """
    try:
        address = chain.get_agent(agent_id)
        is_registered = address and address != "0x0000000000000000000000000000000000000000"
        
        return AgentInfoResponse(
            agent_id=agent_id,
            address=address if is_registered else None,
            is_registered=is_registered
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting agent info: {str(e)}"
        )


@router.post("/buy-auth", response_model=BuyAuthResponse)
async def buy_authorization(
    request: BuyAuthRequest,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Buy authorization from one agent to another.
    
    This allows the buyer agent to access the seller agent's memories and data.
    Both agents must be registered on the blockchain.
    """
    try:
        # Verify both agents are registered
        buyer_address = chain.get_agent(request.buyer_id)
        seller_address = chain.get_agent(request.seller_id)
        
        if not buyer_address or buyer_address == "0x0000000000000000000000000000000000000000":
            return BuyAuthResponse(
                success=False,
                message=f"Buyer agent {request.buyer_id} is not registered"
            )
            
        if not seller_address or seller_address == "0x0000000000000000000000000000000000000000":
            return BuyAuthResponse(
                success=False,
                message=f"Seller agent {request.seller_id} is not registered"
            )
        
        # Check if authorization already exists
        if chain.has_auth(request.buyer_id, request.seller_id):
            return BuyAuthResponse(
                success=True,
                message=f"Agent {request.buyer_id} already has authorization from {request.seller_id}"
            )
        
        # Buy authorization
        result = chain.buy(request.buyer_id, request.seller_id)
        
        if result:
            return BuyAuthResponse(
                success=True,
                message=f"Authorization purchased successfully",
                transaction_hash=None  # Could be enhanced to return actual tx hash
            )
        else:
            return BuyAuthResponse(
                success=False,
                message=f"Failed to purchase authorization"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error buying authorization: {str(e)}"
        )


@router.get("/{agent_id}/has-auth/{target_id}", response_model=AuthCheckResponse)
async def check_authorization(
    agent_id: str,
    target_id: str,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Check if an agent has authorization to access another agent's data.
    
    Returns whether agent_id has purchased authorization from target_id.
    """
    try:
        has_auth = chain.has_auth(agent_id, target_id)
        
        return AuthCheckResponse(
            agent_id=agent_id,
            target_id=target_id,
            has_auth=has_auth,
            message=f"Agent {agent_id} {'has' if has_auth else 'does not have'} authorization from {target_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking authorization: {str(e)}"
        )