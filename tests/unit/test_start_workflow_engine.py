from pathlib import Path


def test_start_workflow_engine_uses_catalog_domains_and_routes() -> None:
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "start-workflow-engine.sh"
    ).read_text()

    assert "orchestrator.worker inspect-catalog" in script
    assert 'DOMAIN="story-analysis"' not in script
    assert 'TASK_LIST="story-analysis"' not in script
    assert 'for domain in "${DOMAINS[@]}"' in script
    assert 'for route in "${ROUTES[@]}"' in script
    assert 'if [[ "$WORKER_COUNT" -eq 0 ]]' in script
