#!/usr/bin/env python3
"""
AgentWrapper - Abstract base class for agent implementations.

Defines the interface that all agent wrappers (DevinWrapper, etc.) must implement.
This enables the Orchestrator to work with multiple agent types without modification.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional


class AgentWrapper(ABC):
    """Abstract base class for agent wrappers.
    
    All agent implementations must inherit from this class and implement
    the execute_prompt() method.
    """
    
    @abstractmethod
    def execute_prompt(
        self,
        prompt: str,
        agent_config: str,
        timeout: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Execute a prompt with the agent.
        
        Args:
            prompt: The prompt to execute
            agent_config: Path to agent configuration file
            timeout: Optional timeout in seconds
            session_id: Optional session ID to resume an existing session
        
        Returns:
            Tuple[str, Optional[str]]: (output, session_id)
                - output: The agent's output/response
                - session_id: The session ID (new or resumed)
        """
        pass
