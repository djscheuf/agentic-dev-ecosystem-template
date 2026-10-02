"""Unit tests for vendor-independent usage coercion helpers."""

from common.harness_usage import coerce_cost, coerce_token


class TestCoerceToken:
    def test_int_value_returned_unchanged(self) -> None:
        assert coerce_token(42) == 42

    def test_bool_value_rejected(self) -> None:
        assert coerce_token(True) is None
        assert coerce_token(False) is None

    def test_non_int_value_rejected(self) -> None:
        assert coerce_token("42") is None
        assert coerce_token(4.2) is None
        assert coerce_token(None) is None


class TestCoerceCost:
    def test_int_value_coerced_to_float(self) -> None:
        assert coerce_cost(2) == 2.0

    def test_float_value_returned_unchanged(self) -> None:
        assert coerce_cost(0.5) == 0.5

    def test_bool_value_rejected(self) -> None:
        assert coerce_cost(True) is None
        assert coerce_cost(False) is None

    def test_non_numeric_value_rejected(self) -> None:
        assert coerce_cost("0.5") is None
        assert coerce_cost(None) is None
