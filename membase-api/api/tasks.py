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
        task_info = chain.getTask(request.task_id)
        if task_info and task_info[0]:  # task_info[0] is the 'finished' flag
            return CreateTaskResponse(
                success=False,
                message=f"Task {request.task_id} already exists",
                task_id=request.task_id
            )
        
        # Create the task (waits for blockchain confirmation)
        try:
            tx_hash = chain.createTask(request.task_id, request.price)
            
            if tx_hash:
                return CreateTaskResponse(
                    success=True,
                    message=f"Task {request.task_id} created and confirmed on blockchain with price {request.price}",
                    task_id=request.task_id,
                    transaction_hash=tx_hash
                )
            else:
                # Transaction was sent but failed on blockchain
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transaction failed on blockchain for task {request.task_id}"
                )
        except Exception as chain_error:
            # Chain operation failed (before or during transaction)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create task {request.task_id}: {str(chain_error)}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating task: {str(e)}"
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
        agent_address = chain.get_agent(request.agent_id)
        if not agent_address or agent_address == "0x0000000000000000000000000000000000000000":
            return JoinTaskResponse(
                success=False,
                message=f"Agent {request.agent_id} is not registered",
                task_id=task_id,
                agent_id=request.agent_id
            )
        
        # Check if task exists and is not finished
        task_info = chain.getTask(task_id)
        if not task_info:
            return JoinTaskResponse(
                success=False,
                message=f"Task {task_id} does not exist",
                task_id=task_id,
                agent_id=request.agent_id
            )
            
        if task_info[0]:  # Task is finished
            return JoinTaskResponse(
                success=False,
                message=f"Task {task_id} is already finished",
                task_id=task_id,
                agent_id=request.agent_id
            )
        
        # Join the task (waits for blockchain confirmation)
        try:
            tx_hash = chain.joinTask(task_id, request.agent_id)
            
            if tx_hash:
                return JoinTaskResponse(
                    success=True,
                    message=f"Agent {request.agent_id} joined task {task_id} and confirmed on blockchain",
                    task_id=task_id,
                    agent_id=request.agent_id,
                    transaction_hash=tx_hash
                )
            else:
                # Transaction was sent but failed on blockchain
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transaction failed on blockchain for joining task {task_id}"
                )
        except Exception as chain_error:
            # Chain operation failed (before or during transaction)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to join task {task_id}: {str(chain_error)}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining task: {str(e)}"
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
        agent_address = chain.get_agent(request.agent_id)
        if not agent_address or agent_address == "0x0000000000000000000000000000000000000000":
            return FinishTaskResponse(
                success=False,
                message=f"Agent {request.agent_id} is not registered",
                task_id=task_id,
                agent_id=request.agent_id
            )
        
        # Check if task exists and is not already finished
        task_info = chain.getTask(task_id)
        if not task_info:
            return FinishTaskResponse(
                success=False,
                message=f"Task {task_id} does not exist",
                task_id=task_id,
                agent_id=request.agent_id
            )
            
        if task_info[0]:  # Task is already finished
            return FinishTaskResponse(
                success=False,
                message=f"Task {task_id} is already finished by {task_info[4]}",
                task_id=task_id,
                agent_id=request.agent_id
            )
        
        # Finish the task (waits for blockchain confirmation)
        try:
            tx_hash = chain.finishTask(task_id, request.agent_id)
            
            if tx_hash:
                return FinishTaskResponse(
                    success=True,
                    message=f"Task {task_id} finished and confirmed on blockchain by agent {request.agent_id}",
                    task_id=task_id,
                    agent_id=request.agent_id,
                    transaction_hash=tx_hash
                )
            else:
                # Transaction was sent but failed on blockchain
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transaction failed on blockchain for finishing task {task_id}"
                )
        except Exception as chain_error:
            # Chain operation failed (before or during transaction)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to finish task {task_id}: {str(chain_error)}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finishing task: {str(e)}"
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
        task_info = chain.getTask(task_id)
        
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