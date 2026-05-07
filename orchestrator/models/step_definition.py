from pathlib import Path
from typing import Optional


class StepDefinition:
    """Represents a step definition for Devin execution."""
    
    def __init__(self, data: dict, step_def_dir: Path):
        self.prompt = data.get("prompt")
        self.model = data.get("model")
        self.budget = data.get("budget")
        self.timeout = data.get("timeout")
        self.verify = data.get("verify")
        self.agent_config = data.get("agent_config")
        self.step_def_dir = step_def_dir
        
        if not self.prompt:
            raise ValueError("Step definition must include 'prompt' property")
        if not self.model:
            raise ValueError("Step definition must include 'model' property")
    
    def get_prompt_content(self) -> str:
        """Get prompt content, either directly or from file."""
        # Resolve prompt file path relative to step definition directory
        prompt_path = Path(self.prompt)
        if not prompt_path.is_absolute():
            prompt_path = self.step_def_dir / prompt_path
        
        if prompt_path.exists():
            return prompt_path.read_text()
        return self.prompt
    
    def get_agent_config_path(self) -> Optional[Path]:
        """Get agent config path, resolving relative paths to step directory.
        
        Returns:
            Path: Resolved path to agent config file, or None if not specified.
                  Relative paths are resolved relative to step_def_dir.
                  Absolute paths are returned as-is.
        """
        # Return None if agent_config is not specified, empty, or null
        if not self.agent_config:
            return None
        
        config_path = Path(self.agent_config)
        
        # If absolute path, return as-is
        if config_path.is_absolute():
            return config_path
        
        # Resolve relative path relative to step definition directory
        return self.step_def_dir / config_path
