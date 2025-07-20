"""AIP Agent Manager for handling agent lifecycle and communication."""

import asyncio
import logging
import sys
import os
from typing import Dict, Optional, List
from datetime import datetime

# Add aip-agent to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../aip-agent/src'))

from aip_agent.agents.full_agent import FullAgentWrapper
from aip_agent.agents.agent import Agent
from aip_agent.grpc import GrpcWorkerAgentRuntime
from aip_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from core.config import settings
from .exceptions import AgentNotFoundError, AgentTimeoutError

logger = logging.getLogger(__name__)


class ActiveAgentInfo:
    """Information about an active agent."""
    def __init__(self, agent_id: str, wrapper: FullAgentWrapper, created_at: datetime):
        self.agent_id = agent_id
        self.wrapper = wrapper
        self.created_at = created_at
        self.status = "running"
        self.description = wrapper._description


class AIPAgentManager:
    """Manages AIP agent lifecycle and communication."""
    
    def __init__(self):
        self._agents: Dict[str, ActiveAgentInfo] = {}
        self._runtime: Optional[GrpcWorkerAgentRuntime] = None
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
                # Initialize gRPC runtime
                self._runtime = GrpcWorkerAgentRuntime(settings.aip_grpc_host)
                self._initialized = True
                logger.info(f"AIP Agent Manager initialized with gRPC host: {settings.aip_grpc_host}")
            except Exception as e:
                logger.error(f"Failed to initialize AIP Agent Manager: {e}")
                raise
    
    async def create_agent(self, agent_id: str, description: str = "AIP Agent", 
                          default_conversation_id: Optional[str] = None) -> ActiveAgentInfo:
        """Create and initialize an AIP agent."""
        if not self._initialized:
            await self.initialize()
            
        # Check if agent already exists
        if agent_id in self._agents:
            return self._agents[agent_id]
            
        # Check max agents limit
        if len(self._agents) >= settings.aip_max_agents:
            raise Exception(f"Maximum number of agents ({settings.aip_max_agents}) reached")
            
        try:
            # Create agent wrapper without LLM
            wrapper = FullAgentWrapper(
                agent_cls=Agent,
                name=agent_id,
                host_address=settings.aip_grpc_host,
                description=description,
                runtime=self._runtime,
                default_conversation_id=default_conversation_id
            )
            
            # Initialize the agent (it will create its own LLM internally)
            await wrapper.initialize()
            
            # Store agent info
            agent_info = ActiveAgentInfo(agent_id, wrapper, datetime.utcnow())
            self._agents[agent_id] = agent_info
            
            logger.info(f"Created AIP agent: {agent_id}")
            return agent_info
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_id}: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[FullAgentWrapper]:
        """Get active agent by ID."""
        agent_info = self._agents.get(agent_id)
        return agent_info.wrapper if agent_info else None
    
    async def process_query(self, agent_id: str, query: str, 
                          conversation_id: Optional[str] = None,
                          use_history: bool = True,
                          system_prompt: Optional[str] = None,
                          recent_n_messages: int = 16,
                          use_tool_call: bool = True) -> str:
        """Process a query through an agent."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)
            
        try:
            response = await agent.process_query(
                query=query,
                conversation_id=conversation_id,
                use_history=use_history,
                system_prompt=system_prompt,
                recent_n_messages=recent_n_messages,
                use_tool_call=use_tool_call
            )
            return response
        except asyncio.TimeoutError:
            raise AgentTimeoutError(agent_id, "process_query", settings.aip_agent_timeout)
        except Exception as e:
            logger.error(f"Error processing query for agent {agent_id}: {e}")
            raise
    
    async def send_message(self, source_id: str, target_id: str, action: str, message: str) -> str:
        """Send message from one agent to another."""
        source_agent = await self.get_agent(source_id)
        if not source_agent:
            raise AgentNotFoundError(source_id)
            
        try:
            response = await source_agent.send_message(target_id, action, message)
            return response
        except asyncio.TimeoutError:
            raise AgentTimeoutError(source_id, "send_message", settings.aip_agent_timeout)
        except Exception as e:
            logger.error(f"Error sending message from {source_id} to {target_id}: {e}")
            raise
    
    async def update_prompt(self, agent_id: str, prompt: str) -> None:
        """Update agent's system prompt."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)
            
        try:
            await agent.set_system_prompt(prompt)
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
            await agent_info.wrapper.stop()
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