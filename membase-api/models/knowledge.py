from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class DocumentCreate(BaseModel):
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Document metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Python is a high-level programming language...",
                "metadata": {
                    "source": "documentation",
                    "category": "programming",
                    "date": "2024-01-15"
                }
            }
        }


class DocumentUpdate(BaseModel):
    doc_id: str = Field(..., description="Document ID to update")
    content: Optional[str] = Field(None, description="New content (optional)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc-123",
                "content": "Updated content...",
                "metadata": {"updated": True}
            }
        }


class DocumentResponse(BaseModel):
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AddDocumentsRequest(BaseModel):
    documents: Union[DocumentCreate, List[DocumentCreate]] = Field(..., description="Document or list of documents to add")
    strict: bool = Field(False, description="Enable strict duplicate checking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": {
                    "content": "Machine learning is a subset of AI...",
                    "metadata": {"topic": "AI"}
                },
                "strict": True
            }
        }


class AddDocumentsResponse(BaseModel):
    success: bool
    message: str
    documents_added: int
    documents: List[DocumentResponse]


class QueryDocumentsRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Filter by metadata")
    content_filter: Optional[str] = Field(None, description="Filter by content substring")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is machine learning?",
                "top_k": 10,
                "similarity_threshold": 0.8,
                "metadata_filter": {"category": "AI"}
            }
        }


class QueryResult(BaseModel):
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    created_at: datetime
    updated_at: datetime


class QueryDocumentsResponse(BaseModel):
    query: str
    results: List[QueryResult]
    total_results: int


class UpdateDocumentsRequest(BaseModel):
    documents: Union[DocumentUpdate, List[DocumentUpdate]] = Field(..., description="Document or list of documents to update")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": {
                    "doc_id": "doc-123",
                    "content": "Updated content for the document"
                }
            }
        }


class UpdateDocumentsResponse(BaseModel):
    success: bool
    message: str
    documents_updated: int


class DeleteDocumentsRequest(BaseModel):
    doc_ids: Union[str, List[str]] = Field(..., description="Document ID or list of IDs to delete")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_ids": ["doc-123", "doc-456"]
            }
        }


class DeleteDocumentsResponse(BaseModel):
    success: bool
    message: str
    documents_deleted: int


class KnowledgeStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    collections: List[str]
    storage_size_estimate: Optional[str] = None


class OptimalThresholdRequest(BaseModel):
    query: str = Field(..., description="Query to test")
    min_threshold: float = Field(0.3, description="Minimum threshold to test", ge=0.0, le=1.0)
    max_threshold: float = Field(0.9, description="Maximum threshold to test", ge=0.0, le=1.0)
    step: float = Field(0.1, description="Step size for threshold testing", ge=0.01, le=0.5)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "min_threshold": 0.3,
                "max_threshold": 0.9,
                "step": 0.1
            }
        }


class ThresholdAnalysis(BaseModel):
    threshold: float
    result_count: int
    top_scores: List[float]


class OptimalThresholdResponse(BaseModel):
    query: str
    analysis: List[ThresholdAnalysis]
    recommended_threshold: float
    message: str


class ClearKnowledgeResponse(BaseModel):
    success: bool
    message: str
    documents_cleared: int