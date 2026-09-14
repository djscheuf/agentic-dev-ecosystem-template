import dataclasses


class BaselineResultError(Exception):
    pass


@dataclasses.dataclass
class BaselineResult:
    passing: int
    failing: int
    total: int
    percentage: float
    coverage: dict
    failures: list
    duration: float
    outcome: str


_REQUIRED_FIELDS = {
    "passing",
    "failing",
    "total",
    "percentage",
    "coverage",
    "failures",
    "duration",
    "outcome",
}


class BaselineResultParser:
    def parse(self, raw: dict) -> BaselineResult:
        missing = _REQUIRED_FIELDS - raw.keys()
        if missing:
            raise BaselineResultError(
                f"missing baseline result fields: {sorted(missing)}"
            )
        return BaselineResult(
            **{field: raw[field] for field in _REQUIRED_FIELDS}
        )
