#!/usr/bin/env python3
"""
Saga Models - Data structures for saga orchestration.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union


@dataclass
class NodeDefinition:
    """Defines a node in the saga graph (step or sub-saga)."""
    type: str
    reference: str
    timeout: Optional[int] = None


@dataclass
class ConnectionTarget:
    """Represents a connection target with optional traversal limit."""
    target: str
    traversal_limit: Optional[int] = None


@dataclass
class DirectedConnection:
    """A simple directed connection (then)."""
    node: str
    then: ConnectionTarget
    max_retries: Optional[int] = None


@dataclass
class BranchingConnection:
    """A branching connection (pass/fail)."""
    node: str
    pass_target: ConnectionTarget
    fail_target: ConnectionTarget


Connection = Union[DirectedConnection, BranchingConnection]


@dataclass
class SagaDefinition:
    """Complete saga definition."""
    name: str
    start: str
    nodes: Dict[str, NodeDefinition]
    connections: List[Connection]
    max_recursion_depth: Optional[int] = 50
    enrichment: Dict[str, str] = field(default_factory=dict)
    
    @staticmethod
    def from_dict(data: dict) -> 'SagaDefinition':
        """Parse saga definition from dictionary."""
        name = data.get("name")
        start = data.get("start")
        nodes_data = data.get("nodes", {})
        connections_data = data.get("connections", [])
        max_recursion_depth = data.get("max_recursion_depth", 50)
        
        if not name:
            raise ValueError("Saga definition must include 'name'")
        if not start:
            raise ValueError("Saga definition must include 'start'")
        
        nodes = {}
        for node_name, node_data in nodes_data.items():
            node_type = node_data.get("type")
            reference = node_data.get("reference")
            timeout = node_data.get("timeout")
            
            if not node_type:
                raise ValueError(f"Node '{node_name}' must include 'type'")
            if node_type not in ["step", "saga"]:
                raise ValueError(f"Node '{node_name}' has invalid type '{node_type}' (must be 'step' or 'saga')")
            if not reference:
                raise ValueError(f"Node '{node_name}' must include 'reference'")
            
            nodes[node_name] = NodeDefinition(
                type=node_type,
                reference=reference,
                timeout=timeout
            )
        
        connections = []
        for conn_data in connections_data:
            node = conn_data.get("node")
            if not node:
                raise ValueError("Connection must include 'node'")
            
            # Check if it's a branching connection (has pass/fail)
            if "pass" in conn_data or "fail" in conn_data:
                if "pass" not in conn_data or "fail" not in conn_data:
                    raise ValueError(
                        f"Connection from '{node}' has pass/fail but missing one: "
                        "both 'pass' and 'fail' are required"
                    )
                
                pass_data = conn_data["pass"]
                fail_data = conn_data["fail"]
                
                connections.append(BranchingConnection(
                    node=node,
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
                    node=node,
                    then=ConnectionTarget(
                        target=then_data.get("target") if isinstance(then_data, dict) else then_data,
                        traversal_limit=then_data.get("traversal_limit") if isinstance(then_data, dict) else None
                    ),
                    max_retries=conn_data.get("max_retries") or conn_data.get("max_attempts")
                ))
            else:
                raise ValueError(
                    f"Connection from '{node}' must have either 'then' or 'pass'/'fail'"
                )
        
        enrichment = data.get("enrichment", {})
        
        return SagaDefinition(
            name=name,
            start=start,
            nodes=nodes,
            connections=connections,
            max_recursion_depth=max_recursion_depth,
            enrichment=enrichment
        )
