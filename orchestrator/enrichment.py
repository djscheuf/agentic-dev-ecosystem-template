#!/usr/bin/env python3
"""
Enrichment utilities - Variable substitution for prompts.
"""

import re

try:
    from .models import EnrichmentDictionary
except ImportError:
    from models import EnrichmentDictionary


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
