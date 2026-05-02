#!/usr/bin/env python3
"""
Saga Models - Data structures for saga orchestration.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Union


@dataclass
class ConnectionTarget:
    """Represents a connection target with optional traversal limit."""
    target: str
    traversal_limit: Optional[int] = None


@dataclass
class DirectedConnection:
    """A simple directed connection (then)."""
    origin: str
    then: ConnectionTarget


@dataclass
class BranchingConnection:
    """A branching connection (pass/fail)."""
    origin: str
    pass_target: ConnectionTarget
    fail_target: ConnectionTarget


Connection = Union[DirectedConnection, BranchingConnection]


@dataclass
class SagaDefinition:
    """Complete saga definition."""
    name: str
    start: str
    connections: List[Connection]
    
    @staticmethod
    def from_dict(data: dict) -> 'SagaDefinition':
        """Parse saga definition from dictionary."""
        name = data.get("name")
        start = data.get("start")
        connections_data = data.get("connections", [])
        
        if not name:
            raise ValueError("Saga definition must include 'name'")
        if not start:
            raise ValueError("Saga definition must include 'start'")
        
        connections = []
        for conn_data in connections_data:
            origin = conn_data.get("origin")
            if not origin:
                raise ValueError("Connection must include 'origin'")
            
            # Check if it's a branching connection (has pass/fail)
            if "pass" in conn_data or "fail" in conn_data:
                if "pass" not in conn_data or "fail" not in conn_data:
                    raise ValueError(
                        f"Connection from '{origin}' has pass/fail but missing one: "
                        "both 'pass' and 'fail' are required"
                    )
                
                pass_data = conn_data["pass"]
                fail_data = conn_data["fail"]
                
                connections.append(BranchingConnection(
                    origin=origin,
                    pass_target=ConnectionTarget(
                        target=pass_data.get("target") if isinstance(pass_data, dict) else pass_data,
                        traversal_limit=pass_data.get("traversal_limit") if isinstance(pass_data, dict) else None
                    ),
                    fail_target=ConnectionTarget(
                        target=fail_data.get("target") if isinstance(fail_data, dict) else fail_data,
                        traversal_limit=fail_data.get("traversal_limit") if isinstance(fail_data, dict) else None
                    )
                ))
            
            # Check if it's a directed connection (has then)
            elif "then" in conn_data:
                then_data = conn_data["then"]
                connections.append(DirectedConnection(
                    origin=origin,
                    then=ConnectionTarget(
                        target=then_data.get("target") if isinstance(then_data, dict) else then_data,
                        traversal_limit=then_data.get("traversal_limit") if isinstance(then_data, dict) else None
                    )
                ))
            else:
                raise ValueError(
                    f"Connection from '{origin}' must have either 'then' or 'pass'/'fail'"
                )
        
        return SagaDefinition(name=name, start=start, connections=connections)
