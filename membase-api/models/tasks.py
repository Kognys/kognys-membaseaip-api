from pydantic import BaseModel, Field
from typing import Optional


class CreateTaskRequest(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    price: int = Field(..., description="Price/reward for completing the task", ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-123",
                "price": 100000
            }
        }


class CreateTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    transaction_hash: Optional[str] = None


class JoinTaskRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent joining the task")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "alice"
            }
        }


class JoinTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    agent_id: str
    transaction_hash: Optional[str] = None


class FinishTaskRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent who completed the task")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "alice"
            }
        }


class FinishTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    agent_id: str
    transaction_hash: Optional[str] = None


class TaskInfoResponse(BaseModel):
    task_id: str
    is_finished: bool
    owner: Optional[str] = None
    price: Optional[int] = None
    value: Optional[int] = None
    winner: Optional[str] = None
    message: str