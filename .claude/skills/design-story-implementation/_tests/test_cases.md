# Design Story Implementation Test Cases

## Happy Path
- Create design document, matching schema
- Model user flow as sequence of domain events
- Define instrumentation events, using VerbObjectContext naming pattern, events emerge from User flow.
- Assigned Layer Responsibilities, using responsibility heuristics:
    - Front-end: Display, Accessibility, Sequence
    - Backend: Business logic, Security, Performance, Scope, Caching
    - Database: Data storage, Data integrity, Heavy computations
- Define Contracts Between Layers, using responsibility heuristics:
    - Data model first
    - Frontend needs drive backend requirements
    - Backend needs drive data layer requirements
- Identified Archiectural Decisions, document rationale, favoring existing ADRs, and calling out deviations. 
- Document ambiguities, with assumed answers and basis/rationale for each assumption, justifing assumptions with Industry standard practice, or specific ADRs for the repo. 

## Backend Only
- Create design document, matching schema
- Model user flow as sequence of domain events
- Define instrumentation events, using VerbObjectContext naming pattern, events emerge from User flow.
- Assigned Layer Responsibilities, using responsibility heuristics:
    - Front-end: No new responsibilities assigned
    - Backend: new responsibilities assigned
    - Database: new responsibilities assigned
- Define Contracts Between Layers, using responsibility heuristics:
    - Data model first
    - Backend needs drive data layer requirements
    - No Change in Front-end to Backend Contracts
- Identified Archiectural Decisions, document rationale, favoring existing ADRs, and calling out deviations. 
- Document ambiguities, with assumed answers and basis/rationale for each assumption.


## Frontend Only
- Create design document, matching schema
- Model user flow as sequence of domain events
- Define instrumentation events, using VerbObjectContext naming pattern, events emerge from User flow.
- Assigned Layer Responsibilities, using responsibility heuristics:
    - Front-end: New Components, and interactions identified
    - Backend: No new responsibilities assigned
    - Database: No new responsibilities assigned
- Define Contracts Between Layers, using responsibility heuristics:
    - Data model first
    - Backend needs drive data layer requirements
    - No Change in Front-end to Backend Contracts
    - Potential changes in Front-end components and interactions
- Identified Archiectural Decisions, document rationale, favoring existing ADRs, and calling out deviations. 
- Document ambiguities, with assumed answers and basis/rationale for each assumption.