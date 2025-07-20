from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from membase.memory.multi_memory import MultiMemory
from membase.knowledge.chroma import ChromaKnowledgeBase
try:
    from membase.chain.chain import membase_chain
except Exception as e:
    print(f"Failed to initialize blockchain client: {e}")
    membase_chain = None
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
    if membase_chain is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain client is not available. Check environment variables: MEMBASE_ACCOUNT, MEMBASE_SECRET_KEY, MEMBASE_ID"
        )
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


# AIP service dependencies (lazy loading)
_agent_manager = None
_router_service = None


async def get_agent_manager():
    """Get or create AIPAgentManager singleton instance."""
    global _agent_manager
    if settings.enable_aip:
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
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIP is disabled. Set ENABLE_AIP=true to enable."
        )


async def get_router_service():
    """Get or create AIPRouterService singleton instance."""
    global _router_service
    if settings.enable_aip:
        if _router_service is None:
            try:
                from core.aip import AIPRouterService
                _router_service = AIPRouterService()
                await _router_service.initialize_router()
            except ImportError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"AIP dependencies not available: {str(e)}"
                )
        return _router_service
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIP is disabled. Set ENABLE_AIP=true to enable."
        )


# Dependency injection
memory_dep = Depends(get_multi_memory)
knowledge_dep = Depends(get_knowledge_base)
chain_dep = Depends(get_chain)
auth_dep = Depends(verify_api_key)
agent_manager_dep = Depends(get_agent_manager)
router_service_dep = Depends(get_router_service)