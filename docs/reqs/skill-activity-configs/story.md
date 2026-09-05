# Skill Activity Configuration

## Story
So that I can run agentic workflow Activities with the capabilities and safeguards appropriate to each task
As a Software Engineer and AI Process Designer
I want to configure the Devin model and tool permissions used by each Skill Activity invocation

## Acceptance Criteria
- Skill Activity invocation settings are defined in a human-readable, version-controlled configuration file.
- The configuration provides default settings that apply when a skill has no explicit override.
- The configuration supports overrides keyed by the canonical skill name, including `extract-story-intent`, `analyze-story`, `grade-story-analysis`, and `repair-story-analysis`.
- Each default or skill-specific profile can select the Devin model used for the invocation.
- Each default or skill-specific profile can select a supported Devin CLI permission mode.
- A skill-specific setting takes precedence over the corresponding default setting, while unspecified values inherit from the defaults.
- The resolved configuration allows unattended skills to create and update files in the repository without requiring interactive confirmation when their permission profile permits those operations.
- Unrestricted tool permissions are not granted by default and must be selected explicitly.
- Invalid configuration, including unsupported permission modes, malformed values, and unusable referenced configuration files, fails before the Devin subprocess is started and reports the affected skill and setting.
- Skill configuration is resolved from structured Skill Activity metadata rather than inferred by parsing the natural-language prompt.
- The generic Skill Activity contract remains independent of Devin-specific command-line details and continues to support alternate Harness implementations.
- Existing skill output and sentinel-file contracts remain unchanged.
- Each Activity log records the skill name and resolved model, permission mode, and any referenced Devin configuration profile without recording credentials or other secrets.
- Cadence retries apply the documented configuration consistency policy so operators can determine whether all attempts use a workflow-start snapshot or the latest Activity-side configuration.
- Existing installations using the current global model and permission-mode configuration either remain compatible or receive a clear migration error with corrective guidance.
- Automated tests cover default resolution, per-skill overrides, partial inheritance, invalid configuration, subprocess argument construction, alternate Harness compatibility, and safe logging.
- The configuration format, precedence rules, supported values, retry behavior, security implications, and local-development examples are documented for other users.
