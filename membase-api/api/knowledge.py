from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List, Union, Optional
from membase.knowledge.document import Document
from membase.knowledge.chroma import ChromaKnowledgeBase
from models.knowledge import (
    AddDocumentsRequest,
    AddDocumentsResponse,
    QueryDocumentsRequest,
    QueryDocumentsResponse,
    QueryResult,
    UpdateDocumentsRequest,
    UpdateDocumentsResponse,
    DeleteDocumentsRequest,
    DeleteDocumentsResponse,
    DocumentResponse,
    KnowledgeStatsResponse,
    OptimalThresholdRequest,
    OptimalThresholdResponse,
    ThresholdAnalysis,
    ClearKnowledgeResponse
)
from core.dependencies import knowledge_dep, auth_dep

router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)


def document_to_response(doc: Document) -> DocumentResponse:
    """Convert a Document object to DocumentResponse."""
    return DocumentResponse(
        doc_id=doc.doc_id,
        content=doc.content,
        metadata=doc.metadata,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.post("/documents", response_model=AddDocumentsResponse)
async def add_documents(
    request: AddDocumentsRequest,
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Add one or more documents to the knowledge base.
    
    Documents are automatically embedded and indexed for similarity search.
    Use strict=True to enable duplicate checking.
    """
    try:
        # Convert request documents to Document objects
        docs_to_add = []
        
        if isinstance(request.documents, list):
            for doc_data in request.documents:
                doc = Document(
                    content=doc_data.content,
                    metadata=doc_data.metadata or {}
                )
                docs_to_add.append(doc)
        else:
            doc = Document(
                content=request.documents.content,
                metadata=request.documents.metadata or {}
            )
            docs_to_add.append(doc)
        
        # Add documents to knowledge base
        kb.add_documents(docs_to_add, strict=request.strict)
        
        # Convert to response format
        doc_responses = [document_to_response(doc) for doc in docs_to_add]
        
        return AddDocumentsResponse(
            success=True,
            message=f"Successfully added {len(docs_to_add)} documents",
            documents_added=len(docs_to_add),
            documents=doc_responses
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding documents: {str(e)}"
        )


@router.get("/documents/search", response_model=QueryDocumentsResponse)
async def search_documents(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
    metadata_filter: Optional[str] = None,
    content_filter: Optional[str] = None,
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Search for documents using similarity search.
    
    Returns the most similar documents based on the query, filtered by similarity threshold
    and optional metadata/content filters.
    """
    try:
        # Parse metadata filter if provided as JSON string
        metadata_dict = None
        if metadata_filter:
            import json
            try:
                metadata_dict = json.loads(metadata_filter)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="metadata_filter must be a valid JSON string"
                )
        
        # Retrieve documents
        results = kb.retrieve(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            metadata_filter=metadata_dict,
            content_filter=content_filter
        )
        
        # Convert to response format
        query_results = []
        for doc, score in results:
            query_results.append(QueryResult(
                doc_id=doc.doc_id,
                content=doc.content,
                metadata=doc.metadata,
                similarity_score=score,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            ))
        
        return QueryDocumentsResponse(
            query=query,
            results=query_results,
            total_results=len(query_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )


@router.put("/documents", response_model=UpdateDocumentsResponse)
async def update_documents(
    request: UpdateDocumentsRequest,
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Update one or more existing documents.
    
    Documents must have valid doc_id. Only provided fields will be updated.
    """
    try:
        # Convert request documents to Document objects
        docs_to_update = []
        
        if isinstance(request.documents, list):
            for doc_data in request.documents:
                # Create document with only the fields to update
                doc = Document(
                    content=doc_data.content or "",  # Will be updated if provided
                    metadata=doc_data.metadata or {},
                    doc_id=doc_data.doc_id
                )
                docs_to_update.append(doc)
        else:
            doc = Document(
                content=request.documents.content or "",
                metadata=request.documents.metadata or {},
                doc_id=request.documents.doc_id
            )
            docs_to_update.append(doc)
        
        # Update documents
        updated_count = 0
        for doc in docs_to_update:
            try:
                kb.update_documents(doc)
                updated_count += 1
            except Exception as e:
                # Log error but continue with other updates
                print(f"Failed to update document {doc.doc_id}: {str(e)}")
        
        return UpdateDocumentsResponse(
            success=True,
            message=f"Successfully updated {updated_count} documents",
            documents_updated=updated_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating documents: {str(e)}"
        )


@router.delete("/documents", response_model=DeleteDocumentsResponse)
async def delete_documents(
    doc_ids: Union[str, List[str]],
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Delete one or more documents by their IDs.
    
    Provide a single doc_id or a list of doc_ids to delete.
    """
    try:
        # Ensure doc_ids is a list
        if isinstance(doc_ids, str):
            doc_ids = [doc_ids]
        
        # Delete documents
        deleted_count = kb.delete_documents(doc_ids)
        
        return DeleteDocumentsResponse(
            success=True,
            message=f"Successfully deleted {deleted_count} documents",
            documents_deleted=deleted_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting documents: {str(e)}"
        )


@router.get("/documents/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats(
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Get statistics about the knowledge base.
    
    Returns document count, chunk count, and collection information.
    """
    try:
        stats = kb.get_stats()
        
        # Extract relevant statistics
        total_documents = stats.get('documents', 0)
        total_chunks = stats.get('chunks', 0)
        
        # Get collection names if available
        collections = []
        if 'collections' in stats:
            collections = list(stats['collections'].keys())
        
        return KnowledgeStatsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            collections=collections,
            storage_size_estimate=stats.get('size_estimate')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting knowledge stats: {str(e)}"
        )


@router.post("/documents/optimal-threshold", response_model=OptimalThresholdResponse)
async def find_optimal_threshold(
    request: OptimalThresholdRequest,
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Find the optimal similarity threshold for a given query.
    
    Tests different threshold values and returns result counts and top scores
    to help determine the best threshold for your use case.
    """
    try:
        analysis_results = kb.find_optimal_threshold(
            query=request.query,
            min_threshold=request.min_threshold,
            max_threshold=request.max_threshold,
            step=request.step
        )
        
        # Convert to response format
        threshold_analyses = []
        recommended_threshold = request.min_threshold
        max_good_results = 0
        
        for threshold, results in analysis_results.items():
            result_count = results['result_count']
            top_scores = results['top_scores']
            
            analysis = ThresholdAnalysis(
                threshold=threshold,
                result_count=result_count,
                top_scores=top_scores
            )
            threshold_analyses.append(analysis)
            
            # Simple heuristic for recommended threshold:
            # Find threshold that gives reasonable number of results (2-10)
            if 2 <= result_count <= 10 and result_count > max_good_results:
                recommended_threshold = threshold
                max_good_results = result_count
        
        # Sort by threshold
        threshold_analyses.sort(key=lambda x: x.threshold)
        
        return OptimalThresholdResponse(
            query=request.query,
            analysis=threshold_analyses,
            recommended_threshold=recommended_threshold,
            message=f"Recommended threshold: {recommended_threshold} (returns {max_good_results} results)"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding optimal threshold: {str(e)}"
        )


@router.delete("/documents/all", response_model=ClearKnowledgeResponse)
async def clear_knowledge_base(
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Clear all documents from the knowledge base.
    
    This operation cannot be undone. Use with caution.
    """
    try:
        # Get current stats before clearing
        stats = kb.get_stats()
        doc_count = stats.get('documents', 0)
        
        # Clear the knowledge base
        kb.clear()
        
        return ClearKnowledgeResponse(
            success=True,
            message=f"Successfully cleared {doc_count} documents from knowledge base",
            documents_cleared=doc_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing knowledge base: {str(e)}"
        )


@router.post("/documents/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_knowledge_to_hub(
    background_tasks: BackgroundTasks,
    kb: ChromaKnowledgeBase = knowledge_dep,
    _auth=auth_dep
):
    """
    Manually trigger upload of knowledge base to the hub.
    
    This is usually done automatically if auto_upload_to_hub is enabled.
    Returns immediately and uploads in the background.
    """
    try:
        # Trigger upload in background
        if hasattr(kb, 'upload_hub'):
            background_tasks.add_task(kb.upload_hub)
            
            return {
                "message": "Upload of knowledge base initiated",
                "status": "accepted"
            }
        else:
            return {
                "message": "Upload not available for this knowledge base instance",
                "status": "skipped"
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading knowledge base: {str(e)}"
        )