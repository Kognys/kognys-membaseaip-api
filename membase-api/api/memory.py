from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Union
from datetime import datetime
from membase.memory.message import Message
from membase.memory.multi_memory import MultiMemory
from models.memory import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    AddMessageRequest,
    GetMessagesRequest,
    MessagesResponse,
    MessageResponse
)
from core.dependencies import memory_dep, auth_dep

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)


def message_to_response(msg: Message) -> MessageResponse:
    """Convert a Message object to MessageResponse."""
    return MessageResponse(
        id=msg.id,
        name=msg.name,
        content=msg.content,
        role=msg.role,
        url=msg.url,
        metadata=msg.metadata,
        timestamp=msg.timestamp
    )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Create a new conversation.
    
    If conversation_id is not provided, a unique ID will be generated automatically.
    """
    try:
        conversation_id = request.conversation_id
        
        # If no ID provided, let MultiMemory generate one
        if not conversation_id:
            # Update the default conversation ID which creates a new one
            memory.update_conversation_id(None)
            conversation_id = memory.default_conversation_id
        else:
            # Check if conversation already exists
            existing_conversations = memory.get_all_conversations()
            if conversation_id in existing_conversations:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Conversation {conversation_id} already exists"
                )
            
            # Create the conversation by simply getting it
            # get_memory() will create a new BufferedMemory instance if it doesn't exist
            memory.get_memory(conversation_id)
        
        return ConversationResponse(
            conversation_id=conversation_id,
            message_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating conversation: {str(e)}"
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    List all conversations.
    
    Returns a list of all conversation IDs with their message counts.
    """
    try:
        conversation_ids = memory.get_all_conversations()
        conversations = []
        
        for conv_id in conversation_ids:
            messages = memory.get(conv_id)
            conversations.append(
                ConversationResponse(
                    conversation_id=conv_id,
                    message_count=len(messages) if messages else 0
                )
            )
        
        return ConversationListResponse(
            conversations=conversations,
            total_count=len(conversations)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=MessagesResponse)
async def get_conversation_messages(
    conversation_id: str,
    recent_n: Optional[int] = None,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Get messages from a specific conversation.
    
    Optionally limit to the most recent N messages.
    """
    try:
        messages = memory.get(conversation_id, recent_n=recent_n)
        
        if messages is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        message_responses = [message_to_response(msg) for msg in messages]
        
        return MessagesResponse(
            conversation_id=conversation_id,
            messages=message_responses,
            total_count=len(message_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting messages: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=MessagesResponse)
async def add_messages(
    conversation_id: str,
    request: AddMessageRequest,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Add one or more messages to a conversation.
    
    Creates the conversation if it doesn't exist.
    """
    try:
        # Convert request messages to Message objects
        messages_to_add = []
        
        if isinstance(request.messages, list):
            for msg_data in request.messages:
                msg = Message(
                    name=msg_data.name,
                    content=msg_data.content,
                    role=msg_data.role,
                    url=msg_data.url,
                    metadata=msg_data.metadata
                )
                messages_to_add.append(msg)
        else:
            msg = Message(
                name=request.messages.name,
                content=request.messages.content,
                role=request.messages.role,
                url=request.messages.url,
                metadata=request.messages.metadata
            )
            messages_to_add.append(msg)
        
        # Add messages to the conversation
        memory.add(messages_to_add, conversation_id=conversation_id)
        
        # Get all messages from the conversation
        all_messages = memory.get(conversation_id)
        message_responses = [message_to_response(msg) for msg in all_messages]
        
        return MessagesResponse(
            conversation_id=conversation_id,
            messages=message_responses,
            total_count=len(message_responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding messages: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Clear all messages from a conversation.
    
    The conversation still exists but will have no messages.
    """
    try:
        # Check if conversation exists
        if conversation_id not in memory.get_all_conversations():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Clear the conversation
        buffered_memory = memory._get_or_create_buffered_memory(conversation_id)
        buffered_memory.clear()
        
        return {
            "success": True,
            "message": f"Conversation {conversation_id} cleared successfully",
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}/messages/{index}")
async def delete_message(
    conversation_id: str,
    index: int,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Delete a specific message from a conversation by index.
    
    Index is 0-based from the beginning of the conversation.
    """
    try:
        # Get the specific conversation's BufferedMemory
        buffered_memory = memory._get_or_create_buffered_memory(conversation_id)
        
        # Check if index is valid
        messages = buffered_memory.get()
        if index < 0 or index >= len(messages):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid index {index}. Conversation has {len(messages)} messages"
            )
        
        # Delete the message
        buffered_memory.delete(index)
        
        return {
            "success": True,
            "message": f"Message at index {index} deleted successfully",
            "deleted_index": index
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting message: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_conversation_to_hub(
    conversation_id: str,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Manually trigger upload of a conversation to the hub.
    
    This is usually done automatically if auto_upload_to_hub is enabled.
    Returns immediately with 202 Accepted status.
    """
    try:
        # Check if conversation exists
        if conversation_id not in memory.get_all_conversations():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Get the conversation's BufferedMemory
        buffered_memory = memory._get_or_create_buffered_memory(conversation_id)
        
        # Trigger upload
        if hasattr(buffered_memory, 'upload_hub'):
            buffered_memory.upload_hub()
            
            return {
                "message": f"Upload of conversation {conversation_id} initiated",
                "status": "accepted"
            }
        else:
            return {
                "message": "Upload not available for this memory instance",
                "status": "skipped"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading conversation: {str(e)}"
        )


