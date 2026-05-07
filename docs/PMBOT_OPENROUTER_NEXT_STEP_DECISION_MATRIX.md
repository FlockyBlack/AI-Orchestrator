# PMBOT OpenRouter Next Step Decision Matrix

- schema_version: openrouter_next_step_decision_matrix.v1
- task_id: PMBOT-OPENROUTER-053-N5-SURFACE-WORKBENCH-INVENTORY-UX-AND-CONTOUR-AUDIT
- status: next_step_decision_matrix_created
- future_live_calls_approved: false

## Recommended Priority Order

- C. Market inventory/source evidence review
- D. Source/evidence enrichment design
- E. Operator UX/dashboard refinement
- A/B. Repeat N=5 or N=10 readiness protocol after review
- F/G. Model comparison and cost optimization later
- H. Manual operator review lifecycle statuses

## Possible Next Steps

- A. Repeat N=5 controlled batch protocol/live cycle
  purpose: Confirm stability across another same-size controlled batch.
  expected_benefit: Strengthens baseline before larger expansion.
  risk: Consumes live-call budget and repeats current fenced-normalization issue.
  prerequisites: review inventory, review source/evidence audit, fresh readiness protocol
  live_calls_required: true
  recommended_priority: 3
  approved_by_this_task: false
- B. N=10 readiness protocol
  purpose: Design a protocol-only larger batch gate.
  expected_benefit: Surfaces scale constraints before live calls.
  risk: Can create false readiness if inventory/source gaps are not reviewed first.
  prerequisites: inventory review, operator UX review, cost cap design
  live_calls_required: false
  recommended_priority: 3
  approved_by_this_task: false
- C. Market packet category/source inventory refinement
  purpose: Improve local market classification and packet completeness fields.
  expected_benefit: Makes the operator workflow easier to inspect and safer to expand.
  risk: Low risk; local static artifact work only.
  prerequisites: current inventory artifact
  live_calls_required: false
  recommended_priority: 1
  approved_by_this_task: false
- D. Source/evidence enrichment design
  purpose: Define how local packets should capture rules, source gaps, and checklists.
  expected_benefit: Reduces missing-source ambiguity before future LLM review.
  risk: Must remain design/local-artifact work until separately approved.
  prerequisites: inventory review, evidence completeness audit
  live_calls_required: false
  recommended_priority: 1
  approved_by_this_task: false
- E. Workbench UX refinement
  purpose: Improve static operator surfaces and dashboard readability.
  expected_benefit: Reduces artifact spelunking and clarifies status at a glance.
  risk: Low risk if kept static and local.
  prerequisites: dashboard artifact, review pack pointer
  live_calls_required: false
  recommended_priority: 2
  approved_by_this_task: false
- F. Model comparison protocol
  purpose: Design a controlled comparison between analysis-only routes.
  expected_benefit: May improve output format and cost profile.
  risk: Can increase live-call cost if run before protocol approval.
  prerequisites: repeat N=5 or protocol-only design, cost cap
  live_calls_required: false
  recommended_priority: 4
  approved_by_this_task: false
- G. Cost optimization protocol
  purpose: Design lower-cost analysis-only trial constraints.
  expected_benefit: Can reduce per-market cost after quality baseline is stable.
  risk: Premature optimization may obscure source-quality issues.
  prerequisites: stable inventory, baseline review
  live_calls_required: false
  recommended_priority: 4
  approved_by_this_task: false
- H. Manual operator review lifecycle statuses
  purpose: Define local statuses after operator review.
  expected_benefit: Clarifies accepted, blocked, needs-local-enrichment, and archived states.
  risk: Must not mutate queue or runtime state in this task.
  prerequisites: static status vocabulary, runbook review
  live_calls_required: false
  recommended_priority: 2
  approved_by_this_task: false

## Safety Constraints

- future live calls require separate approval
- local inventory and UX work remains static/operator-review-only
- no queue, runtime, wallet, order, or dispatcher authority is granted
