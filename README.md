# Agentic Development Ecosystem Template

A comprehensive template repository containing rules, workflows, and skills for AI-assisted development with Windsurf. This ecosystem provides a structured approach to multiply developer impact through systematic use of AI pair programming patterns.

## Purpose

This repository serves as a template for establishing effective AI-assisted development practices. It provides:

- **Reusable Rules**: Coding standards and AI interaction patterns
- **Proven Workflows**: Step-by-step processes for common development scenarios
- **Example Sequences**: Real-world usage patterns showing inputs, outputs, and workflow combinations
- **Persona Patterns**: Specialized AI interaction modes for different development needs

## Workflow Sequences

### Brownfield Projects (Joining Existing Codebases)

When joining an existing project, start with documentation:

1. **[Explore Codebase](.windsurf/workflows/explore-codebase.md)** → Generate living documentation of the existing system
   - Input: Existing codebase
   - Output: Structured documentation of architecture, patterns, and key components

### Greenfield Projects (Starting Fresh)

For new projects, establish standards first:

1. **Active Partner Conversation** → Define coding standards and target architecture
   - Input: Project goals, technology preferences, quality standards
   - Output: Documented coding standards, architectural decisions, project structure

### Feature Development (User Story Implementation)

For implementing user stories with defined personas, user value, and BDD-style acceptance criteria:

1. **[Analyze User Story](.windsurf/workflows/analyze-user-story.md)** → Deep analysis of requirements
   - Input: User story (persona + value + BDD acceptance criteria)
   - Output: Analysis document with clarifying questions
   
2. **Clarification Round** → Answer questions and resolve ambiguities
   - Input: Responses to analysis questions
   - Output: Confirmed understanding and refined requirements

3. **[Planning](.windsurf/workflows/planning.md)** → Generate implementation plan
   - Input: Analyzed and clarified user story
   - Output: Step-by-step implementation plan

4. **[Design Buddy](.windsurf/rules/design-buddy.md) Conversation** → Evaluate design and refine plan
   - Input: Implementation plan
   - Output: Design-reviewed plan focused on effective solutions rather than problem fixation

5. **[TDD Workflow](.windsurf/workflows/tdd-workflow.md)** → Iterative test-driven implementation
   - Input: Implementation plan
   - Process: For each step:
     - Think about what to implement
     - Write a failing test
     - Implement code to pass the test
     - Refactor for cleanliness
   - Output: Fully implemented feature with comprehensive unit tests

**Note**: This sequence covers implementation through unit testing. Integration testing and deployment are separate concerns handled by additional workflows.

### E2E Test Debugging (Systematic Failure Resolution)

For debugging failing E2E tests with a systematic, evidence-based approach:

1. **[Debug E2E Review](.windsurf/workflows/debug-e2e-review.md)** → Classify failures and gather evidence
   - Input: Test failure information (terminal output or test-results folder)
   - Process: For each failing test, classify as setup failure or test execution failure
   - Output: Debugging session document with classified failures and evidence
   
2. **[Debug E2E Hypothesis](.windsurf/workflows/debug-e2e-hypothesis.md)** → Form root cause hypotheses
   - Input: Classified failures with evidence
   - Process: 
     - Path A: Setup failures → Infrastructure/environment analysis
     - Path B: Test execution failures → Application/test logic analysis
     - Prioritize hypotheses (setup failures always first)
   - Output: Prioritized hypothesis list with validation results

3. **[Debug E2E Fix](.windsurf/workflows/debug-e2e-fix.md)** → Apply TDD-style fixes
   - Input: Validated hypothesis
   - Process: For each hypothesis (highest priority first):
     - Think: Plan the fix
     - Red: Create/verify failing test
     - Green: Implement minimal fix
     - Refactor: Clean up code
     - Verify: Run E2E tests
   - Output: Fixed tests with no regressions
   - **Critical**: After fixing setup failures, re-run tests before fixing test execution failures

4. **Final Verification** → Confirm all tests passing
   - Input: All fixes applied
   - Output: Full E2E suite passing, ready to commit

**Key Concepts:**
- **Two failure types**: Setup failures (infrastructure) vs Test execution failures (application/test logic)
- **Priority system**: Always fix setup failures first (Priority 0), then test failures (Priority 1+)
- **Re-run gate**: Must re-run tests after fixing setup failures to get clean results
- **TDD discipline**: Think → Red → Green → Refactor → Verify for all fixes

**See**: [E2E Debugging Workflow Guide](docs/e2e-debugging-workflow-guide.md) for complete documentation

## Repository Structure

```
.windsurf/
├── rules/          # Coding standards and AI interaction patterns
├── workflows/      # Step-by-step process definitions
├── skills/         # Specialized capabilities and knowledge
├── scripts/        # Hook scripts for automated verification and auditing
└── hooks.json      # Hook configuration for Cascade events
```

## Key Components

### Rules

Rules define how the AI assistant should behave and what standards to follow. They can be assigned to a type of file or manually activated. 

I often use manually activated rules for 'Persona's like:

- **active-partner.md**: Interactive questioning pattern for unclear requirements ([source](https://lexler.github.io/augmented-coding-patterns/patterns/active-partner/))
- **design-buddy.md**: Design thinking and architectural guidance (custom persona)
- **security-buddy.md**: Security-focused review persona (example for creating custom personas)

### Workflows

Workflows provide structured processes for common development tasks:

**Development Workflows:**
- **[explore-codebase](.windsurf/workflows/explore-codebase.md)**: Generate documentation for existing projects
- **[analyze-user-story](.windsurf/workflows/analyze-user-story.md)**: Deep analysis of user stories
- **[planning](.windsurf/workflows/planning.md)**: Generate implementation plans
- **[tdd-workflow](.windsurf/workflows/tdd-workflow.md)**: Test-driven development iteration

**E2E Debugging Workflows:**
- **[debug-e2e-workflow](.windsurf/workflows/debug-e2e-workflow.md)**: Complete E2E test debugging workflow (composite orchestrator)
- **[debug-e2e-review](.windsurf/workflows/debug-e2e-review.md)**: Review test failures and classify failure types
- **[debug-e2e-hypothesis](.windsurf/workflows/debug-e2e-hypothesis.md)**: Form and validate root cause hypotheses
- **[debug-e2e-fix](.windsurf/workflows/debug-e2e-fix.md)**: Apply TDD-style fixes to validated hypotheses

### Skills

Skills provide specialized knowledge and capabilities:

**E2E Testing Skills:**
- **[e2e-logging-and-artifacts](.windsurf/skills/e2e-logging-and-artifacts/)**: Set up comprehensive logging infrastructure for Playwright E2E tests
- **[running-e2e-tests](.windsurf/skills/running-e2e-tests/)**: Execute E2E tests with proper commands and patterns

### Hooks

Hooks are automatically executed scripts triggered by events in the Cascade interaction stream, providing continuous verification and conversation auditing:

- **[Hooks Overview](docs/hooks-overview.md)**: Complete guide to the hooks system
- **[Conversation Audit Hook](docs/conversation-audit-hook.md)**: Capture and analyze AI conversations for continuous improvement

**Key capabilities:**
- **Secret detection** - Prevent accidental commits of API keys and credentials
- **Incremental verification** - Fast checks after code edits
- **Command gating** - Block dangerous operations like `git push` until verification passes
- **Conversation auditing** - Capture full conversation history for retrospective analysis and prompt evaluation

The conversation audit hook is particularly valuable for building a feedback loop: review past conversations to identify successful patterns, refine prompts and workflows, and continuously improve your AI-assisted development practices.

## Acknowledgments

This ecosystem builds upon the excellent work of the AI-assisted development community:

### Primary Contributors

**[Devlin Liles](https://www.linkedin.com/in/devlinliles/)** and the Improvers community have been instrumental in refining these workflows:

- **TDD Workflow**: Entirely credited to Devlin Liles, with minimal adaptations needed
- **Analyze User Story**: Based on Devlin's workflow, adapted to match my existing prompt patterns
- **Planning**: Borrowed from Devlin's work, customized for my workspace needs
- **Hooks**: Initial validation checks, and common shell script for continual automated verification. 

### Pattern Sources

- **Active Partner**: Directly from [Augmented Coding Patterns](https://lexler.github.io/augmented-coding-patterns/patterns/active-partner/)

### Personal Contributions

My additions to this ecosystem include:

- **Coding Standards Capture**: Translating team/personal coding standards into AI-consumable rules
- **Design Buddy**: Custom persona developed using Active Partner to capture my design approach ([blog post](https://daniel.scheufler.tech/blog/design-buddy-for-better-code/))
- **Security Buddy**: Example persona demonstrating how to create specialized AI interaction modes
- **Workflow Adaptations**: Customizing community workflows to match my development style
- **Conversation Audit Hook**: Expanded on the initial validation checks to create a comprehensive conversation auditing system, allowing for prompt evaluation on past conversations. 
- **E2E Logging Artifacts Skill**: Created a skill to automatically log E2E test artifacts (screenshots, videos, console and network logs) to a centralized directory for easy access and analysis.
- **E2E Debugging Workflow**: Created a comprehensive workflow for debugging E2E test failures, including infrastructure checks, hypothesis-based application debugging, and re-run verification.

## Getting Started

1. **Fork this repository** to create your own development ecosystem
2. **Review and customize rules** in `.windsurf/rules/` to match your coding standards
3. **Explore workflows** in `.windsurf/workflows/` to understand available processes
4. **Try a workflow sequence** based on your current project phase (brownfield/greenfield/feature development)

## Additional Guides

### E2E Test Debugging

For comprehensive guidance on the E2E debugging workflow system, see the [E2E Debugging Workflow Guide](docs/e2e-debugging-workflow-guide.md). This guide explains:

- **What the workflow is**: A systematic, evidence-based approach to debugging E2E test failures
- **Why it exists**: Solves the complexity of distinguishing infrastructure issues from application bugs
- **Core concepts**: Two failure types, re-run gate, priority system, TDD discipline
- **How workflows and skills interact**: Complete integration map
- **Common patterns**: Real-world debugging scenarios and solutions

### Creating Your Own Personas

Want to create specialized AI interaction modes like Security Buddy? See the [Creating Personas Guide](docs/creating-personas.md) for a step-by-step conversational approach to developing custom personas using the Active Partner pattern.

## License

See LICENSE file for details.
