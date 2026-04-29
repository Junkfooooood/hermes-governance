# Quality Rules

## 1. Quality Standards

Every agent output must be:

| Standard | Definition |
|----------|-----------|
| **Verifiable** | Output can be checked against success criteria without the agent's reasoning |
| **Traceable** | Every decision can be traced to a rule, instruction, or data source |
| **Explicit** | Uncertainty is stated; assumptions are labeled; confidence is indicated |
| **Minimal** | Contains what's needed, nothing more (noise minimization — Law 5) |
| **Correct** | Free of fabricated facts, invented APIs, guessed file paths |

## 2. Code Output Standards

When an executor produces code:
- Must pass existing tests before submission
- Must not degrade test coverage
- Must not introduce security vulnerabilities (OWASP Top 10 awareness)
- Must follow project conventions (linting, formatting, naming)
- Must be reviewable (not a monolithic blob)
- Must include verification that it works (test output, not "should work")

## 3. Analysis Output Standards

When an executor produces analysis:
- Must cite sources (which files were read, which data was used)
- Must separate facts from interpretations
- Must state confidence level for conclusions
- Must note what was NOT analyzed and why
- Must highlight assumptions that could change the conclusion

## 4. Error Reporting Standards

When something fails:
- State WHAT failed (specific operation, not "it didn't work")
- State WHY it failed (root cause, not symptom)
- State WHAT was tried (so the next agent doesn't repeat failures)
- Suggest NEXT STEP (concrete, actionable)

Bad: "The build failed."
Good: "Build failed at `npm run build` with error `Module not found: './auth'`. The file was renamed from `auth.ts` to `authentication.ts` but `index.ts` still imports from `./auth`. Fix: update the import in `src/index.ts:3`."

## 5. Self-Review Checklist

Before returning any output, every agent must self-review:

1. **Completeness**: Did I address everything in the task/success criteria?
2. **Correctness**: Can I verify each factual claim?
3. **Safety**: Did I check for destructive ops, secrets, injection?
4. **Noise**: Can I remove anything without losing meaning?
5. **Format**: Is the output in the expected format?

## 6. Quality Violations

| Violation | Severity | Consequence |
|-----------|----------|-------------|
| Fabricated fact | High | Immediate rejection + audit entry |
| Missing success criterion | Medium | Returned for revision |
| No source citation | Low | Warning + self-review reminder |
| Excessive noise | Low | Context compression trigger |
| Wrong format | Low | Returned for reformatting |

## 7. The "Stop and Fix" Rule

If an agent discovers its own error during self-review, it must:
1. Stop — do not submit incorrect output hoping it won't be noticed
2. Fix — correct the error
3. Re-verify — check that the fix didn't break something else
4. Note — mention the self-correction in the output (transparency, not hiding)
