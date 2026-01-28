# Creating Your Own Personas

Personas are specialized AI interaction modes that help you work more effectively in specific contexts. This guide shows you how to create custom personas using a conversational approach with the Active Partner pattern.

## What is a Persona?

A persona is a rule file that defines how the AI assistant should behave in a particular role. Examples include:

- **Design Buddy**: Focuses on design thinking and architectural decisions
- **Security Buddy**: Reviews code through a security lens
- **Active Partner**: Asks clarifying questions when requirements are unclear

## The Conversational Approach

The most effective way to create a persona is through conversation with the AI using the Active Partner pattern. Here's the step-by-step process:

### Step 1: Identify the Need

Start by recognizing a gap in your development workflow. Ask yourself:

- What specialized perspective am I missing?
- What type of feedback would help me make better decisions?
- What expertise do I want readily available during development?

**Example**: "I need help evaluating my designs to avoid jumping straight to implementation without considering alternatives."

### Step 2: Engage Active Partner

Invoke the Active Partner rule and describe what you want to create:

```
@active-partner I want to create a persona that helps me think through 
design decisions. I tend to fixate on the first solution that comes to 
mind, and I need something that pushes me to consider alternatives and 
trade-offs before implementing.
```

### Step 3: Answer Clarifying Questions

The Active Partner will ask questions to understand your needs better. Be specific about:

- **Context**: When will you use this persona?
- **Goals**: What outcomes do you want?
- **Style**: How should the persona communicate?
- **Constraints**: What should it avoid or prioritize?

**Example conversation**:
```
AI: What kinds of design decisions are you making? Architecture? 
    Data structures? API design?

You: Mostly class design and API interfaces. I want to make sure 
     I'm thinking about extensibility and maintainability.

AI: Should this persona challenge your assumptions or just provide 
    alternatives?

You: Both. I want it to question whether I'm solving the right 
     problem and suggest alternative approaches.
```

### Step 4: Capture Your Approach

Describe how you naturally think about this domain. The persona should embody your best practices:

- What questions do you ask yourself?
- What principles guide your decisions?
- What mistakes have you learned to avoid?
- What frameworks or mental models do you use?

**Example**:
```
When I'm doing design well, I:
1. Start by understanding the problem deeply before proposing solutions
2. Consider at least 3 different approaches
3. Think about how the design will evolve over time
4. Look for existing patterns before inventing new ones
5. Consider the perspective of future maintainers
```

### Step 5: Refine the Persona

Work with the AI to translate your approach into a concise rule format:

```markdown
---
trigger: manual
---

Challenge Solution Fixation
Ask "What problem are we really solving?" before evaluating solutions
Require at least 2 alternative approaches before choosing one
Question assumptions about requirements
Push back on premature optimization

Evaluate Design Quality
Consider extensibility and maintainability
Look for existing patterns and idioms
Think about the future maintainer's perspective
Identify potential coupling and dependencies

Guide the Design Process
Start with the problem, not the solution
Encourage iterative refinement
Highlight trade-offs explicitly
Recommend simplest viable approach
```

### Step 6: Test and Iterate

Use your new persona in real work:

1. Invoke it during your normal workflow
2. Notice what works and what doesn't
3. Refine the rules based on actual usage
4. Add or remove guidance as needed

## Best Practices

### Keep It Focused

Each persona should have a clear, specific purpose. Don't try to create one persona that does everything.

**Good**: Security Buddy focuses only on security concerns
**Bad**: A persona that tries to handle security, performance, and design all at once

### Make It Actionable

Personas should provide clear, actionable guidance, not vague principles.

**Good**: "Require at least 2 alternative approaches before choosing one"
**Bad**: "Think about design quality"

### Use Your Voice

The persona should reflect how you think and work, not generic advice. Include your specific principles and lessons learned.

### Start Simple

Begin with a minimal persona and expand it as you learn what's useful. It's easier to add guidance than to remove noise.

### Document the Why

Include a brief comment at the top of the persona file explaining its purpose and when to use it.

## Example: Creating Security Buddy

Here's the actual conversation that was used to create the Security Buddy persona, showing the complete process from initial request through refinement to final implementation.

### Initial Request

```
@active-partner Hey, I want to capture a security buddy type persona to help 
me think through especially the cybersecurity and data governance implications 
of a new design as I go through a design. It'll be invoked at about the same 
time the design buddy is once I've done analysis and maybe an initial passive 
planning for the story. And I want this one to, like the design buddy, challenge 
my assumptions and check, hey, here's the implication of that decision for 
future data governance, and to ask me whether that's acceptable or not, and 
then to capture the decision log similar to how design buddy does. I'll hand 
you the design buddy prompt here in just a second as a starting point. What 
kind of things should I add or clarify to make the security buddy better? 

Here's the working design buddy prompt: @design-buddy.md
```

### AI's Initial Recommendations

Based on the design buddy prompt, here are key additions and clarifications for a **Security Buddy** persona:

**1. Threat Modeling Focus**
- STRIDE analysis (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
- Attack surface mapping - what new endpoints, data flows, or integrations are introduced?
- Trust boundaries - where does data cross security zones?

**2. Data Governance Specifics**
- Data classification - PII, PHI, financial, confidential, public?
- Data lifecycle - collection, storage, processing, retention, deletion
- Compliance requirements - GDPR, HIPAA, SOC2, PCI-DSS, etc.
- Data residency - where is data stored and processed geographically?
- Right to erasure - can users delete their data? How?

**3. Security Decision Points**
Challenge on:
- Authentication/Authorization - who can access what and why?
- Encryption - at rest, in transit, key management
- Secrets management - API keys, credentials, tokens
- Input validation - injection risks, sanitization
- Audit logging - what security events need tracking?
- Rate limiting - DoS protection
- Session management - timeouts, token expiry

**4. Risk Assessment Questions**
- "What's the blast radius if this component is compromised?"
- "What sensitive data flows through this layer?"
- "Have you considered the insider threat scenario?"
- "What happens if this third-party service is breached?"
- "How will you detect abuse of this feature?"

**5. Documentation Structure**
```markdown
# Security Review: [Feature Name]

## Data Classification & Flow
[What data types, sensitivity levels, where it moves]

## Trust Boundaries & Attack Surface
[New endpoints, integrations, external dependencies]

## Security Controls
### Authentication & Authorization
### Encryption & Secrets
### Input Validation & Sanitization
### Audit & Monitoring

## Compliance Implications
[GDPR, HIPAA, etc. - what's triggered by this design?]

## Risk Decisions
[What we accepted and why - with mitigation plans]

## Security Test Cases
[Abuse cases, boundary violations, privilege escalation scenarios]
```

**6. Interaction Style Tweaks**
- Flag "security smells" immediately (hardcoded secrets, overly permissive access, etc.)
- Ask "What could go wrong?" for each layer
- Challenge default-allow - push for least privilege
- Question third-party trust - what are we assuming about external services?
- Demand explicit consent - for data collection/processing decisions

**7. Timing Consideration**
Since this runs after initial planning, add:
- "Review the proposed architecture for security gaps"
- "Identify where security wasn't considered in initial design"
- "Flag where convenience may have trumped security"

**8. Decision Log Format**
Capture:
- Risk accepted - what threat/vulnerability and why
- Mitigation applied - what control and coverage
- Deferred - what's punted to future work (with ticket)
- Compliance impact - what regulation triggered what decision

### User's Refinement Response

```
Honestly, I hadn't thought of which threat model analysis we needed to use. 
Let's go ahead and have it do both stride analysis and attack surface mapping, 
because the trust boundaries is a little bit beyond the scope of what this 
application will do. 

As for data governance specifics, yes, we should definitely have some data 
classification for the stories. I expect a lot of those will end up being the 
same across, but better to have it clarified. We definitely want to have data 
lifecycle, because this will likely impact the collection, storage, and 
processing, but may not impact retention yet. For compliance, right now, we're 
not under a ton, but I'd like to go ahead and implement GDPR just in case, 
because I think that's a good starting standard. For data residency, we don't 
need to handle that. That'll be handled by the platform team. And right to 
erasure, right now, the users cannot delete their own data, but that's why I 
want to be able to look at what the GDPR implications are.

So, for security decision points, yes, I want to challenge on authentication 
and authorization. They should be explicit within the story, and if they're 
not, we need to make them so. For encryption, right now, we're not going to 
have encryption in transit. Key management is handled through appropriate other 
management services, but the data at rest, we probably need to look at some 
level of encryption. Right now, we're kind of depending upon our cloud provider 
to handle that. Evidence management is handled appropriately, not in the scope 
of this conversation. Input validations, we definitely want to consider. I have 
not gotten injection risks or sanitization set up, and I want it to start 
catching me on those. For audit logging, yeah, I would like it to propose the 
kind of security events that need tracking, and a good way to do that, as part 
of how I'm capturing telemetry for the existing.

As for the risk assessment questions, I believe the questions that you proposed 
are good. The buddy should make use of those questions in providing its 
evaluation. As for the document structure, yeah, that seems good. We'll use 
that for the first pass and we can deal with any changes as we need over time. 

Yes, it should flag security smells, but those seem to be more about a code 
analysis. We want to be hanging more up at a design layer. So if it sees a 
security smell in the design, yeah, let me know. Yes, it should definitely ask 
what could go wrong for each layer, but I think I would prefer it to ask what 
if such and such happens scenarios rather than just asking me an open-ended 
question like that. And yes, it should challenge default allows, push release 
privilege, abso-frickin-lutely.

Yes, go ahead and review the proposed architecture security gaps. That's 
excellent. Identify where security wasn't considered in the initial design, 
yes. And flag where convenience may have trumped security. I'm a little less 
certain on that one, but that's probably a good idea. And yes, we should 
definitely document risk accepted, mitigated, or deferred, right? So that 
we'll understand. That's fantastic. Good work. Go ahead and help me get that 
first draft.
```

### Final Implementation Summary

The AI created `security-buddy.md` with these key features:

**Threat Analysis:**
- STRIDE framework with all six categories
- Attack surface mapping for endpoints, integrations, and data flows

**Data Governance:**
- Data classification (PII, confidential, public)
- Lifecycle focus on collection, storage, and processing
- GDPR compliance built in

**Security Decision Points:**
- Explicit authentication/authorization requirements
- Encryption at rest considerations
- Input validation and injection protection
- Audit logging with specific event proposals
- Integration with existing telemetry

**Interaction Style:**
- "What if..." scenario-based questions instead of open-ended
- Challenges default-allow and pushes least privilege
- Flags security gaps in design (not code-level smells)
- Reviews architecture for missing security considerations

**Risk Documentation:**
- Accepted, Mitigated, and Deferred categories
- Rationale capture for all security decisions
- GDPR compliance implications tracked

### Key Takeaways from This Example

1. **Start with a reference**: Using the design buddy as a template provided structure
2. **AI proposes comprehensive options**: The AI suggested many security aspects to consider
3. **User refines based on context**: The user clarified what was in/out of scope based on their specific needs
4. **Iterative refinement**: The conversation moved from broad suggestions to specific, actionable guidance
5. **Context matters**: Decisions like "design-level not code-level" and "scenario-based questions" shaped the final persona
6. **Document decisions**: The user explicitly stated preferences (GDPR yes, data residency no) that became part of the persona

## Tips for Success

1. **Use Active Partner**: Let the AI help you articulate your thinking
2. **Be Specific**: Include concrete examples and scenarios
3. **Iterate**: Refine based on real usage
4. **Keep It Short**: Aim for one screen of guidance
5. **Test Early**: Use the persona immediately to validate it works

## Next Steps

Ready to create your own persona? 

1. Identify a gap in your workflow
2. Invoke `@active-partner` 
3. Describe what you want to create
4. Work through the clarifying questions
5. Capture the persona in `.windsurf/rules/your-persona.md`
6. Test it in your actual work
7. Refine based on experience

Remember: The best personas emerge from your real needs and evolve with your practice.
