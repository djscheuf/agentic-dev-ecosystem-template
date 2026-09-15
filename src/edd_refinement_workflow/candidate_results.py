import dataclasses


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
