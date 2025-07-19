from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from membase.memory.multi_memory import MultiMemory
from membase.knowledge.chroma import ChromaKnowledgeBase
from membase.chain.chain import membase_chain
from core.config import settings


# Singleton instances
_multi_memory: Optional[MultiMemory] = None
_knowledge_base: Optional[ChromaKnowledgeBase] = None


def get_multi_memory() -> MultiMemory:
    """Get or create MultiMemory singleton instance."""
    global _multi_memory
    if _multi_memory is None:
        _multi_memory = MultiMemory(
            membase_account=settings.membase_account,
            auto_upload_to_hub=True,
            preload_from_hub=True
        )
    return _multi_memory


def get_knowledge_base() -> ChromaKnowledgeBase:
    """Get or create ChromaKnowledgeBase singleton instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = ChromaKnowledgeBase(
            persist_directory=settings.chroma_persist_dir,
            membase_account=settings.membase_account,
            auto_upload_to_hub=True
        )
    return _knowledge_base


def get_chain():
    """Get the membase chain client."""
    return membase_chain


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify API key if configured."""
    if settings.api_key is None:
        # No API key configured, allow access
        return True
    
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return True


# Dependency injection
memory_dep = Depends(get_multi_memory)
knowledge_dep = Depends(get_knowledge_base)
chain_dep = Depends(get_chain)
auth_dep = Depends(verify_api_key)