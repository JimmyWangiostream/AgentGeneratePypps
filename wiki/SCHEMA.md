# Wiki Schema - UFS Pattern Wiki

Based on LLM Wiki pattern with integrated conflict resolution.

## Knowledge Sources (6 integrated)

1. **Spec/** - UFS specification baseline (raw, immutable)
2. **CustomerReq/** - Customer requirements (raw, immutable)
3. **UserPrompt/** - Test engineer guidance (raw, immutable)
4. **Script/** - Pattern code examples (raw, immutable)
5. **ProNoun/** - Terminology definitions (raw, immutable)
6. **ModelDefault/** - Auto-generated defaults (raw, immutable)

## Conflict Resolution Rules

**Rule 1: Spec vs CustomerReq**
- When: Both define same parameter differently
- Result: CustomerReq wins, Spec deleted
- Logged: conflicts.md

**Rule 2: UserPrompt vs ModelDefault**
- When: Both define same parameter differently
- Result: UserPrompt wins, ModelDefault deleted
- Logged: conflicts.md

**All Others: Keep Both**
- When: Any other conflict (e.g., Spec vs Script)
- Result: Both values kept, logged in conflicts.md
- Examples: Spec vs Script, Script vs ModelDefault, etc.

## Wiki Structure

- entities/ - Specific things (devices, components)
- concepts/ - Ideas and methods
- sources/ - Per-source summaries
- synthesis/ - Analysis and comparisons
- Spec/ - UFS spec files
- CustomerReq/ - Customer requirement files
- UserPrompt/ - Test guidance files
- Script/ - Pattern code files
- ProNoun/ - Terminology files
- ModelDefault/ - Default value files

## Three Operations

**Ingest** - New source arrives, integrate with conflict detection
**Query** - Ask question, synthesize from wiki
**Lint** - Health check for structure and semantic issues

---

Status: Ready for first ingest
Created: 2026-06-21
