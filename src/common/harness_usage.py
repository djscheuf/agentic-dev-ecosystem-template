"""Vendor-independent coercion helpers shared by harness usage parsers."""


def coerce_token(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def coerce_cost(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None
