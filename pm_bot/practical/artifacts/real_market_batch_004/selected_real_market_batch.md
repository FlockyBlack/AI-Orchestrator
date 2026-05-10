# PMBOT Real Market Batch 004 Selection

- Selected count: 5
- Rejected candidates: 9
- Live network used: false
- External fetch required: false

## Selection Strategy

Select a bounded set of safe local-only PMBOT packets with concrete title/context, available local source placeholders, no secrets, no live fetch requirement, and enough class diversity to compare analysis quality over time.

## Selected Markets

- `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Class: `generic`
  Packet: `pm_bot/llm/manual_packet_batch/563650_packet.v1.json`
  Reason: Selected for the multi-market batch because it is a safe local-only packet with a concrete title, local rules or context, source placeholders, and no live fetch requirement.
- `597964` Macron out by June 30, 2026?
  Class: `politics`
  Packet: `pm_bot/llm/manual_packet_batch/597964_packet.v1.json`
  Reason: Selected for the multi-market batch because it is a safe local-only packet with a concrete title, local rules or context, source placeholders, and no live fetch requirement.
- `598936` Will the next UK election be called by June 30, 2026?
  Class: `politics`
  Packet: `pm_bot/llm/manual_packet_batch/598936_packet.v1.json`
  Reason: Selected for the multi-market batch because it is a safe local-only packet with a concrete title, local rules or context, source placeholders, and no live fetch requirement.
- `691547` Kraken IPO by December 31, 2026?
  Class: `crypto`
  Packet: `pm_bot/llm/manual_packet_batch/691547_packet.v1.json`
  Reason: Selected for the multi-market batch because it is a safe local-only packet with a concrete title, local rules or context, source placeholders, and no live fetch requirement.
- `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Class: `crypto`
  Packet: `pm_bot/llm/manual_packet_batch/692258_packet.v1.json`
  Reason: Selected for the multi-market batch because it is a safe local-only packet with a concrete title, local rules or context, source placeholders, and no live fetch requirement.

## Limitations

- All selected packets are local saved artifacts; several upstream source artifact paths referenced by packets are absent in this checkout.
- Outcome records are unresolved placeholders until the operator later attaches saved local resolution evidence.
- Source-learning rows are pending and cannot judge usefulness until outcomes are updated.
