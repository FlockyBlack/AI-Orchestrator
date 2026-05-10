# PMBOT Public Fetch Replay Before Update Plan

- Replay plan ID: `public-read-only-fetch-prep-005-5-markets.replay_before_update_plan.006`
- Fetch plan ID: `public-read-only-fetch-prep-005-5-markets`
- Request manifest ID: `public-read-only-fetch-prep-005-5-markets.request_manifest.006`
- Evidence save plan ID: `public-read-only-fetch-prep-005-5-markets.evidence_save_plan.006`
- Replay adapter required: `true`
- Source packet mapping required: `true`
- Automatic analysis update allowed: `false`
- Automatic trading allowed: `false`

## Evidence Packet Inputs

- `public_fetch_request_intent_006_01_563650_563650_market_metadata`
  Market: `563650`
  Hypothesis: `563650.analysis.adc53630aa1f.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/563650/public_fetch_request_intent_006_01_563650_563650_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_02_563650_563650_domain_public_evidence`
  Market: `563650`
  Hypothesis: `563650.analysis.adc53630aa1f.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/563650/public_fetch_request_intent_006_02_563650_563650_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_03_597964_597964_market_metadata`
  Market: `597964`
  Hypothesis: `597964.analysis.33643849e5db.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/597964/public_fetch_request_intent_006_03_597964_597964_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_04_597964_597964_domain_public_evidence`
  Market: `597964`
  Hypothesis: `597964.analysis.33643849e5db.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/597964/public_fetch_request_intent_006_04_597964_597964_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_05_598936_598936_market_metadata`
  Market: `598936`
  Hypothesis: `598936.analysis.dceea0f50063.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/598936/public_fetch_request_intent_006_05_598936_598936_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_06_598936_598936_domain_public_evidence`
  Market: `598936`
  Hypothesis: `598936.analysis.dceea0f50063.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/598936/public_fetch_request_intent_006_06_598936_598936_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_07_691547_691547_market_metadata`
  Market: `691547`
  Hypothesis: `691547.analysis.56b3a68b9b94.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/691547/public_fetch_request_intent_006_07_691547_691547_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_08_691547_691547_domain_public_evidence`
  Market: `691547`
  Hypothesis: `691547.analysis.56b3a68b9b94.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/691547/public_fetch_request_intent_006_08_691547_691547_domain_public_evidence.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_09_692258_692258_market_metadata`
  Market: `692258`
  Hypothesis: `692258.analysis.bed289c1494d.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/692258/public_fetch_request_intent_006_09_692258_692258_market_metadata.saved_public_evidence_packet.json`
- `public_fetch_request_intent_006_10_692258_692258_domain_public_evidence`
  Market: `692258`
  Hypothesis: `692258.analysis.bed289c1494d.paper_hypothesis`
  Expected packet: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence/692258/public_fetch_request_intent_006_10_692258_692258_domain_public_evidence.saved_public_evidence_packet.json`

## Required Checks

- Contradiction check: `true`
- Staleness check: `true`
- Operator review after replay: `true`

## Affected Markets

- `563650`
- `597964`
- `598936`
- `691547`
- `692258`

## Safety Boundary

- Saved evidence must be replayed before any PMBOT analysis update.
- Replay does not update analysis automatically.
- Trading remains blocked.
