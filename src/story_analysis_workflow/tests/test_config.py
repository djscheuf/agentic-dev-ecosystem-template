import json
import os
from datetime import timedelta
from pathlib import Path

import pytest

from story_analysis_workflow.config import CadenceConfig, load_config


def test_config_loads_defaults_from_json_file(tmp_path):
    config_path = tmp_path / "domain-task-list-retry-config.json"
    config_path.write_text(
        json.dumps(
            {
                "domain": "story-analysis",
                "task_list": "story-analysis",
                "cadence_target": "localhost:7833",
                "workflow_defaults": {"execution_start_to_close_timeout_seconds": 3600, "task_start_to_close_timeout_seconds": 10},
                "human_escalation": {"timeout_seconds": 300},
            }
        )
    )

    config = load_config(config_path)

    assert config.domain == "story-analysis"
    assert config.task_list == "story-analysis"
    assert config.cadence_target == "localhost:7833"
    assert config.execution_start_to_close_timeout == timedelta(hours=1)
    assert config.task_start_to_close_timeout == timedelta(seconds=10)
    assert config.escalation_timeout == timedelta(minutes=5)


def test_config_allows_overrides(tmp_path):
    config_path = tmp_path / "domain-task-list-retry-config.json"
    config_path.write_text(
        json.dumps(
            {
                "domain": "story-analysis",
                "task_list": "story-analysis",
                "cadence_target": "localhost:7833",
                "workflow_defaults": {"execution_start_to_close_timeout_seconds": 3600},
                "human_escalation": {"timeout_seconds": 300},
            }
        )
    )

    config = load_config(
        config_path,
        domain="other-domain",
        task_list="other-task-list",
        cadence_target="host:9999",
        execution_start_to_close_timeout_seconds=60,
        escalation_timeout_seconds=30,
    )

    assert config.domain == "other-domain"
    assert config.task_list == "other-task-list"
    assert config.cadence_target == "host:9999"
    assert config.execution_start_to_close_timeout == timedelta(seconds=60)
    assert config.escalation_timeout == timedelta(seconds=30)


def test_config_falls_back_to_environment_variables_and_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("CADENCE_DOMAIN", "env-domain")
    monkeypatch.setenv("CADENCE_TARGET", "env:1234")

    config = load_config(tmp_path / "missing.json")

    assert config.domain == "env-domain"
    assert config.cadence_target == "env:1234"
    assert config.task_list == "story-analysis"
    assert config.execution_start_to_close_timeout == timedelta(hours=1)


def test_config_to_start_workflow_kwargs_includes_required_options():
    config = CadenceConfig(
        domain="story-analysis",
        task_list="story-analysis",
        cadence_target="localhost:7833",
        execution_start_to_close_timeout=timedelta(hours=1),
        task_start_to_close_timeout=timedelta(seconds=10),
        escalation_timeout=timedelta(minutes=5),
    )

    kwargs = config.to_start_workflow_kwargs("wf-1")

    assert kwargs["workflow_id"] == "wf-1"
    assert kwargs["task_list"] == "story-analysis"
    assert kwargs["execution_start_to_close_timeout"] == timedelta(hours=1)
    assert kwargs["task_start_to_close_timeout"] == timedelta(seconds=10)
