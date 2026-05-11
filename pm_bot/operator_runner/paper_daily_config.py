from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import clean_text, load_json_object, mapping_rows, normalize_path
from pm_bot.trading_core.trade_intent_candidate import (
    DEFAULT_ACTIVE_HYPOTHESES_PATH,
    DEFAULT_MARKET_QUEUE_PATH,
    load_practical_paper_state,
)

PAPER_DAILY_CONFIG_CONTRACT = "pmbot_paper_daily_loop_config.v1"
DEFAULT_PAPER_DAILY_OUTPUT_DIR = Path("pm_bot/operator_runner/artifacts/paper_daily_022")
DEFAULT_PAPER_DAILY_TRADING_CORE_DIR = Path("pm_bot/trading_core/artifacts/paper_daily_022")
DEFAULT_TRACKED_MARKET_IDS = ("563650", "597964", "598936", "691547", "692258", "573656")
DEFAULT_IDEMPOTENCY_MODE = "upsert_by_run_date_market_intent"


class PaperDailyConfigError(ValueError):
    pass


@dataclass(frozen=True)
class PaperDailyLoopConfig:
    run_date: str = field(default_factory=lambda: date.today().isoformat())
    run_id: str = ""
    market_ids: tuple[str, ...] = DEFAULT_TRACKED_MARKET_IDS
    max_markets: int = 6
    output_dir: Path | str = DEFAULT_PAPER_DAILY_OUTPUT_DIR
    previous_ledger_path: Path | str | None = None
    previous_portfolio_path: Path | str | None = None
    allow_network: bool = False
    allow_real_trading: bool = False
    allow_openrouter: bool = False
    allow_polymarket_api: bool = False
    max_total_paper_exposure_usd: float = 1000.0
    max_single_market_paper_exposure_usd: float = 100.0
    idempotency_mode: str = DEFAULT_IDEMPOTENCY_MODE
    dashboard_enabled: bool = True
    write_artifacts: bool = True

    def __post_init__(self) -> None:
        normalized_run_date = clean_text(self.run_date)
        if not normalized_run_date:
            raise PaperDailyConfigError("run_date is required")
        object.__setattr__(self, "run_date", normalized_run_date)
        object.__setattr__(self, "run_id", self.run_id or f"paper-daily-loop-022-{normalized_run_date}")
        object.__setattr__(self, "market_ids", tuple(clean_text(value) for value in self.market_ids if clean_text(value)))
        object.__setattr__(self, "output_dir", Path(self.output_dir))
        if self.previous_ledger_path is not None:
            object.__setattr__(self, "previous_ledger_path", Path(self.previous_ledger_path))
        if self.previous_portfolio_path is not None:
            object.__setattr__(self, "previous_portfolio_path", Path(self.previous_portfolio_path))
        _validate_daily_config(self)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAPER_DAILY_CONFIG_CONTRACT
        value["output_dir"] = normalize_path(self.output_dir)
        value["previous_ledger_path"] = (
            normalize_path(self.previous_ledger_path) if self.previous_ledger_path is not None else None
        )
        value["previous_portfolio_path"] = (
            normalize_path(self.previous_portfolio_path) if self.previous_portfolio_path is not None else None
        )
        value["market_ids"] = list(self.market_ids)
        return value


def _validate_daily_config(config: PaperDailyLoopConfig) -> None:
    errors: list[str] = []
    if config.allow_network:
        errors.append("allow_network must be false for ORCH-PMBOT-TRADING-MVP-022")
    if config.allow_real_trading:
        errors.append("allow_real_trading must be false for all PMBOT paper daily loop runs")
    if config.allow_openrouter:
        errors.append("allow_openrouter must be false for ORCH-PMBOT-TRADING-MVP-022")
    if config.allow_polymarket_api:
        errors.append("allow_polymarket_api must be false for ORCH-PMBOT-TRADING-MVP-022")
    if config.max_markets < 1:
        errors.append("max_markets must be >= 1")
    if config.max_total_paper_exposure_usd < 0:
        errors.append("max_total_paper_exposure_usd must be >= 0")
    if config.max_single_market_paper_exposure_usd < 0:
        errors.append("max_single_market_paper_exposure_usd must be >= 0")
    if config.idempotency_mode != DEFAULT_IDEMPOTENCY_MODE:
        errors.append(f"idempotency_mode must be {DEFAULT_IDEMPOTENCY_MODE}")
    if errors:
        raise PaperDailyConfigError("; ".join(errors))


def load_tracked_market_state(config: PaperDailyLoopConfig) -> dict[str, Any]:
    state = load_practical_paper_state()
    selected_markets = select_tracked_markets(
        state.get("market_queue", {}),
        market_ids=config.market_ids,
        max_markets=config.max_markets,
    )
    selected_ids = {clean_text(row.get("market_id")) for row in selected_markets}
    market_queue = dict(state.get("market_queue", {}))
    market_queue["items"] = selected_markets
    market_queue["tracked_market_count"] = len(selected_markets)

    active_hypotheses = _filter_hypotheses(state.get("active_hypotheses", {}), selected_ids)
    filtered_state = dict(state)
    filtered_state["market_queue"] = market_queue
    filtered_state["active_hypotheses"] = active_hypotheses
    return filtered_state


def select_tracked_markets(
    market_queue: Mapping[str, Any],
    *,
    market_ids: Sequence[str] = DEFAULT_TRACKED_MARKET_IDS,
    max_markets: int = 6,
) -> list[Mapping[str, Any]]:
    requested_ids = [clean_text(value) for value in market_ids if clean_text(value)]
    queue_items = {clean_text(row.get("market_id")): row for row in mapping_rows(market_queue.get("items"))}
    selected = [queue_items[market_id] for market_id in requested_ids if market_id in queue_items]
    if not selected:
        selected = sorted(mapping_rows(market_queue.get("items")), key=lambda row: clean_text(row.get("market_id")))
    return selected[:max_markets]


def load_market_outcome_inputs(markets: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    outcomes = []
    for market in markets:
        path = clean_text(market.get("outcome_record_path"))
        if not path:
            outcomes.append(_unknown_outcome(market, "outcome_record_path_missing"))
            continue
        path_obj = Path(path)
        if not path_obj.exists():
            outcomes.append(_unknown_outcome(market, f"outcome_record_missing:{normalize_path(path_obj)}"))
            continue
        outcome = load_json_object(path_obj, label=f"outcome record {market.get('market_id')}")
        outcome["outcome_record_path"] = normalize_path(path_obj)
        outcomes.append(outcome)
    return outcomes


def attach_outcome_status_to_markets(
    markets: Sequence[Mapping[str, Any]],
    outcome_inputs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    outcomes_by_market = {clean_text(row.get("market_id")): row for row in outcome_inputs}
    enriched = []
    for market in markets:
        row = dict(market)
        outcome = dict(outcomes_by_market.get(clean_text(market.get("market_id")), {}))
        row["outcome"] = outcome
        row["outcome_status"] = clean_text(outcome.get("outcome_status") or "unknown")
        row["feedback_ready"] = False
        enriched.append(row)
    return enriched


def generated_at_for_run_date(run_date: str) -> str:
    return f"{clean_text(run_date)}T00:00:00Z"


def _filter_hypotheses(active_hypotheses: Mapping[str, Any], selected_ids: set[str]) -> dict[str, Any]:
    filtered = dict(active_hypotheses)
    for key in ("active_hypotheses", "active_paper_hypotheses"):
        rows = [row for row in mapping_rows(active_hypotheses.get(key)) if clean_text(row.get("market_id")) in selected_ids]
        if rows:
            filtered[key] = rows
    filtered["active_hypothesis_count"] = len(mapping_rows(filtered.get("active_hypotheses")))
    filtered["unresolved_count"] = len(
        [
            row
            for row in mapping_rows(filtered.get("active_hypotheses"))
            if clean_text(row.get("outcome_status")) == "unresolved"
        ]
    )
    filtered["resolved_count"] = len(
        [
            row
            for row in mapping_rows(filtered.get("active_hypotheses"))
            if clean_text(row.get("outcome_status")) in {"resolved", "void", "ambiguous"}
        ]
    )
    filtered["feedback_pending_count"] = 0
    filtered["next_outcome_checks"] = [
        row
        for row in mapping_rows(active_hypotheses.get("next_outcome_checks"))
        if clean_text(row.get("market_id")) in selected_ids
    ]
    return filtered


def _unknown_outcome(market: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "market_id": clean_text(market.get("market_id")),
        "market_title": clean_text(market.get("market_title")),
        "outcome_status": "unknown",
        "missing_reason": reason,
    }


def local_source_paths() -> dict[str, str]:
    return {
        "market_queue_path": normalize_path(DEFAULT_MARKET_QUEUE_PATH),
        "active_hypotheses_path": normalize_path(DEFAULT_ACTIVE_HYPOTHESES_PATH),
    }
