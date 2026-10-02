# Design principles and architectural fit

## Design versus architecture
The difference is **ease of change**.
- **Architecture**: widely applicable, hard to change (for example, choosing CQRS, or a repository pattern used for all data access). Changing it touches everything.
- **Design**: local, easy to change. The contract on an interface, or a class's responsibilities. The blast radius is limited to its users.

Use this to scope concerns. An architectural deviation deserves more scrutiny and a more deliberate conversation than a local design choice. Design matters less than getting the tests right, so do not over-invest review effort on easily changed details.

## Architectural fit
- Is the code in the correct layer or module (UI, API, data)? Is business logic hidden in controllers, or data access in service code?
- Does it respect separation of concerns?
- Is it consistent with patterns already present in the codebase? Does it avoid architectural drift?
- Are layer boundaries crossed through contracts (interfaces, APIs, schemas), not by reaching into internals?
- Are user stories sliced vertically (a working increment), or has the layering dictated horizontal slices?
- Structure mirrors the communication structure of the organization (Conway's Law). When a design crosses team boundaries, ask whether the information flow it implies is realistic.
- Interface changes: is this a revision (compatible) or a version (breaking)? Are consumers accounted for?

## Design by contract
Before code, agree what each component promises: inputs, outputs, and possible results. Review against that contract. Check that the code honors stated preconditions and postconditions, and that contracts are narrow and explicit.

## SOLID checks
Single responsibility:
- One clear reason to change?
- Smells: long if/else chains, many public methods, a class doing several jobs.

Open/closed:
- Can behavior be extended without modifying existing code?
- Are future developers set up to succeed, or forced to hack around limitations?

Liskov substitution:
- Explicit casts to a subtype are a red flag.
- Could any derived class replace its base without breaking expectations? Subtypes must not strengthen preconditions or weaken postconditions.
- Methods throwing "not supported" signal a broken hierarchy.
- Is inheritance used where composition would be clearer?

Interface segregation:
- Does an interface have too many methods or cover more than one area?
- Are implementations forced to implement methods they do not need?
- Is a wide interface injected when only a small part is used? Prefer narrow abstractions of what is actually consumed.

Dependency inversion:
- Depend on abstractions, not concretions.
- Smells: liberal use of `new` instead of injection, declaring concrete types where an abstraction exists, service code connecting directly to a database.

## Coupling and reuse
- Would changing this break unrelated parts of the system?
- Is the logic reusable, or tied to this one context?
- Are abstractions at the right level?

## Rules of thumb
**Rule of 3**: repeated code is not always evil. You do not know the right abstraction until you have about three examples. Do not recommend abstracting after one or two. Do recommend it at the third.

**KISS**: simple algorithms and data structures are easier to reason about and less buggy. Fancy algorithms are slow when n is small, and n is usually small. Do not accept cleverness without evidence it is needed.

**Premature optimization**: is complexity justified by an observed or clearly foreseeable performance need?

**Stage-appropriate design**: a short design effort up front usually pays back, but how much is a judgment about context. Weigh the maturity of the team and the stage of the product. A rule that is best practice in one context (for example microservices for an organization with mature operations) can be harmful in another. Ask when a principle applies, when it does not, and what it commits the team to.

## Review questions
- What design did I expect for this problem, and what did I find? Are the differences justified?
- What are the responsibilities of each new piece? Could I state each in one sentence?
- What assumptions does this make about callers and data?
- If I rewrote this, what would I do differently, and is it worth saying?

## Priorities
- Violations that break layering or create wrong dependencies across the system: `blocking` or `suggestion` depending on scale.
- Local design improvements: `suggestion` or `comment`.
