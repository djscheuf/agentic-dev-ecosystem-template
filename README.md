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

## Repository Structure

```
.windsurf/
├── rules/          # Coding standards and AI interaction patterns
├── workflows/      # Step-by-step process definitions
└── skills/         # Specialized capabilities and knowledge
```

## Key Components

### Rules

Rules define how the AI assistant should behave and what standards to follow:

- **active-partner.md**: Interactive questioning pattern for unclear requirements ([source](https://lexler.github.io/augmented-coding-patterns/patterns/active-partner/))
- **design-buddy.md**: Design thinking and architectural guidance (custom persona)
- **security-buddy.md**: Security-focused review persona (example for creating custom personas)

### Workflows

Workflows provide structured processes for common development tasks:

- **[explore-codebase](.windsurf/workflows/explore-codebase.md)**: Generate documentation for existing projects
- **[analyze-user-story](.windsurf/workflows/analyze-user-story.md)**: Deep analysis of user stories
- **[planning](.windsurf/workflows/planning.md)**: Generate implementation plans
- **[tdd-workflow](.windsurf/workflows/tdd-workflow.md)**: Test-driven development iteration

## Acknowledgments

This ecosystem builds upon the excellent work of the AI-assisted development community:

### Primary Contributors

**[Devlin Liles](https://www.linkedin.com/in/devlinliles/)** and the Improvers community have been instrumental in refining these workflows:

- **TDD Workflow**: Entirely credited to Devlin Liles, with minimal adaptations needed
- **Analyze User Story**: Based on Devlin's workflow, adapted to match my existing prompt patterns
- **Planning**: Borrowed from Devlin's work, customized for my workspace needs

### Pattern Sources

- **Active Partner**: Directly from [Augmented Coding Patterns](https://lexler.github.io/augmented-coding-patterns/patterns/active-partner/)

### Personal Contributions

My additions to this ecosystem include:

- **Coding Standards Capture**: Translating team/personal coding standards into AI-consumable rules
- **Design Buddy**: Custom persona developed using Active Partner to capture my design approach ([blog post](https://daniel.scheufler.tech/blog/design-buddy-for-better-code/))
- **Security Buddy**: Example persona demonstrating how to create specialized AI interaction modes
- **Workflow Adaptations**: Customizing community workflows to match my development style

## Getting Started

1. **Fork this repository** to create your own development ecosystem
2. **Review and customize rules** in `.windsurf/rules/` to match your coding standards
3. **Explore workflows** in `.windsurf/workflows/` to understand available processes
4. **Try a workflow sequence** based on your current project phase (brownfield/greenfield/feature development)

## Creating Your Own Personas

Want to create specialized AI interaction modes like Security Buddy? See the [Creating Personas Guide](docs/creating-personas.md) for a step-by-step conversational approach to developing custom personas using the Active Partner pattern.

## License

See LICENSE file for details.
