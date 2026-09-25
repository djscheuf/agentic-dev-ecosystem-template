import dataclasses


@dataclasses.dataclass(frozen=True)
class EvaluationRunConfiguration:
    command: list[str]
    configuration: str
    pinned_provider_version: str
    timeout_seconds: int
    measurement_context: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class CandidateMetricRecord:
    candidate_id: str
    run_id: str
    attempt_number: int
    passing: int
    failing: int
    total: int
    percentage: float
    required_coverage: dict[str, int]
    artifact_references: list[str]
    pinned_provider_version: str
    measurement_context: str
    evaluated_at: str
    status: str
    failure_reason: str | None
    usable_for_acceptance: bool

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class UsageMetrics:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float


@dataclasses.dataclass(frozen=True)
class ExecutionResult:
    status: str
    usage_metrics: UsageMetrics
    changed_files: list[str]
    diff_hash: str
    failure_reason: str | None
    atif_path: str | None
    duration_ms: int


@dataclasses.dataclass(frozen=True)
class CandidateValidationResult:
    candidate_id: str
    run_id: str
    status: str
    usage_metrics: UsageMetrics
    changed_files: list[str]
    diff_hash: str
    rejection_reason: str | None
    validated_at: str
    out_of_scope_details: dict | None = None
