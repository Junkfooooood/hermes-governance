# Context Noise Diagnostic

## Purpose

This is a self-assessment prompt that any agent can run to measure and reduce context noise. It implements Law 5 (Noise Minimization) enforcement.

## When to Run

- At session start (baseline)
- After 10+ turns (drift check)
- When the agent feels "overwhelmed" or "unfocused"
- When the coordinator requests a noise report

## The Diagnostic Prompt

Copy this prompt and answer each question honestly:

---

### Noise Diagnostic — Self Assessment

**1. Context Composition**
What percentage of your current context is:
- [ ] % Core rules & role definition (essential)
- [ ] % Task-relevant information (needed for this task)
- [ ] % Reference information (may be needed, can be fetched on demand)
- [ ] % Historical context (past turns, past tasks — potentially stale)
- [ ] % Redundant or duplicated content
- [ ] % Low-value filler (greetings, acknowledgments, formatting overhead)

**2. Duplication Check**
List any information that appears more than once in your context:
- [ ] ...
- [ ] ...

**3. Pointer Candidates**
List content that could be replaced with a pointer:
- Content: <description> → Pointer to: <where the content lives>

**4. Staleness Check**
List any information that may be outdated or superseded:
- [ ] ...
- [ ] ...

**5. Noise Ratio**
- Total useful context: ___%
- Total noise (redundant + low-value + stale + can-be-pointer): ___%

**6. Action Items**
Based on the above:
- [ ] Remove duplicates: <which items>
- [ ] Replace with pointers: <which content>
- [ ] Fetch on demand instead: <which reference info>
- [ ] Archive stale items: <which items>
- [ ] Compress verbose content: <which content>

---

## Noise Thresholds

| Noise Ratio | Status | Action |
|-------------|--------|--------|
| 0–15% | Healthy | No action needed |
| 16–30% | Acceptable | Monitor; run diagnostic again in 5 turns |
| 31–50% | Elevated | Active compression required; defer non-essential recalls |
| 51%+ | Critical | Force context compression; escalate to coordinator |

## Auto-Compression Triggers

If noise ratio exceeds 50%, the harness should automatically:
1. Remove all duplicate entries (keep first occurrence)
2. Replace full-text memories with pointers (where pointer exists)
3. Truncate historical turns to last 5
4. Defer non-essential prefetched content (re-fetch on demand)
5. Re-run diagnostic to confirm noise dropped below 30%

## Coordinator Noise Report

When the coordinator requests noise reports from child agents, each agent reports:
```yaml
agent_id: <id>
noise_ratio: <percentage>
top_noise_source: <category>
action_taken: <what was done>
remaining_issues: <what couldn't be resolved>
```
