from common.invocation_context import get_current_skill_name, skill_invocation_context


def test_skill_invocation_context_restores_nested_value() -> None:
    assert get_current_skill_name() is None

    with skill_invocation_context("outer"):
        assert get_current_skill_name() == "outer"
        with skill_invocation_context("inner"):
            assert get_current_skill_name() == "inner"
        assert get_current_skill_name() == "outer"

    assert get_current_skill_name() is None
