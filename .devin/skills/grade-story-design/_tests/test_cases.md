# Tests Cases for Design Grader

## Happy Path
Given ANY valid design output
THEN
- Scores on all fields
- All Scores 3 or less.
- All Scores provide reasoning
- Matches Schema

## Design Reasoning Rubric
Given Design Missing Architectural Justification
THEN Design Reasoning Score is 0
AND Reasoning explains missing justification
AND Recommendation suggests grounding decisions in ADRs or existing code patterns

Given Design has Vague, or hueristic-driven Architectural Justification
THEN Design Reasoning Score is 1
AND Reasoning explains vagueness
AND Recommendation suggests strengthening justification with specific patterns

Given Design has over-engineered Architectural Justification
THEN Design Reasoning Score is 1
AND Reasoning explains over-engineering in significant excess of user story scope
AND Recommendation suggests simplifying design to match story scope and RoI. 

Given Design exhibits solid Architectural Justification, with a few unclear design intentions
THEN Design Reasoning Score is 2
AND Reasoning explains mostly solid justification, and highlights some components whose justification is unclear.
AND Recommendation suggests making design intent of all components explicit, and avoiding overlap to tighten scope.

Given Analysis Exemplary Architectural Justification wtih every component exhibiting clear, distinct design intent, grounded in proper justifications, and minimal over-engineering
THEN Design Reasoning Score is 3
AND Reasoning explains exemplary justification
AND no Recommendation needed


## Workflow Changes Rubric

Given Design Missing Workflow Changes such as happy path or edge cases
THEN Workflow Changes Score is 0
AND Reasoning explains missing workflow changes such as missing happy path or edge cases
AND Recommendation suggests specifying user journey step-by-step, including happy and edge paths, as well as data flows.

Given Design has Vague Workflow Changes, such as edge cases with unclear divergence from the happy path
THEN Workflow Changes Score is 1
AND Reasoning explains vagueness of edge cases
AND Recommendation suggests strengthening workflow changes by clarifying and diostinguishing edge cases, and improving clarity of design intent as expressed in the proposed workflow changes

Given Design has Workflow Changes with unclear layer responsibilities
THEN Workflow Changes Score is 1
AND Reasoning explains unclear layer responsibilities, making the location of expected changes unclear, muddling the flow of data
AND Recommendation suggests clarifying workflow change responsibility assignment

Given Design exhibits clear workflow changes, differentiated edge cases, and layer responsibility assignment
THEN Design Reasoning Score is 2
AND Reasoning explains clear Happy path data flows, and differentiated edge cases, and some layer responsibility assignment
AND Recommendation suggests identifying recovery paths for each edge case, and ensuring that all acceptance criteria are mapped.

Given Analysis Exemplary Workflow Changes with an unambiguous happy path, edge cases with clear divergences, and recovery paths, and all acceptance criteria mapped
THEN Workflow Changes Score is 3
AND Reasoning explains exemplary workflow changes
AND no Recommendation needed


## Interface And Contracts Rubric

Given Design Missing Interface And Contracts such as API contracts or component interfaces being absent, or disconnected
THEN Interface And Contracts Score is 0
AND Reasoning explains missing interface and contracts like endpoint definitions, payload shapes or component props 
AND Recommendation suggests specifying API contracts and component interfaces explicitly, including endpoint definitions, payload shapes, and component props.

Given Design has Vague or incomplete Interface And Contracts, interfaces are indicative but not descriptive or complete, such not mapping the whole workflow, or missing error handling. 
THEN Interface and Contracts Score is 1
AND Reasoning explains vagueness incomplete contract definitions
AND Recommendation suggests completing contract definitions with clear endpoint definitions, payload shapes, and component props.

Given Design has partial Interface and Contracts which are missing details for certain workflow steps
THEN Interface and Contracts Score is 1
AND Reasoning explains incomplete workflow mapping
AND Recommendation suggests ensuring that all workflow steps are properly documented with clear interface and contract details.

Given Design exhibits clear interfaces and contracts, but missing error handling or constraints
THEN Interface And Contracts Score is 2
AND Reasoning explains clear interface and contract definitions but missing error handling or value constraints
AND Recommendation suggests adding error handling and constraints to ensure robustness. 

Given Design exhibits clear interfaces and contracts, but whose chain, mapped along the workflow steps exhibits mis-matches in contract shape
THEN Interface And Contracts Score is 2
AND Reasoning explains clear interface and contract definitions but contracts along the workflow do not perfectly map along the workflow
AND Recommendation suggests ensuring that contracts along the workflow are consistent and properly mapped. 

Given Analysis Exemplary Interface and Contracts with an complete contracty definition, 1:1 mappiong between workflow and contracts, with error handling and constrains specified
THEN Interface And Contracts Score is 3
AND Reasoning explains exemplary interface and contract definitions
AND no Recommendation needed

## Layer Responsibilities & Consistency Rubric

Given Design Missing Layer Responsibilities & Consistencyd
THEN Layer Responsibilities & Consistency Score is 0
AND Reasoning explains missing layer responsibilities, explicit boundaries between layers, and clear responsibilities for each layer 
AND Recommendation suggests specifying layer responsibilities explicitly, including explicit boundaries between layers, and clear responsibilities for each layer.

Given Design contradictory Layer Responsibilities & Consistency where existing layer responsibilities are inconsistent or conflicting with proposed design, such as enforcement of AUthorization in the UI layer, lacking explicit design justification
THEN Layer Responsibilities & Consistency Score is 0
AND Reasoning explains contradictory layer responsibilities, without explicit design justification
AND Recommendation suggests reviewing existing layer responsibilities and confirming proposed design with established patterns unless provided explicit justification for responsibility contradiction.

Given Design has incomplete Layer Responsibilities, layer responsibilities are indicative but not descriptive or complete, such exhibiting gaps around which layer owns certain workflow changes
THEN Layer Responsibilities & Consistency Score is 1
AND Reasoning explains incomplete nature of layer responsibility, citing the gap
AND Recommendation suggests completing layer responsibilities & consistency with clear ownership of each layer, explicit boundaries between layers, and clear responsibilities for each layer, and mapping of all workflow changes to exactly one layer for ownership.

Given Design has ambiguous Layer Responsibilities, layer responsibilities exhibiting overlaps around which layers own certain workflow changes
THEN Layer Responsibilities & Consistency Score is 1
AND Reasoning explains ambiguous nature of layer responsibility, citing the overlap
AND Recommendation suggests completing layer responsibilities & consistency with clear ownership of each layer, explicit boundaries between layers, and clear responsibilities for each layer, and mapping of all workflow changes to exactly one layer for ownership.

Given Design exhibits clear layer responsibilities & consistency, but limited reuse of existing components
THEN Layer Responsibilities & Consistency Score is 2
AND Reasoning explains clear layer responsibilities & consistency but limited reuse of existing components 
AND Recommendation suggests reviewing existing components and reusing them where possible to reduce duplication.

Given Design exhibits clear layer responsibilities & consistency, but leaves deviaition from established patterns unexplained.
THEN Layer Responsibilities & Consistency Score is 2
AND Reasoning explains clear layer responsibilities & consistency but unexplained deviation from established patterns
AND Recommendation suggests explaining/clarifying rational for deviation from established patterns.

Given Analysis Exemplary Layer Responsibilities with all workflow responsibilities clearly assigned with explicit rationale, and clear, unambiguous layer responsibility, as well as reuse of existing components and utilities, all deviations justified
THEN Layer Responsibilities & Consistency Score is 3
AND Reasoning explains exemplary layer responsibilities & consistency
AND no Recommendation needed

## Instrumentation & Observability Rubric


