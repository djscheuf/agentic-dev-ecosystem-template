#!/usr/bin/env python3
"""
Enrichment Dictionary - Maintains saga context for prompt enrichment.
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


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


def substitute_variables(prompt: str, enrichment: EnrichmentDictionary) -> str:
    """
    Substitute variables in prompt using enrichment dictionary.
    
    Supports {{variable}} syntax for single-pass substitution.
    Undefined variables remain as-is.
    
    Args:
        prompt: Prompt text with {{variable}} placeholders
        enrichment: EnrichmentDictionary with variable values
        
    Returns:
        Prompt with variables substituted
    """
    if not prompt:
        return prompt
    
    result = prompt
    
    # Build variable map from enrichment
    variables = {
        "saga_id": enrichment.saga_id,
        "state_storage_location": enrichment.state_storage_location,
        "initial_prompt_path": enrichment.initial_prompt_path,
        "previous_step_output": enrichment.previous_step_output,
        "previous_step_error": enrichment.previous_step_error,
    }
    
    # Add custom variables
    variables.update(enrichment.custom_variables)
    
    # Single-pass substitution: replace {{variable}} with value if it exists
    def replace_var(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))
    
    result = re.sub(r'\{\{(\w+)\}\}', replace_var, result)
    
    return result
