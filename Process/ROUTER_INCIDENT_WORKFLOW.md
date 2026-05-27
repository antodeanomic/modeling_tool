# Router Incident Workflow

## Purpose

When a complex Diagram Viewer router problem appears, the agent must create a routing-analysis artifact before broad code changes. The goal is to keep investigation grounded in an explicit execution model instead of speculative edits.

## Trigger

Use this workflow when any of the following are true:
- the routing defect spans multiple functions or modules
- the visible failure is hard to explain from one local code read
- a previous routing fix regressed another diagram or routing mode
- the agent cannot state a tight local hypothesis after the first investigation pass

## Required Analysis Artifact

Before implementation-heavy changes, create or update a Markdown artifact in `Process/` that contains:
- a sequence diagram showing the routing logic under investigation
- color-coded notes that classify what is known to work, what is partially understood, what is failing, and what remains factual context or a pending probe
- the exact diagram/test/input that exposed the problem
- the controlling code path or functions currently believed to own the behavior
- the next validation step that could falsify the current hypothesis

Preferred starting point:
- start from `Process/ROUTER_INCIDENT_TEMPLATE.md` and fill it in rather than inventing a new structure from scratch

## Required Note Colors

Every router-investigation sequence diagram must include the following note semantics:
- green: confirmed working behavior, invariant, or code path
- orange: partially working behavior, uncertain branch, or competing hypothesis
- red: confirmed failure, regression, contradiction, or missing guardrail
- blue: factual context, assumptions, open questions, or next probe

## Representation Rule

Preserve all four note colors in the investigation packet even when the live Diagram Viewer note renderer does not natively support every color.

Allowed representation:
- preferred: sequence diagram plus companion Markdown notes in the same `Process/` artifact
- also allowed: sequence diagram in CSV plus a Markdown legend that maps each note to green/orange/red/blue status

Not allowed:
- freeform narrative without a routing sequence diagram
- broad code exploration without recording the current routing logic
- skipping the color classification and only describing the issue in prose

## Minimum Investigation Content

The sequence diagram and notes must answer these questions:
1. What input or diagram triggered the routing issue?
2. Which routing stages are confirmed to behave correctly?
3. Where does the failure first become visible?
4. Which branch or decision remains uncertain?
5. What narrow validation will be run next?

## Exit Criteria

The agent may move from analysis artifact to implementation once all are true:
- the routing sequence diagram exists
- green/orange/red/blue notes are present
- the suspected owning code path is named
- one falsifiable next check is recorded

## Scope Note

This is a development-process rule. It does not by itself change Diagram Viewer rendering capabilities or add a new runtime note type.