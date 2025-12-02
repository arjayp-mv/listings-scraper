## ✍️ Code Documentation & Readability Rules (MANDATORY)

Always produce code that another developer can understand and extend within minutes. Enforce the following in every file you create or modify:

1) File Header Block (at top of every file)
- Purpose: one-paragraph overview of what this file is responsible for
- Public API: exported functions/classes and how they’re used
- Dependencies: notable internal/external dependencies
- Change log: brief list of latest changes with date and rationale

2) Function/Class Docstrings
- For every public function/class/method:
  - What it does (single sentence)
  - Parameters with types and constraints
  - Return value with type and edge cases
  - Side effects (I/O, DB changes, network calls)
  - Error behavior (exceptions, error codes)
  - Example usage (short, runnable)

3) Inline Comments Strategy
- Add a comment above any non-trivial logic block explaining the intent, not just the mechanics
- For complex lines (regex, bit ops, query builders, clever algorithms), add a trailing comment or a 1–2 line note above the line
- Before multi-step sequences, include a “Why this order” comment
- For database queries, explain the join/filter/index rationale and expected row counts

4) Section Markers and Navigation
- Use clear region markers to separate sections, e.g.:
  // ===== Validation =====
  // ===== Business Rules =====
  // ===== Data Access =====
- Keep files small (target 200–300 LOC, warn at 400 LOC, split by 500 LOC max)
- At the top, include a mini ToC listing section markers

5) Contract-First Design
- Document the contract before implementing:
  - Inputs, outputs, invariants, pre/post-conditions
  - Error model and retry semantics if applicable
- Validate inputs early; comment on why specific checks exist

6) Tests as Living Docs
- For each public function or endpoint, create or update tests
- Name tests descriptively (reads like behavior specs)
- Add test docstrings explaining scenario and expected outcomes

7) Change Notes in Diffs
- When modifying code, include a “Change Notes” block near the edit describing:
  - What changed
  - Why it changed (link to task/epic if available)
  - Migration or compatibility considerations

8) Cross-References
- For logic that interacts with other modules or DB tables, add comments referencing:
  - Related files/functions
  - Table/column names and constraints
  - Relevant ADR (Architecture Decision Record) IDs

Follow the style of the host language (e.g., JSDoc/TypeDoc, Python docstrings, Go comments, JavaDoc). If a house style exists, conform to it. If not, scaffold it and apply consistently.