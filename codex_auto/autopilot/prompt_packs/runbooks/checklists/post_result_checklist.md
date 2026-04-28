# Post-result Checklist

- Copy back the rendered prompt report, agent output, and operator notes into approved review artifacts only.
- Confirm no runtime, queue, state, result, freeze, or checkpoint surface is updated.
- Confirm Codex output is followed by Flocky read-only validation.
- Confirm any repair request uses a new bounded render request.
- Stop if copied output would be treated as runtime state.
- Stop if Flocky validation after Codex output is skipped.
