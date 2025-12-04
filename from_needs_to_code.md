# From Needs to Code

*A framework for thinking about software design: the layers of abstraction, the relationships between them, and the iterative process of discovery.*

---

## Part I: The Structure of Software Design

### The Five Layers

Software exists in layers, each more concrete than the last. Understanding these layers—and the relationships between them—is foundational to systematic design.

| Layer | Objects | Nature |
|-------|---------|--------|
| Needs | User goals, desires, problems | Intentional, informal, situated in human context |
| Features | Discrete capability units | Specified behaviors, acceptance-testable |
| Patterns | Structural templates | Meta-level schemas describing how designs are organized |
| Abstractions | Interfaces, contracts, types | Formal specifications of *what*, silent on *how* |
| Implementations | Functions, classes, logic | Concrete, executable, operational |

### The Morphisms Between Layers

The relationships between layers are not uniform. Each connection is a different kind of relationship, and precision about these differences prevents conceptual confusion.

```
    Needs
      ↑
      │ addresses (justificatory: "why does this exist?")
      │
    Features
      ↑
      │ structures (organizational: template application)
      │
    Patterns
      │
      │ prescribes (definitional: what the pattern requires)
      ↓
    Abstractions
      ↑
      │ realizes (implementation: satisfies the contract)
      │
    Implementations
```

| Morphism | Type | Direction | Meaning |
|----------|------|-----------|---------|
| addresses | Justificatory | Feature → Need | Why does this feature exist? |
| structures | Organizational | Pattern → Feature | Template application, schema instantiation |
| prescribes | Definitional | Pattern → Abstraction | What the pattern requires to exist |
| realizes | Implementation | Impl → Abstraction | Satisfies the contract |

Each layer also has internal morphisms: needs *refine* into more specific needs; features *compose* and *depend-on* each other; patterns *specialize* and *combine-with* other patterns; abstractions *extend* and *subtype* one another.

---

## Part II: The Nature of Patterns and Abstractions

### Patterns as Higher-Order Structures

Patterns occupy a peculiar ontological position. They are not things in the way features or implementations are things. You never ship a "Strategy Pattern" to production. Rather, patterns are *schemas*—descriptions of shapes that code can take.

A pattern is not about a single abstraction. It describes *relationships between abstractions*. Consider the Observer pattern:

- There is a Subject role
- There is an Observer role
- There is a relationship: Subject holds references to Observers, notifies them on state change
- There is a protocol: the dynamics of subscription, notification, and unsubscription

The pattern is the *configuration* of all these elements together. This makes patterns **higher-order**: they exist in a space where the objects are themselves abstractions and relationships.

Formally:

```
Pattern = (Roles, Relationships, Protocols)
```

Where *Roles* are abstract participants, *Relationships* are structural connections between them, and *Protocols* are dynamic constraints governing their interaction.

### Abstractions as Boundary Objects

Interfaces and abstractions serve as *boundary objects*—they sit at the threshold between specification and realization. They have two faces:

**Upward-facing (toward patterns):** They fulfill roles. An interface "plays the part of" Observer in a particular instantiation of the Observer pattern.

**Downward-facing (toward implementations):** They constrain implementations. Any concrete class must satisfy the contract.

This dual nature makes abstractions the *mediating layer*—they are both what patterns prescribe and what implementations realize.

### The "Plays-Role-In" Relation

A crucial relationship: how a concrete abstraction in your code relates to the abstract role in a pattern.

```
plays-role-in : Abstraction × Pattern → Role
```

This relationship is *many-to-many*. One interface can play roles in multiple patterns. One role can be fulfilled by different interfaces in different contexts. Recognizing this prevents over-rigid thinking about how abstractions must be designed.

### Patterns as Compressed Design Knowledge

Patterns function as *compression*. They take extensive description—the full graph of abstractions, relationships, and protocols—and compress it into a name plus parameterization.

Saying "we used Strategy here" conveys enormous information to someone who knows the pattern. The pattern name is an *index* into shared design knowledge. This is why patterns exist partially in the social and epistemic realm, not just the formal one. Their utility depends on shared understanding.

---

## Part III: From Feature to Implementation

### Starting Point: The Behavior-Driven Feature

You begin with a feature specification: a description, steps to meet the need, and a test status that starts as failing. The question is: *what's the next move?*

Before decomposing or abstracting, interrogate the feature itself.

**Can a user get partial value if only some steps pass?**
This reveals decomposability into sub-features.

**Are steps coupled or independent?**
This reveals internal cohesion.

**What are the nouns?**
These are candidate entities and abstractions.

**What are the verbs?**
These are candidate operations and interfaces.

**What external systems are touched?**
These define boundaries and potential ports.

**What can vary independently?**
These are axes of change and extension points.

### The Decomposition Decision

Given a feature F with steps S₁, S₂, …, Sₙ:

**If** any step is independently valuable *and* independently testable → **Extract** as sub-feature. Establish dependency. Recurse.

**Else if** the feature is too large to hold in working memory → **Decompose by boundary** (external systems, entities, temporal phases). These become internal structural units, not independent features.

**Else** → Proceed to abstraction discovery.

*"Too large" heuristic:* If you cannot articulate, without notes, what all the steps require to pass, the feature is too large.

### Abstraction Discovery

Now you work with a feature of manageable size. The goal is to discover the abstractions implicit in the specification.

1. **Extract noun phrases** from your steps. These are candidate entities or value objects.

2. **Extract verb phrases** and associate them with nouns. These become candidate method signatures.

3. **Identify what's external** versus internal. External things become ports—abstractions that hide external reality.

4. **Identify what varies** versus what's fixed. Variance suggests an interface; fixedness suggests concrete implementation.

The key question: *what do I want to be able to vary independently?* If report generation might change, that's an interface. If notification channel might change, that's an interface. If the request flow is stable, that can be concrete.

### Pattern Recognition

With candidate abstractions in hand, look for patterns in two directions.

#### Internal Patterns (Within the Feature)

Ask: do the relationships between my candidate abstractions match a known pattern?

**An operation that varies by type or context** → Strategy

**A process with ordered stages** → Pipeline, Chain of Responsibility

**An object built piece by piece** → Builder

**Something that notifies multiple parties** → Observer

**An operation on a recursive structure** → Composite, Visitor

**An external system to insulate from** → Adapter, Port/Adapter

#### External Patterns (Across Features)

Ask: do any of my candidate abstractions already exist or rhyme with existing ones?

For each candidate abstraction, search for:

- **Same concept, same name** → Reuse
- **Same concept, different name** → Reconcile (rename one or extract common parent)
- **Similar concept, same shape** → Generalize (extract shared interface)
- **Similar concept, different shape** → Evaluate whether the difference is accidental or essential

Also ask: will other planned features need similar abstractions? If multiple features need "notification," define the NotificationPort once, correctly, now.

### Interface-First Implementation

Now you have a clear feature, candidate abstractions with signatures, patterns structuring their relationships, and knowledge of existing abstractions to reuse.

**Implementation order:**

1. Define interfaces for ports (external boundaries)
2. Define interfaces for internal variance points
3. Write the feature's test against these interfaces (still fails, but compiles)
4. Implement the concrete classes
5. Wire concretes to interfaces
6. Test passes

This is "outside-in"—define contracts before implementations. The BDD test becomes an integration test; add unit tests for individual implementations as needed.

---

## Part IV: The Iterative Structure

The linear flow presented above is a *first pass*. In practice, development is a system of nested feedback loops, each operating at different timescales.

### The Three Nested Loops

```
┌─────────────────────────────────────────────────────────────────────┐
│  OUTER LOOP: Feature Understanding                                  │
│  Timescale: Days to weeks                                           │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  MIDDLE LOOP: Design/Abstraction Fit                          │  │
│  │  Timescale: Hours to days                                     │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  INNER LOOP: Implementation/Test                        │  │  │
│  │  │  Timescale: Minutes to hours                            │  │  │
│  │  │                                                         │  │  │
│  │  │  Write code → Run test → Observe failure →              │  │  │
│  │  │  Adjust implementation → Repeat                         │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                                                               │  │
│  │  Escalate when: interface friction, duplication, wrongness   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Escalate when: ambiguity, contradiction, underdetermination        │
└─────────────────────────────────────────────────────────────────────┘
```

#### Loop 1: Implementation/Test (Inner)

**Timescale:** Minutes to hours

**Activity:** Writing code to make a test pass

**Trigger to iterate:** Test fails, compiler error, runtime exception

**Resolution:** Change implementation details—algorithm, data structure, control flow

**Escalates when:** You need a method that doesn't exist on an interface, you're fighting the interface's shape, you're duplicating code that shouldn't be duplicated, or the test is awkward to write.

#### Loop 2: Design/Abstraction Fit (Middle)

**Timescale:** Hours to days

**Activity:** Revising interfaces, reconsidering patterns, adjusting abstraction boundaries

**Trigger to iterate:** Signals from inner loop (friction, duplication) or direct observation that abstractions don't compose well

**Resolution:** Add, remove, or modify interfaces; switch patterns; adjust responsibilities

**Escalates when:** You can't write a coherent test because the feature's steps are ambiguous, two obvious designs contradict each other, or the feature seems to require impossible things.

#### Loop 3: Feature Understanding (Outer)

**Timescale:** Days to weeks

**Activity:** Revisiting what the feature means, clarifying with stakeholders, revising acceptance criteria

**Trigger to iterate:** Signals from middle loop (ambiguity, contradiction, underdetermination)

**Resolution:** Clarify steps, add or remove acceptance criteria, decompose or merge features, revise the need itself

### Reading the Signals

The system communicates through specific signals. Learning to read them is a core skill.

| Signal | Observed At | Likely Origin | Response |
|--------|-------------|---------------|----------|
| Compiler error | Inner loop | Wrong impl or interface | Fix impl; if unfixable, revise interface |
| Test failure (logic) | Inner loop | Wrong implementation | Fix implementation |
| Implementation friction | Inner loop | Wrong abstraction shape | Escalate to middle loop |
| Duplication | Inner loop | Missing abstraction | Escalate to middle loop |
| Pattern mismatch | Middle loop | Wrong pattern choice | Reconsider pattern |
| Interface explosion | Middle loop | Over-abstraction | Simplify or re-decompose |
| Ambiguous test | Middle loop | Underspecified feature | Escalate to outer loop |
| Contradictory requirements | Outer loop | Misunderstood need | Clarify or decompose |

### Course Correction: Propagate or Adapt

When you detect friction, you choose between **local adaptation** (work around the problem) or **propagation** (change higher levels to resolve it).

#### When to Adapt Locally

The friction is small. The workaround is contained and doesn't leak. You understand why the friction exists. In these cases, adapt and move on.

#### When to Propagate

The friction is large. The workaround leaks into other areas. You don't understand why the friction exists. In these cases, propagate the change upward.

#### Propagation Directions

**Downward propagation** (abstract → concrete) is straightforward: revise an interface, implementations must follow. The compiler often catches issues.

**Upward propagation** (concrete → abstract) is harder: a discovery at implementation level suggests abstractions are wrong. Identify what's wrong—missing method, wrong signature, wrong responsibility, wrong boundary—then check for ripple effects. Does this change affect the pattern? Do other implementations still make sense? Do consumers need to change?

**Lateral propagation** (across features) occurs when changes to shared abstractions affect other features. This is why shared abstractions are both powerful and dangerous—they create coupling.

### The Three Strikes Rule

A practical heuristic for managing propagation decisions:

**First time** you encounter friction of type X → Note it, adapt locally.

**Second time** → Note it again, adapt locally, mark as suspicious.

**Third time** → Propagate. This is a pattern, not an accident.

This balances responsiveness with stability. You don't thrash on every small signal, but you don't ignore persistent ones either.

### The Healthy Rhythm

Skilled development has a characteristic rhythm:

1. Long stretches in the inner loop (implementation)
2. Occasional bumps to the middle loop (abstraction adjustment)
3. Rare bumps to the outer loop (feature clarification)

Deviations from this rhythm are diagnostic:

**Frequently in outer loop** → Requirements are unstable, or you're starting implementation before understanding.

**Frequently in middle loop** → Complex unfamiliar domain (learning), or over/under-engineering.

**Stuck in inner loop too long** → You may be avoiding a necessary escalation. The friction is a signal; listen to it.

---

## Part V: Essential Questions

At each stage, certain questions cut to the heart of what matters.

### At the Feature Level

**What need does this address?** (Justification)

**How will I know when it's done?** (Acceptance)

**Can it be smaller?** (Decomposition)

### At the Pattern Level

**What forces is this pattern navigating?** (Tradeoffs)

**Does this pattern exist elsewhere in the system?** (Consistency)

**Am I applying this pattern or forcing it?** (Fit)

### At the Abstraction Level

**What role does this play?** (Purpose)

**What does this hide?** (Encapsulation)

**What can vary behind this interface?** (Flexibility)

### At the Implementation Level

**Does this satisfy the contract?** (Correctness)

**Is this the simplest solution that works?** (Simplicity)

**Where is this likely to change?** (Anticipation)

---

## Closing Thought

This framework is not a recipe to follow mechanically. It is a vocabulary for thinking and a set of questions to ask. The goal is not to eliminate judgment but to make judgment more precise—to know what kind of decision you're making and what kind of evidence is relevant to it.

Software design is irreducibly iterative. You will discover things at the implementation level that invalidate design decisions. You will discover ambiguities in features that seemed clear. This is not failure; it is the process working correctly. The discipline is in recognizing the signals, propagating changes when needed, and keeping the layers in sync.
