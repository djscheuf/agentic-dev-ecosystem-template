class EvaluationIdentityError(Exception):
    """Raised when an evaluation identity cannot be extracted or used."""


_PLACEHOLDER = "{evaluation_id}"


def extract_evaluation_id(result: dict) -> str:
    """Return the evaluation identity from a test command result.

    The identity may be reported as ``evaluation_id`` or ``id``.  The
    ``evaluation_id`` key is preferred when both are present.
    """
    for key in ("evaluation_id", "id"):
        value = result.get(key)
        if value:
            return str(value)
    raise EvaluationIdentityError(
        f"evaluation result missing evaluation_id: {sorted(result.keys())}"
    )


def build_inspect_command(inspect_command: list[str], evaluation_id: str) -> list[str]:
    """Return a copy of ``inspect_command`` with the evaluation id interpolated.

    Only the literal ``{evaluation_id}`` placeholder is replaced in each
    argument.  Static arguments are returned unchanged.
    """
    if not evaluation_id:
        raise EvaluationIdentityError("evaluation_id is required to build inspect command")
    return [arg.replace(_PLACEHOLDER, evaluation_id) for arg in inspect_command]
