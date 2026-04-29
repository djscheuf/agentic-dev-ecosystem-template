# ADR-002: Software Factory Purpose & Dual Audience

**Date:** 2026-04-29  
**Status:** Accepted

## Decision

This template repository serves a dual audience: humans and AI agents. Its primary service is to humans through documentation and structural examples, with secondary service to AIs through skills, workflows, rules, and other machine-readable artifacts that enable rapid progression from human intent to sound designed, implemented code.

## Rationale

The template's chief value is as a reference and repository of proven structures and patterns that can be gradually refined and improved. By explicitly serving both audiences:

- **Humans** gain a clear template of how to organize a software factory, with documentation explaining the rationale
- **AIs** gain machine-readable skills, workflows, and rules that enable high-level code generation at appropriate token cost
- **Future software factories** can fork this template and inherit both the structural patterns and the operational knowledge

This dual-audience design ensures the template remains useful as a reference while simultaneously enabling AI-driven development workflows.

## Implications

- Documentation should be clear enough for humans to understand and adapt
- Skills, workflows, and rules should be sufficiently detailed for agents to execute without human intervention
- The vault protocol (ADR-001) supports both audiences by providing structured, discoverable knowledge
- Continuous refinement of this template improves all future software factories that inherit from it

## Related Decisions

- [ADR-001: Vault Protocol for Agentic Wiki](ADR-001-vault-protocol-agentic-wiki.md)
- [ADR-003: Skills-Based Architecture with Workflow Coordination](ADR-003-skills-based-architecture.md)
