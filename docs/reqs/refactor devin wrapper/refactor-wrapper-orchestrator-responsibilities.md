# Refactor: Wrapper and Orchestrator Responsibility Split

## Problem Statement

The `DevinWrapper` currently handles too many concerns:
- CLI interface wrapping (appropriate)
- Instrumentation orchestration (inappropriate)
- Verification script invocation (inappropriate)
- Session state management (partially appropriate)
- Logging and output redirection (partially appropriate)

This violates separation of concerns and makes the wrapper tightly coupled to saga execution details.

## Desired Architecture

### Wrapper Responsibility (Minimal)
The wrapper should be a **thin CLI interface adapter**:
1. Accept a prompt and agent configuration
2. Pass them to the Devin CLI tool
3. Capture and return the output
4. Return session ID if available
5. Enforce timeout if specified
6. Optionally resume an existing session

### Orchestrator Responsibility (Expanded)
The orchestrator should handle **all instrumentation and state management**:
1. Load step definition data
2. Enrich the prompt with context
3. Invoke the wrapper with enriched prompt + agent config
4. Enforce timeout around the wrapper call
5. Capture output into saga/step state
6. Invoke the step's verification script
7. Manage logging destinations
8. Handle session resumption logic

### Saga Responsibility (Clarified)
When a saga determines it needs to execute a step:
1. Call `orchestrator.invoke_step(step_id)` 
2. Let the orchestrator handle all step execution details
3. Receive back the result and state

## Generic Agent Wrapper Interface

```python
class AgentWrapper:
    """Generic interface for agent CLI tools."""
    
    def execute_prompt(
        self,
        prompt: str,
        agent_config: dict | str,
        timeout: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Execute a prompt with the agent.
        
        Args:
            prompt: The prompt to send to the agent
            agent_config: Agent configuration (dict or path to config file)
            timeout: Optional timeout in seconds
            session_id: Optional session ID to resume
        
        Returns:
            Tuple[output, session_id]:
                - output: The agent's response/output
                - session_id: The session ID (new or resumed)
        """
        pass
```

## Key Design Decisions

- **Wrapper is stateless**: No session file management, no logging to files
- **Orchestrator owns session lifecycle**: Manages session_id.txt, feedback.txt, stderr.txt
- **Timeout enforcement at orchestrator level**: Wrapper receives timeout but orchestrator enforces it
- **Verification is orchestrator responsibility**: Not wrapper responsibility
- **Generic interface enables future agents**: Can swap Devin for Claude, Anthropic, etc.

## Current Code Locations

- Wrapper: `/orchestrator/devin_wrapper.py`
- Orchestrator: `/orchestrator/saga_executor.py` (needs expansion)
- Saga executor: `/orchestrator/saga_executor.py`
