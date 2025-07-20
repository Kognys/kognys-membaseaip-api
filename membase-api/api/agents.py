from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, List
from models.agents import (
    RegisterAgentRequest,
    RegisterAgentResponse,
    BuyAuthRequest,
    BuyAuthResponse,
    AgentInfoResponse,
    AuthCheckResponse,
    # AIP models
    CreateAgentRequest,
    QueryRequest,
    QueryResponse,
    MessageRequest,
    MessageResponse,
    UpdatePromptRequest,
    ActiveAgentInfo
)
from core.dependencies import chain_dep, auth_dep
from core.config import settings

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
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent {request.agent_id} is already registered with address {existing_address}"
            )
        
        # Register the agent (waits for blockchain confirmation)
        tx_hash = chain.register(request.agent_id)
        
        # Chain method returns None if already registered to same wallet, or tx_hash if successful
        if tx_hash is None:
            # This should not happen due to our check above, but just in case
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected: Agent {request.agent_id} already registered to current wallet"
            )
        
        if not tx_hash:
            # Transaction was sent but failed on blockchain
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction failed on blockchain for registering agent {request.agent_id}"
            )
        
        # Success - transaction confirmed on blockchain
        # Get the registered address
        address = chain.get_agent(request.agent_id)
        return RegisterAgentResponse(
            success=True,
            message=f"Agent {request.agent_id} registered and confirmed on blockchain",
            agent_id=request.agent_id,
            address=address,
            transaction_hash=tx_hash
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Buyer agent {request.buyer_id} is not registered"
            )
            
        if not seller_address or seller_address == "0x0000000000000000000000000000000000000000":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seller agent {request.seller_id} is not registered"
            )
        
        # Check if authorization already exists
        if chain.has_auth(request.buyer_id, request.seller_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent {request.buyer_id} already has authorization from {request.seller_id}"
            )
        
        # Buy authorization (waits for blockchain confirmation)
        tx_hash = chain.buy(request.buyer_id, request.seller_id)
        
        # Chain method returns None if permission already exists, or tx_hash if successful
        if tx_hash is None:
            # This should not happen due to our check above, but just in case
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected: Authorization already exists between {request.buyer_id} and {request.seller_id}"
            )
        
        if not tx_hash:
            # Transaction was sent but failed on blockchain
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction failed on blockchain for purchasing authorization"
            )
        
        # Success - transaction confirmed on blockchain
        return BuyAuthResponse(
            success=True,
            message=f"Authorization purchased and confirmed on blockchain",
            transaction_hash=tx_hash
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


# AIP Agent Communication Endpoints
if settings.enable_aip:
    # Create agent manager instance
    _agent_manager = None
    
    async def get_agent_manager():
        global _agent_manager
        if _agent_manager is None:
            try:
                from core.aip import AIPAgentManager
                _agent_manager = AIPAgentManager()
                await _agent_manager.initialize()
            except ImportError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"AIP dependencies not available: {str(e)}"
                )
        return _agent_manager
    
    @router.post("/create", response_model=ActiveAgentInfo)
    async def create_aip_agent(
        request: CreateAgentRequest,
        agent_manager = Depends(get_agent_manager),
        _auth=auth_dep
    ):
        """
        Create a new AIP agent with advanced capabilities.
        
        This creates an agent that can process queries with LLM integration,
        communicate with other agents, and maintain conversation history.
        """
        try:
            agent_info = await agent_manager.create_agent(
                agent_id=request.agent_id,
                description=request.description,
                default_conversation_id=request.default_conversation_id
            )
            
            return ActiveAgentInfo(
                agent_id=agent_info.agent_id,
                status=agent_info.status,
                created_at=agent_info.created_at,
                description=agent_info.description
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating AIP agent: {str(e)}"
            )
    
    @router.post("/{agent_id}/query", response_model=QueryResponse)
    async def query_agent(
        agent_id: str,
        request: QueryRequest,
        agent_manager = Depends(get_agent_manager),
        _auth=auth_dep
    ):
        """
        Process a query through an AIP agent with advanced options.
        
        The agent will use its LLM integration and available tools to process
        the query and return a response.
        """
        try:
            response = await agent_manager.process_query(
                agent_id=agent_id,
                query=request.query,
                conversation_id=request.conversation_id,
                use_history=request.use_history,
                system_prompt=request.system_prompt,
                recent_n_messages=request.recent_n_messages,
                use_tool_call=request.use_tool_call
            )
            
            return QueryResponse(
                response=response,
                conversation_id=request.conversation_id or "default",
                agent_id=agent_id
            )
            
        except Exception as e:
            if "AgentNotFoundError" in str(type(e)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
            elif "AgentTimeoutError" in str(type(e)):
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=str(e)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing query: {str(e)}"
                )
    
    @router.post("/{agent_id}/message", response_model=MessageResponse)
    async def send_message_to_agent(
        agent_id: str,
        request: MessageRequest,
        agent_manager = Depends(get_agent_manager),
        _auth=auth_dep
    ):
        """
        Send a message from one agent to another.
        
        This enables inter-agent communication for collaborative workflows.
        """
        try:
            response = await agent_manager.send_message(
                source_id=agent_id,
                target_id=request.target_agent_id,
                action=request.action,
                message=request.message
            )
            
            return MessageResponse(
                response=response,
                source_agent=agent_id,
                target_agent=request.target_agent_id
            )
            
        except Exception as e:
            if "AgentNotFoundError" in str(type(e)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            elif "AgentTimeoutError" in str(type(e)):
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=str(e)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error sending message: {str(e)}"
                )
    
    @router.put("/{agent_id}/prompt")
    async def update_agent_prompt(
        agent_id: str,
        request: UpdatePromptRequest,
        agent_manager = Depends(get_agent_manager),
        _auth=auth_dep
    ):
        """
        Update an agent's system prompt.
        
        This allows dynamic modification of agent behavior and personality.
        """
        try:
            await agent_manager.update_prompt(agent_id, request.system_prompt)
            
            return {
                "success": True,
                "message": f"System prompt updated for agent {agent_id}"
            }
            
        except Exception as e:
            if "AgentNotFoundError" in str(type(e)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error updating prompt: {str(e)}"
                )
    
    @router.get("/active", response_model=List[ActiveAgentInfo])
    async def list_active_agents(
        agent_manager = Depends(get_agent_manager),
        _auth=auth_dep
    ):
        """
        List all active AIP agents.
        
        Returns information about all currently running AIP agents.
        """
        try:
            agents = await agent_manager.list_active_agents()
            
            return [
                ActiveAgentInfo(
                    agent_id=agent["agent_id"],
                    status=agent["status"],
                    created_at=agent["created_at"],
                    description=agent["description"]
                )
                for agent in agents
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing active agents: {str(e)}"
            )
    
    @router.delete("/{agent_id}/stop")
    async def stop_agent(
        agent_id: str,
        agent_manager = Depends(get_agent_manager),
        _auth=auth_dep
    ):
        """
        Stop an active AIP agent.
        
        This will gracefully shutdown the agent and clean up resources.
        """
        try:
            success = await agent_manager.stop_agent(agent_id)
            
            return {
                "success": success,
                "message": f"Agent {agent_id} stopped successfully"
            }
            
        except Exception as e:
            if "AgentNotFoundError" in str(type(e)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error stopping agent: {str(e)}"
                )