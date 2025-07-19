from fastapi import APIRouter, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional, Union
import json
import os
import tempfile
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
    MessageResponse,
    DeleteMessageResponse,
    ClearConversationResponse,
    ExportRequest,
    ExportResponse,
    ImportRequest,
    ImportResponse
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


@router.delete("/conversations/{conversation_id}/messages/{index}", response_model=DeleteMessageResponse)
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
        
        return DeleteMessageResponse(
            success=True,
            message=f"Message at index {index} deleted successfully",
            deleted_index=index
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting message: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}", response_model=ClearConversationResponse)
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
        
        return ClearConversationResponse(
            success=True,
            message=f"Conversation {conversation_id} cleared successfully",
            conversation_id=conversation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing conversation: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    request: Optional[ExportRequest] = None,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Export a conversation to a file or return as JSON.
    
    If file_path is provided, saves to that location and returns the file.
    Otherwise, returns the conversation data as JSON in the response.
    """
    try:
        # Get the conversation's BufferedMemory
        buffered_memory = memory._get_or_create_buffered_memory(conversation_id)
        
        if request and request.file_path:
            # Export to file
            buffered_memory.export(request.file_path)
            
            # Return the file
            if os.path.exists(request.file_path):
                return FileResponse(
                    path=request.file_path,
                    media_type='application/json',
                    filename=os.path.basename(request.file_path)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to export to file {request.file_path}"
                )
        else:
            # Export to temporary file and read content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                buffered_memory.export(tmp_path)
                
                with open(tmp_path, 'r') as f:
                    content = json.load(f)
                
                return ExportResponse(
                    success=True,
                    message="Conversation exported successfully",
                    content=content
                )
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting conversation: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/import", response_model=ImportResponse)
async def import_conversation(
    conversation_id: str,
    request: ImportRequest,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Import messages into a conversation from a file or JSON data.
    
    Can optionally clear existing messages before import.
    """
    try:
        # Get the conversation's BufferedMemory
        buffered_memory = memory._get_or_create_buffered_memory(conversation_id)
        
        messages_before = len(buffered_memory.get())
        
        if request.file_path:
            # Import from file
            if not os.path.exists(request.file_path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {request.file_path} not found"
                )
            
            buffered_memory.load(request.file_path, clear_previous=request.clear_previous)
            
        elif request.content:
            # Import from provided content
            # Save to temporary file and load
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                json.dump(request.content, tmp)
                tmp_path = tmp.name
            
            try:
                buffered_memory.load(tmp_path, clear_previous=request.clear_previous)
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either file_path or content must be provided"
            )
        
        messages_after = len(buffered_memory.get())
        messages_imported = messages_after - (0 if request.clear_previous else messages_before)
        
        return ImportResponse(
            success=True,
            message=f"Successfully imported {messages_imported} messages",
            messages_imported=messages_imported
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing conversation: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_conversation_to_hub(
    conversation_id: str,
    background_tasks: BackgroundTasks,
    memory: MultiMemory = memory_dep,
    _auth=auth_dep
):
    """
    Manually trigger upload of a conversation to the hub.
    
    This is usually done automatically if auto_upload_to_hub is enabled.
    Returns immediately and uploads in the background.
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
        
        # Trigger upload in background
        if hasattr(buffered_memory, 'upload_hub'):
            background_tasks.add_task(buffered_memory.upload_hub)
            
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