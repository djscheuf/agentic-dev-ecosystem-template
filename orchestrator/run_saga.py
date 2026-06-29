#!/usr/bin/env python3
"""
Saga Orchestrator - Main CLI entry point for executing sagas.

Usage:
    python run_saga.py <saga_definition.json> [input_files...]
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add orchestrator directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import SagaDefinition
from saga_validator import validate_saga
from saga_executor import execute_saga

# Configuration: Set to True to keep attempt logs for debugging
KEEP_ATTEMPT_LOGS = True


def load_saga_definition(path: str) -> SagaDefinition:
    """Load and parse saga definition JSON file."""
    saga_file = Path(path)
    
    if not saga_file.exists():
        raise FileNotFoundError(f"Saga definition file not found: {path}")
    
    try:
        data = json.loads(saga_file.read_text())
        return SagaDefinition.from_dict(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in saga definition: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing saga definition: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_saga.py <saga_definition.json> [input_files...]", file=sys.stderr)
        sys.exit(1)
    
    saga_def_path = sys.argv[1]
    initial_inputs = sys.argv[2:]
    
    try:
        print("[Saga Orchestrator] Loading saga definition...")
        saga = load_saga_definition(saga_def_path)
        print(f"[Saga Orchestrator] Loaded saga: {saga.name}")
        
        repo_root = Path(__file__).parent.parent
        steps_dir = repo_root / "steps"
        sagas_dir = repo_root / "sagas"
        
        if not steps_dir.exists():
            print(f"[Saga Orchestrator] ERROR: Steps directory not found: {steps_dir}", file=sys.stderr)
            sys.exit(1)
        
        if not sagas_dir.exists():
            print(f"[Saga Orchestrator] ERROR: Sagas directory not found: {sagas_dir}", file=sys.stderr)
            sys.exit(1)
        
        print("[Saga Orchestrator] Validating saga definition...")
        is_valid, errors, warnings = validate_saga(saga, steps_dir, sagas_dir)
        
        if not is_valid:
            print("[Saga Orchestrator] ERROR: Saga validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)
        
        if warnings:
            print("[Saga Orchestrator] Warnings:")
            for warning in warnings:
                print(f"  ⚠ {warning}")
        
        print("[Saga Orchestrator] ✓ Saga validation passed")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = repo_root / ".process" / "saga-logs"
        log_path = log_dir / f"{saga.name}_{timestamp}.log"
        
        print(f"[Saga Orchestrator] Execution log: {log_path}")
        print("[Saga Orchestrator] Starting saga execution...\n")
        
        saga_path_abs = str(Path(saga_def_path).resolve())
        original_input = initial_inputs[0] if initial_inputs else ""
        success, final_outputs = execute_saga(saga, steps_dir, sagas_dir, log_path, initial_inputs, saga_path_abs, original_input, KEEP_ATTEMPT_LOGS)
        
        if success:
            print(f"\n[Saga Orchestrator] ✓ Saga '{saga.name}' completed successfully")
            sys.exit(0)
        else:
            print(f"\n[Saga Orchestrator] ✗ Saga '{saga.name}' failed", file=sys.stderr)
            print(f"[Saga Orchestrator] Check log for details: {log_path}", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"[Saga Orchestrator] FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
