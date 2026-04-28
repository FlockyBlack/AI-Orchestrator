# Pre-send Checklist

- Confirm the preflight receiver matches the intended agent.
- Confirm preflight result is not blocked, ambiguous, or misrouted.
- Confirm the prompt still matches the approved write scope.
- Confirm manual approval exists for Codex code-changing or repair work.
- Confirm prompt sending remains manual and bounded.
- Stop if preflight returns `MISROUTED_CODEX_PROMPT_DETECTED`.
- Stop if preflight returns `RETURN_ROUTING_MISMATCH`.
- Stop if preflight returns `BLOCK_UNSAFE_OR_APPROVAL_REQUIRED`.
