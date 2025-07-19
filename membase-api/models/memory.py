from pydantic import BaseModel, Field
from typing import Optional, List, Union, Dict, Any, Literal
from datetime import datetime


class MessageCreate(BaseModel):
    name: str = Field(..., description="Sender identifier")
    content: str = Field(..., description="Message content")
    role: Literal["system", "user", "assistant"] = Field(..., description="Message role")
    url: Optional[Union[str, List[str]]] = Field(None, description="Optional URL(s) for multimodal content")
    metadata: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Optional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "user",
                "content": "Hello, how are you?",
                "role": "user",
                "metadata": {"source": "web"}
            }
        }


class MessageResponse(BaseModel):
    id: str
    name: str
    content: str
    role: str
    url: Optional[Union[str, List[str]]] = None
    metadata: Optional[Union[str, Dict[str, Any]]] = None
    timestamp: datetime


class ConversationCreate(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Custom conversation ID (auto-generated if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "chat-2024-01-15"
            }
        }


class ConversationResponse(BaseModel):
    conversation_id: str
    message_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total_count: int


class AddMessageRequest(BaseModel):
    messages: Union[MessageCreate, List[MessageCreate]] = Field(..., description="Message or list of messages to add")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": {
                    "name": "user",
                    "content": "Tell me about AI",
                    "role": "user"
                }
            }
        }


class GetMessagesRequest(BaseModel):
    recent_n: Optional[int] = Field(None, description="Get only the N most recent messages", ge=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "recent_n": 10
            }
        }


class MessagesResponse(BaseModel):
    conversation_id: str
    messages: List[MessageResponse]
    total_count: int


class DeleteMessageResponse(BaseModel):
    success: bool
    message: str
    deleted_index: int


class ClearConversationResponse(BaseModel):
    success: bool
    message: str
    conversation_id: str


class ExportRequest(BaseModel):
    file_path: Optional[str] = Field(None, description="File path for export (optional)")


class ExportResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class ImportRequest(BaseModel):
    file_path: Optional[str] = Field(None, description="File path to import from")
    content: Optional[Dict[str, Any]] = Field(None, description="Content to import directly")
    clear_previous: bool = Field(True, description="Clear existing messages before import")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/path/to/conversation.json",
                "clear_previous": True
            }
        }


class ImportResponse(BaseModel):
    success: bool
    message: str
    messages_imported: int