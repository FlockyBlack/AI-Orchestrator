# PMBOT How To Add A New Local Market Packet

This workflow adds a new saved local market packet to PMBOT's practical paper-only flow. It does not fetch live data and does not call OpenRouter, Polymarket APIs, authenticated endpoints, wallets, signing paths, or trading endpoints.

## Fields needed

Create or collect a local packet with:

- `contract_version` or a recognizable local packet shape.
- `market_id`
- `market_title`
- `market_type`
- `rules_summary`
- `resolution_source_summary`
- `current_context_summary`
- `outcomes`
- `source_packets`
- `available_evidence`
- `missing_evidence`
- `known_uncertainties`
- `operator_notes`

Each source packet should include:

- `source_id`
- `source_name`
- `source_type`
- `source_url_or_reference`
- `claim_type`
- `claim_value`
- `evidence_summary`
- `freshness_status`
- `known_limitations`

## Where to put the local packet

Use the existing local manual packet batch area:

- `pm_bot/llm/manual_packet_batch/<market_id>_packet.v1.json`

Do not put secrets, cookies, API keys, browser profiles, wallet files, private keys, or authenticated data in the packet.

## How to normalize it

Use the local packet import module:

```powershell
python -m pm_bot.practical.local_market_packet_import --input pm_bot/llm/manual_packet_batch/<market_id>_packet.v1.json --out-json pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/normalized_input.json --out-md pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/import_summary.md
```

The normalizer preserves missing evidence instead of inventing it.

## How to run analysis

Run local analysis only after normalization:

```powershell
python -m pm_bot.practical.one_market_analysis --input pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/normalized_input.json --out-json pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/analysis.result.json --out-md pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/analysis.md
```

Review the analysis output manually before adding the market to any queue.

## How to add to queue

Follow the existing queue shape from:

- `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json`

Add a new versioned queue artifact in the new task directory. Do not overwrite the 004 queue in place.

Each item should include local paths for:

- normalized input
- analysis result
- analysis markdown
- paper hypothesis id
- unresolved outcome record
- source learning ledger placeholder
- next operator action

## How to create outcome placeholder

Use the existing unresolved outcome style from:

- `pm_bot/practical/artifacts/real_market_batch_004/markets/563650/outcome_record.unresolved.json`

Set outcome status to unresolved. Leave resolution fields empty or null until saved local resolution evidence exists.

## How to track paper hypothesis

Use the paper hypothesis from the analysis result and write a new versioned paper hypothesis artifact:

- `pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/paper_hypothesis.json`
- `pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/paper_hypothesis.md`

The hypothesis is paper-only and non-executable.

## Avoid live fetch unless separately approved

Do not fetch public pages from this workflow. If a future source task needs public evidence, create a separate scoped approval packet and keep that task outside the daily runbook.

## Validation

Run the smallest local checks:

```powershell
python -m json.tool pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/normalized_input.json
python -m json.tool pm_bot/practical/artifacts/<new_task_dir>/markets/<market_id>/analysis.result.json
python -m pm_bot.practical.practical_safety_scan --artifact-dir pm_bot/practical/artifacts/<new_task_dir> --out-json pm_bot/practical/artifacts/<new_task_dir>/safety_scan.result.json --out-md pm_bot/practical/artifacts/<new_task_dir>/safety_scan.md
```

Keep all outputs versioned. Do not overwrite original analysis, evidence, dashboard, or tracking artifacts in place.
