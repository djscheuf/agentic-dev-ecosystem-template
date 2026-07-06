# User Story Quality Rubric

## Scoring Overview

Each dimension is scored on a **0-3 scale**:
- **0**: Missing or critically deficient
- **1**: Minimal; significant gaps present
- **2**: Adequate; meets baseline requirements
- **3**: Exemplary; complete and well-articulated

---

## Evaluation Dimensions

### 1. **Business Value & Goal Clarity**

**What this measures**: Does the story articulate *why* we're building this, and who benefits?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | Goal is absent, vague, or misaligned to user need | No "So that..." clause; goal is internal/technical only |
| **1** | Goal exists but is generic or unclear; unclear who benefits | "So that we improve performance" without context on user impact |
| **2** | Goal is clear and tied to user/business value; persona identified | "So that support agents can resolve tickets faster" |
| **3** | Goal is specific, measurable, and tied to observable user outcome or business metric | "So that support agents can resolve tickets 30% faster, reducing customer wait time" |

#### Improvement Questions:
- Who is the *customer* of this story?
- What *value* will they receive upon completion?
- How will this change their behavior or outcome?
- Is this value observable or measurable?

---

### 2. **Scope Definition & Vertical Slice**
**What this measures**: Is the story a thin, complete slice that delivers value end-to-end?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | Scope is unbounded or spans multiple systems; unclear what "done" means | Story requires work from multiple teams or affects multiple features |
| **1** | Scope is partially bounded; some layers missing or unclear | Story covers UI and backend but unclear on data persistence or reporting |
| **2** | Scope is clear and bounded; affects multiple layers but in a thin slice | Story adds a new field to a form, persists it, and displays it on a report |
| **3** | Scope is precisely bounded; minimal, complete vertical slice with clear entry/exit points | Story adds a new field to a form, persists it to DB, displays it on report, and includes validation; no other features affected |

#### Improvement Questions:
- Can this story be completed by a single cross-functional team without external dependencies?
- Does it touch all necessary layers (UI, API, persistence, etc.)?
- Is it the *thinnest possible slice* that still delivers user value?
- What is explicitly *out of scope*?

---

### 3. **Acceptance Criteria Quality**

**What this measures**: Are the acceptance criteria testable, complete, and focused on value delivery?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | No acceptance criteria, or criteria are vague/untestable | "System should work well" or "User should be happy" |
| **1** | Criteria exist but are incomplete or mix implementation details with requirements | "Use React" or "Implement caching" without stating what the user can do |
| **2** | Criteria are testable and cover happy path + nearby edge cases; implementation-agnostic | Given-When-Then format used; 3-5 clear criteria |
| **3** | Criteria are precise, testable, and comprehensive; include happy path, edge cases, and business rules; translatable to test cases | Given-When-Then format; each criterion is a distinct test case; covers both positive and negative scenarios |

#### Improvement Questions:
- Can each criterion be answered with a true/false test?
- Do criteria describe *what the user can do*, not *how the system does it*?
- Are edge cases and business rules captured?
- Can these criteria be translated directly into test cases?
- Are there any criteria that are actually implementation details?

#### Trouble Case:
- No Edge Cases are Documented = Incomplete Acceptance Criteria. Suggest adding edge cases, and provide examples of cases to consider. 

---

### 4. **Story Format & Narrative Clarity**

**What this measures**: Is the story well-structured and easy to understand?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | Story lacks structure or is incoherent | No clear narrative; mixed concerns; hard to parse |
| **1** | Story has some structure but is unclear or poorly articulated | Format present but goal/persona/action are muddled or contradictory |
| **2** | Story follows "So that... As a... I want..." format; narrative is clear | All three parts present and coherent; easy to understand intent |
| **3** | Story follows format with precision; narrative is compelling and unambiguous | Format is clean; goal is front-loaded; persona and action are specific and well-chosen |

#### Improvement Questions:
- Does the story follow "So that {Goal} / As a {Persona} / I want to {Action}" format?
- Is the goal (Why) front-loaded and compelling?
- Is the persona specific and relevant?
- Is the desired action concrete and achievable?

---

### 5. **Dependencies & Team Autonomy**

**What this measures**: Can the team complete this story independently, or are there external blockers?

#### Criteria:

| Score | Descriptor | Evidence |
|-------|-----------|----------|
| **0** | Story has unresolved external dependencies or NO identified dependencies; team cannot proceed | Requires API from another team that doesn't exist; requires design from external stakeholder |
| **1** | Story has dependencies that are documented but not resolved | "Waiting for backend team to expose endpoint" |
| **2** | Story has no external dependencies, or dependencies are clearly documented and scheduled | "Depends on Feature X (scheduled for Sprint N)" |
| **3** | Story is fully autonomous; team has all information and resources to complete it | No external dependencies; all prerequisites are met or in-scope |

#### Improvement Questions:
- Does this story require work from individuals outside the team?
- Are all prerequisites in place or scheduled?
- Is the team blocked on any external decision or deliverable?
- Can scope be adjusted to eliminate external dependencies?

#### Trouble Case:
- No Dependencies are Documented = Incomplete Dependencies. Call out lack of identified depdencies, resolved or otherwise. Provide examples of dependencies to consider. 

## Common Gaps & Remediation

### Gap: Vague Business Value
**Symptom**: Goal is generic or internal-focused ("improve performance", "refactor code")
**Fix**: Ask "Who benefits?" and "How will they know it worked?" Tie to observable user outcome or business metric.

### Gap: Unbounded Scope
**Symptom**: Story touches multiple features or requires external team work
**Fix**: Identify the thinnest slice that delivers value. Split into multiple stories if needed. Document dependencies explicitly.

### Gap: Untestable Acceptance Criteria
**Symptom**: Criteria use words like "should", "nice to have", "consider", or describe implementation
**Fix**: Rewrite as Given-When-Then format. Each criterion should be a true/false test.

### Gap: Unclear Persona or Action
**Symptom**: Persona is too broad ("user") or action is vague ("improve", "handle")
**Fix**: Be specific. "Support agent" not "user". "Resolve a ticket in under 2 minutes" not "handle tickets faster".

### Gap: Missing Edge Cases
**Symptom**: Acceptance criteria only cover happy path
**Fix**: Ask "What could go wrong?" and "What are the business rules?" Add criteria for edge cases and error states.