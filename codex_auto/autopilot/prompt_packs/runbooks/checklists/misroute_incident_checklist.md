# Misroute Incident Checklist

- Stop normal flow immediately.
- Preserve the rendered prompt, preflight report, and wrong-agent output.
- Record which receiver got the prompt and why the mismatch was missed.
- Block any further prompt sending until a human reviews the incident.
- Re-render only after the receiver, scope, and approval path are corrected.
- Stop if anyone proposes runtime mutation, queue mutation, or automatic resend during containment.
