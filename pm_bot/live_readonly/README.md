# PMBOT Live Read-Only Protocols

This directory contains protocol artifacts for local, manual-first PMBOT read-only work.

LIVE-001 is local and protocol-only. It does not call Polymarket, OpenRouter, browsers, queues, dispatchers, runtime workers, wallets, orders, or any external service.

Future read-only discovery work starts at LIVE-002 and requires explicit network approval in a separate task.

## Market rules/source capture pipeline

SOURCE-008 is protocol-only. It defines a future rules/source capture pipeline but does not fetch data, call APIs, use browser automation, read secrets, or mutate capture templates.

Future network tasks require explicit approval in their own task. Any future fetch is limited to public unauthenticated read-only Polymarket or Gamma metadata for the approved market set.

Fetched metadata can only produce raw artifacts, normalized candidates, and future draft-only capture update plans. Future auto-fill may update only empty or not_started manual capture templates and must keep source_capture_status and capture_status at draft.

An operator must verify the direct Polymarket Rules text before any capture can become ready_for_local_review. There is no trading or execution authority, no queue authority, no runtime authority, no dispatcher authority, and no market action guidance.
