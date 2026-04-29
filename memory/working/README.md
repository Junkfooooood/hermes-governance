# Working Memory Layer

## Purpose
Ephemeral task state for the current session. This is the shortest-lived layer — it exists only to serve the current reasoning loop.

## What Belongs Here (During Session Only)
- Current task decomposition
- Intermediate variable values
- Tool call results in progress
- Reasoning chain state
- Partial conclusions not yet verified

## What Does NOT Belong Here
- Anything worth keeping after the session ends
- Summarizable insights (→ short_term with summary)
- Validated conclusions (→ long_term)

## Rules

1. **Never persist raw working memory.** It is discarded at session end.
2. **Summarize before promoting.** If something in working memory proves valuable, write a summary to short_term — don't copy raw state.
3. **Keep it lean.** Working memory is in the context window. Every byte here is a byte not available for reasoning.
4. **Clean on task switch.** When the coordinator delegates a new task, clear previous working state.

## Session-End Protocol

At session end, before discarding working memory:
1. Scan for insights worth keeping
2. If found: write a 1-2 sentence summary → short_term with appropriate TTL
3. Discard everything else
4. Record `session_end` in session log

## Anti-Patterns

| Anti-Pattern | Why Wrong | Correct |
|-------------|-----------|---------|
| Copying entire conversation to working memory | Context bloat, no filtering | Summarize only what matters |
| Keeping working memory "just in case" | Noise accumulation | Trust retrieval layers |
| Promoting raw tool output to long_term | Unprocessed data isn't knowledge | Summarize, validate, then promote |
