from fastapi import APIRouter, HTTPException, status
from models.tasks import (
    CreateTaskRequest,
    CreateTaskResponse,
    JoinTaskRequest,
    JoinTaskResponse,
    FinishTaskRequest,
    FinishTaskResponse,
    TaskInfoResponse
)
from core.dependencies import chain_dep, auth_dep

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)


@router.post("/create", response_model=CreateTaskResponse)
async def create_task(
    request: CreateTaskRequest,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Create a new task on the blockchain.
    
    Creates a task with the specified ID and price/reward. The task can then be
    joined by agents and completed for the reward.
    """
    try:
        # Check if task already exists
        try:
            task_info = chain.getTask(request.task_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to blockchain: {str(e)}"
            )
        
        if task_info and task_info[1] != "0x0000000000000000000000000000000000000000":  # task_info[1] is owner
            # If already owned by current wallet, treat as conflict
            try:
                current_wallet = chain.wallet_address.lower()
                owner_wallet = task_info[1].lower()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Chain configuration error: {str(e)}"
                )
                
            if owner_wallet == current_wallet:
                if task_info[0]:  # Already finished
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Task {request.task_id} already exists and is finished (owned by current wallet)"
                    )
                else:  # Already exists but not finished
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Task {request.task_id} already exists (owned by current wallet)"
                    )
            else:
                # Owned by different wallet
                if task_info[0]:  # Already finished
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Task {request.task_id} already exists and is finished (owned by {task_info[1]})"
                    )
                else:  # Already exists but not finished
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Task {request.task_id} already exists (owned by {task_info[1]})"
                    )
        
        # Create the task (waits for blockchain confirmation)
        try:
            tx_hash = chain.createTask(request.task_id, request.price)
        except Exception as e:
            # Check if this is a known blockchain error
            error_msg = str(e).lower()
            if "already register" in error_msg or "already exists" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Task {request.task_id} already exists: {str(e)}"
                )
            elif "connection" in error_msg or "timeout" in error_msg or "rpc" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Blockchain connection error: {str(e)}"
                )
            elif "insufficient" in error_msg or "gas" in error_msg or "balance" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Blockchain transaction error: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Blockchain error: {str(e)}"
                )
        
        # Chain method returns None if already owned by same wallet, or tx_hash if successful
        if tx_hash is None:
            # This should not happen due to our check above, but just in case
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected: Task {request.task_id} already owned by current wallet"
            )
        
        if not tx_hash:
            # Transaction was sent but failed on blockchain  
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction failed on blockchain for task {request.task_id}"
            )
        
        # Success - transaction confirmed on blockchain
        return CreateTaskResponse(
            success=True,
            message=f"Task {request.task_id} created and confirmed on blockchain with price {request.price}",
            task_id=request.task_id,
            transaction_hash=tx_hash
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions as they already have proper status codes
        raise
    except Exception as e:
        # Catch any remaining unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error creating task: {str(e)}"
        )


@router.post("/{task_id}/join", response_model=JoinTaskResponse)
async def join_task(
    task_id: str,
    request: JoinTaskRequest,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Join an existing task.
    
    Allows an agent to join a task to compete for the reward.
    The agent must be registered on the blockchain.
    """
    try:
        # Verify agent is registered
        try:
            agent_address = chain.get_agent(request.agent_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to blockchain: {str(e)}"
            )
            
        if not agent_address or agent_address == "0x0000000000000000000000000000000000000000":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent {request.agent_id} is not registered"
            )
        
        # Check if task exists and is not finished
        try:
            task_info = chain.getTask(task_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to blockchain: {str(e)}"
            )
            
        if not task_info or task_info[1] == "0x0000000000000000000000000000000000000000":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} does not exist"
            )
            
        if task_info[0]:  # Task is finished
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task {task_id} is already finished"
            )
            
        # Check if agent is trying to join their own task (use already retrieved agent_address)
        task_owner = task_info[1]  # task_info[1] is the owner address
        
        if agent_address and agent_address.lower() == task_owner.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent {request.agent_id} cannot join their own task {task_id}"
            )
        
        # Check if agent has already joined this task
        try:
            already_joined = chain.membase.functions.getPermission(task_id, request.agent_id).call()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to blockchain: {str(e)}"
            )
            
        if already_joined:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent {request.agent_id} has already joined task {task_id}"
            )
        
        # Join the task (waits for blockchain confirmation)
        try:
            tx_hash = chain.joinTask(task_id, request.agent_id)
        except Exception as e:
            # Check if this is a known blockchain error
            error_msg = str(e).lower()
            if "already finish" in error_msg or "already join" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot join task {task_id}: {str(e)}"
                )
            elif "connection" in error_msg or "timeout" in error_msg or "rpc" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Blockchain connection error: {str(e)}"
                )
            elif "insufficient" in error_msg or "gas" in error_msg or "balance" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Blockchain transaction error: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Blockchain error: {str(e)}"
                )
        
        # Chain method returns None if already has permission, or tx_hash if successful
        if tx_hash is None:
            # This should not happen due to our check above, but just in case
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected: Agent {request.agent_id} already has permission for task {task_id}"
            )
        
        if not tx_hash:
            # Transaction was sent but failed on blockchain
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction failed on blockchain for joining task {task_id}"
            )
        
        # Success - transaction confirmed on blockchain
        return JoinTaskResponse(
            success=True,
            message=f"Agent {request.agent_id} joined task {task_id} and confirmed on blockchain",
            task_id=task_id,
            agent_id=request.agent_id,
            transaction_hash=tx_hash
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions as they already have proper status codes
        raise
    except Exception as e:
        # Catch any remaining unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error joining task: {str(e)}"
        )


@router.post("/{task_id}/finish", response_model=FinishTaskResponse)
async def finish_task(
    task_id: str,
    request: FinishTaskRequest,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Mark a task as finished by a specific agent.
    
    The agent claims to have completed the task and will receive the reward
    if they are selected as the winner.
    """
    try:
        # Verify agent is registered
        try:
            agent_address = chain.get_agent(request.agent_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to blockchain: {str(e)}"
            )
            
        if not agent_address or agent_address == "0x0000000000000000000000000000000000000000":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent {request.agent_id} is not registered"
            )
        
        # Check if task exists and is not already finished
        try:
            task_info = chain.getTask(task_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to blockchain: {str(e)}"
            )
            
        if not task_info or task_info[1] == "0x0000000000000000000000000000000000000000":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} does not exist"
            )
            
        if task_info[0]:  # Task is already finished
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task {task_id} is already finished by {task_info[4]}"
            )
        
        # Finish the task (waits for blockchain confirmation)
        try:
            tx_hash = chain.finishTask(task_id, request.agent_id)
        except Exception as e:
            # Check if this is a known blockchain error
            error_msg = str(e).lower()
            if "already finish" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Task {task_id} is already finished: {str(e)}"
                )
            elif "connection" in error_msg or "timeout" in error_msg or "rpc" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Blockchain connection error: {str(e)}"
                )
            elif "insufficient" in error_msg or "gas" in error_msg or "balance" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Blockchain transaction error: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Blockchain error: {str(e)}"
                )
        
        # Chain method should always return tx_hash or raise exception for finishTask
        if tx_hash is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected: finishTask returned None for task {task_id}"
            )
        
        if not tx_hash:
            # Transaction was sent but failed on blockchain
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction failed on blockchain for finishing task {task_id}"
            )
        
        # Success - transaction confirmed on blockchain
        return FinishTaskResponse(
            success=True,
            message=f"Task {task_id} finished and confirmed on blockchain by agent {request.agent_id}",
            task_id=task_id,
            agent_id=request.agent_id,
            transaction_hash=tx_hash
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions as they already have proper status codes
        raise
    except Exception as e:
        # Catch any remaining unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error finishing task: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskInfoResponse)
async def get_task_info(
    task_id: str,
    chain=chain_dep,
    _auth=auth_dep
):
    """
    Get information about a specific task.
    
    Returns the task's status, owner, price, value, and winner (if finished).
    """
    try:
        try:
            task_info = chain.getTask(task_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to blockchain: {str(e)}"
            )
        
        if not task_info:
            return TaskInfoResponse(
                task_id=task_id,
                is_finished=False,
                message=f"Task {task_id} does not exist"
            )
        
        # Unpack task info: (finished, owner, price, value, winner)
        finished, owner, price, value, winner = task_info
        
        return TaskInfoResponse(
            task_id=task_id,
            is_finished=finished,
            owner=owner,
            price=price,
            value=value,
            winner=winner if finished else None,
            message=f"Task {task_id} is {'finished' if finished else 'active'}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting task info: {str(e)}"
        )