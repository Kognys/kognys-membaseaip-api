"""AIP Agent Manager for handling agent lifecycle and communication."""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime

from core.config import settings
from .exceptions import AgentNotFoundError, AgentTimeoutError

logger = logging.getLogger(__name__)


class ActiveAgentInfo:
    """Information about an active agent."""
    def __init__(self, agent_id: str, description: str, created_at: datetime):
        self.agent_id = agent_id
        self.description = description
        self.created_at = created_at
        self.status = "running"


class AIPAgentManager:
    """Manages AIP agent lifecycle and communication."""
    
    def __init__(self):
        self._agents: Dict[str, ActiveAgentInfo] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the agent manager."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                self._initialized = True
                logger.info("AIP Agent Manager initialized (simplified mode)")
            except Exception as e:
                logger.error(f"Failed to initialize AIP Agent Manager: {e}")
                raise
    
    async def create_agent(self, agent_id: str, description: str = "AIP Agent", 
                          default_conversation_id: Optional[str] = None) -> ActiveAgentInfo:
        """Create a simplified AIP agent (no LLM dependencies)."""
        if not self._initialized:
            await self.initialize()
            
        # Check if agent already exists
        if agent_id in self._agents:
            return self._agents[agent_id]
            
        # Check max agents limit
        if len(self._agents) >= settings.aip_max_agents:
            raise Exception(f"Maximum number of agents ({settings.aip_max_agents}) reached")
            
        try:
            # Create simplified agent info without complex dependencies
            agent_info = ActiveAgentInfo(
                agent_id=agent_id,
                description=description, 
                created_at=datetime.utcnow()
            )
            self._agents[agent_id] = agent_info
            
            logger.info(f"Created simplified AIP agent: {agent_id}")
            return agent_info
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_id}: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[ActiveAgentInfo]:
        """Get active agent by ID."""
        return self._agents.get(agent_id)
    
    async def process_query(self, agent_id: str, query: str, 
                          conversation_id: Optional[str] = None,
                          use_history: bool = True,
                          system_prompt: Optional[str] = None,
                          recent_n_messages: int = 16,
                          use_tool_call: bool = True) -> str:
        """Process a query through an agent (simplified - no LLM processing)."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)
            
        try:
            # Simplified response without LLM processing
            response = f"Agent {agent_id} received query: {query}"
            logger.info(f"Processed query for agent {agent_id}")
            return response
        except Exception as e:
            logger.error(f"Error processing query for agent {agent_id}: {e}")
            raise
    
    async def send_message(self, source_id: str, target_id: str, action: str, message: str) -> str:
        """Send message from one agent to another (simplified)."""
        source_agent = await self.get_agent(source_id)
        if not source_agent:
            raise AgentNotFoundError(source_id)
            
        target_agent = await self.get_agent(target_id)
        if not target_agent:
            raise AgentNotFoundError(target_id)
            
        try:
            response = f"Message sent from {source_id} to {target_id}: {action} - {message}"
            logger.info(f"Message sent from {source_id} to {target_id}")
            return response
        except Exception as e:
            logger.error(f"Error sending message from {source_id} to {target_id}: {e}")
            raise
    
    async def update_prompt(self, agent_id: str, prompt: str) -> None:
        """Update agent's system prompt (simplified)."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)
            
        try:
            # Store prompt in agent description for simplified implementation
            agent.description = prompt
            logger.info(f"Updated system prompt for agent {agent_id}")
        except Exception as e:
            logger.error(f"Error updating prompt for agent {agent_id}: {e}")
            raise
    
    async def list_active_agents(self) -> List[Dict]:
        """List all active agents."""
        return [
            {
                "agent_id": info.agent_id,
                "status": info.status,
                "created_at": info.created_at.isoformat(),
                "description": info.description
            }
            for info in self._agents.values()
        ]
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop and cleanup agent."""
        agent_info = self._agents.get(agent_id)
        if not agent_info:
            raise AgentNotFoundError(agent_id)
            
        try:
            del self._agents[agent_id]
            logger.info(f"Stopped agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            raise
    
    async def cleanup(self):
        """Clean up all agents."""
        for agent_id in list(self._agents.keys()):
            try:
                await self.stop_agent(agent_id)
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {e}")