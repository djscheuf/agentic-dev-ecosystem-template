# Software Development Process: Business Case to Deployed Code

**Process Owner**: Development Team Lead  
**Last Updated**: 2026-04-22  
**Status**: Active

---

## Process Overview

This process transforms business value propositions into deployed, working software through systematic breakdown and parallel execution. It emphasizes front-loaded definition of acceptance criteria, data models, and API contracts to enable independent workstreams and reduce integration failures.

**Start Point**: Business Case defining value proposition  
**End Point**: Deployed code with verified acceptance criteria and instrumented value moments

---

## Sessions & Participants

### Session 1: Feature Refinement
**Participants**: Product Owner + Development Team  
**Timing**: Distinct event, happens before story selection  
**Produces**: User Stories with acceptance criteria, dependencies, and workflow steps

### Session 2: Design Session (Story Refinement)
**Participants**: Developer (primary) + QA Engineer + All Team Developers (encouraged)  
**Timing**: Just-in-time after sprint planning, when story selected for development  
**Produces**: Test cases, ADRs, data model updates, API contracts, implementation readiness

---

## Artifacts Index

### Input Artifacts
- [[artifacts/Business Case]]
- [[artifacts/Feature Definition]]
- [[artifacts/User Persona]]
- [[artifacts/Jobs-to-be-Done]]
- [[artifacts/Current System State]]
- [[artifacts/Domain Model]]

### Working Artifacts
- [[artifacts/Acceptance Criteria]]
- [[artifacts/User Story]]
- [[artifacts/Test Case]]
- [[artifacts/User Flow Model]]
- [[artifacts/Layer Responsibilities]]
- [[artifacts/API Contract]]
- [[artifacts/Data Model Update]]
- [[artifacts/Architecture Decision Record]]
- [[artifacts/Implementation Plan]]

### Output Artifacts
- [[artifacts/Deployed Code]]
- [[artifacts/Usage Instrumentation]]
- [[artifacts/Version Release]]

---




# Session 1: Feature Refinement

This is actually an Enrichment step. We start with source material and expand on it. 

Feature comes in as prompt
-> Prompt to Structure
	-> Description
	-> Target Users
	-> Target Value?
	-> 
-> Structure to Expansion
	-> User Personas
	-> Jobs to be Done per Persona?
	-> Value Events (Who, When, What)
	-> Functional Transformations starting from Future State? (Workflow Steps)
	-> Partial AC to Full AC

## [[steps/Derive Acceptance Criteria from Feature]] 


Checks:
- Schema Check
- Has Personas
- Has Transformation Sequence from Current to Future State
	- Starts from Current State
	- Ends with Target State (Matches Feature Intent)
- Each Persona has JTBD(s)?
	- Each JTBD has AC?
		- Has AC of all the types?
		- All AC in GWT Format
		- 


---

This is an expansion step, working from base materials and producing many user story documents.

This step receives the Enriched Feature JSON with the PErsonas, JTBD, and AC already. 

We need to extract all the AC, and then order them based on workflow, and group them by step. Each AC shoiuld know the person and relate to a JTBD. 

Break groups into chunks? (3-7 AC?)
- Id Dependencies between chunks?
- Verify Each Chunk is INVEST
## [[steps/Group Acceptance Criteria into User Stories]]

Checks: 
- Each US passes Schema ccheck
	- Title
	- Description (So that, AS a, I want)
	- AC
- Each US Qual Check
	- Description (So that, as a , I want)
	- AC in GWT
	- AC Has Happy, Error, Edges
- Overall, all Feature AC appear in user story AC ? (Ok for User AC are more)
- 

---

# Interrupt: Develop Existing Refined Story
WHat are the steps presuming we get a user story from outside this evaluation? How do we expand intent, validate format, content, and readiness prior to design?

[[steps/Analyze User Story]]

# Session 2: Design Session (Story Refinement)



## [[steps/Audit Current System State]]

---

## [[steps/Derive Test Cases from Acceptance Criteria]]

---

## [[steps/Model User Flow Through System]]

---

## [[steps/Allocate Responsibilities to Application Layers]]

---

## [[steps/Define Contracts Between Layers]]

---

## [[steps/Capture Design Decisions]]

---

# Implementation Planning

## [[steps/Create Foundations Plan]]

---

## [[steps/Create Layer Implementation Plans]]

---

# Implementation & Deployment

## [[steps/Implement Using TDD Workflow]]

---

## [[steps/Submit for Code Review]]

---

## [[steps/Validate Value Delivery]]

---

# Process Success Factors

1. **Front-loaded definition** (ACs, data models, contracts) enables parallel work
2. **Systematic breakdown** (Feature → Stories → Tests → Tasks) reduces integration failures
3. **Layer responsibility heuristics** maintain clean architecture
4. **TDD workflow** ensures quality at every step
5. **Instrumentation** validates value delivery
6. **Iterative negotiation** ("catch ball") optimizes layer interactions
7. **INVEST criteria** ensures stories are deliverable and valuable

---

# Process Metadata

**Created**: 2026-04-22  
**Method**: Conversational Process Elicitation  
**Source**: Conversational capture in `📥 0-Capture/202604221317 - Process Map - Software Development from Business Case to Deployed Code.md`  
**Scope**: Complete SDLC from business case to production deployment  
**Format**: Structured process definition with wiki-linked artifacts
