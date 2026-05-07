#!/usr/bin/env python3
"""
Enrichment Dictionary - Maintains saga context for prompt enrichment.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any


@dataclass
class EnrichmentDictionary:
    """Maintains enrichment context for saga execution."""
    
    saga_id: str
    state_storage_location: str
    initial_prompt_path: str
    custom_variables: Dict[str, str] = field(default_factory=dict)
    previous_step_output: str = ""
    previous_step_error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'EnrichmentDictionary':
        """Reconstruct from dictionary."""
        return EnrichmentDictionary(
            saga_id=data["saga_id"],
            state_storage_location=data["state_storage_location"],
            initial_prompt_path=data["initial_prompt_path"],
            custom_variables=data.get("custom_variables", {}),
            previous_step_output=data.get("previous_step_output", ""),
            previous_step_error=data.get("previous_step_error", "")
        )
