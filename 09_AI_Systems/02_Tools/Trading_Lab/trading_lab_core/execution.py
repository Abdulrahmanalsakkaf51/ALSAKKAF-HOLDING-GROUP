# -*- coding: utf-8 -*-
"""Causal execution, accounting, metadata, terminal state, and outcomes."""
import copy
import re

from .canonical import (
    AllocationSafetyError,
    NumericSafetyError,
    ReproducibilityError,
    _CanonicalStreamingError,
    _canonical_sha256_with_issues,
    _checked_accumulate,
    _checked_add,
    _checked_cash_add,
    _checked_cash_subtract,
    _checked_divide,
    _checked_effective_add,
    _checked_effective_subtract,
    _checked_multiply,
    _checked_result,
    _checked_subtract,
    _engine_source_snapshot,
    _safe_for_hash,
    _streaming_canonical_sha256,
    canonical_sha256,
)
from .constants import (
    ACCOUNTING_UNIT,
    BLOCKED_DRAWDOWN_HALT,
    BLOCKED_INCREASE_TO_LOSER,
    BLOCKED_INVALID_INPUT,
    BLOCKED_INVALID_STRATEGY_PARAMETERS,
    BLOCKED_POSITION_LIMIT,
    BLOCKED_REPRODUCIBILITY_ERROR,
    BLOCKED_RISK_OVERRIDE_ATTEMPT,
    CHECKPOINT_ID,
    COMMISSION_RATE,
    COMMITTED_BASE_REVISION,
    COMPLETED_TRADE_HISTORY,
    DISCLAIMER,
    ENGINE_NAME,
    ENGINE_SOURCE_DIGEST_ALGORITHM,
    ENGINE_SOURCE_NORMALIZATION,
    ENGINE_VERSION,
    ENTRY_HYPOTHETICALLY_FILLED,
    ENTRY_SIGNAL_SCHEDULED,
    EXIT_HYPOTHETICALLY_FILLED,
    EXIT_SIGNAL_SCHEDULED,
    NO_FILL_END_OF_DATA,
    NO_TRADE_ALREADY_POSITIONED,
    NO_TRADE_INSUFFICIENT_HISTORY,
    NO_TRADE_NO_CROSS,
    NO_TRADE_NO_OPEN_POSITION,
    OPEN_TERMINAL_POSITION,
    OUTCOME_BLOCKED,
    OUTCOME_FILL,
    OUTCOME_HALT,
    OUTCOME_NO_FILL,
    OUTCOME_NO_TRADE,
    OUTCOME_SIGNAL,
    OUTPUT_SCHEMA_VERSION,
    PERFORMANCE_DISCLAIMER,
    PROJECT_ID,
    PUBLIC_SCHEMA_TYPE_POLICY,
    RELEASE_ID,
    SLIPPAGE_RATE,
    STARTING_CASH,
    STRATEGY_STATUS,
)
from .risk import (
    _effective_policy,
    _system_risk_limits,
    check_entry_allowed,
    drawdown_halt_triggered,
)
from .strategy import _safe_raw_strategy_identity, _sma_cross_signals_from_series, sma
from .validation import validate_market_pack, validate_strategy

def _assumptions():
    return {
        "starting_cash": STARTING_CASH,
        "accounting_unit": ACCOUNTING_UNIT,
        "commission_bps_per_fill": 5.0,
        "commission_rate": COMMISSION_RATE,
        "slippage_bps_per_fill": 5.0,
        "slippage_rate": SLIPPAGE_RATE,
        "buy_fill_rule": "NEXT_BAR_OPEN_MULTIPLIED_BY_1.0005",
        "sell_fill_rule": "NEXT_BAR_OPEN_MULTIPLIED_BY_0.9995",
        "separate_spread_bps": 0.0,
        "minimum_fee": 0.0,
        "taxes_financing_borrow_venue_fees": 0.0,
        "market_impact_model": "NONE_BEYOND_FIXED_SLIPPAGE",
        "partial_fills": False,
        "signal_information_cutoff": "BAR_CLOSE_T",
        "execution_bar": "NEXT_VALIDATED_BAR",
        "reference_price": "NEXT_BAR_OPEN",
        "terminal_position_policy": "MARK_TO_MARKET_OPEN",
        "numeric_rounding_policy": "NO_INTERMEDIATE_ROUNDING; DISPLAY_ONLY",
        "timezone_convention": "ISO_INPUT_NORMALIZED_TO_UTC_FOR_VALIDATION",
    }

def _metadata(historical_pack, strategy, input_hash, strategy_hash, policy,
              engine_source_digest=None, raw_strategy_identity=None,
              engine_source_manifest=None):
    if engine_source_digest is None or engine_source_manifest is None:
        captured_digest, captured_manifest = _engine_source_snapshot()
        if engine_source_digest is None:
            engine_source_digest = captured_digest
        if engine_source_manifest is None:
            engine_source_manifest = captured_manifest
    if (type(engine_source_digest) is not str
            or re.fullmatch(r"[0-9a-f]{64}", engine_source_digest) is None):
        raise ReproducibilityError(
            "engine source digest must be lowercase SHA-256 text"
        )
    instrument = None
    if (type(historical_pack) is dict
            and type(historical_pack.get("instruments")) is list
            and len(historical_pack["instruments"]) == 1
            and type(historical_pack["instruments"][0]) is dict):
        instrument = historical_pack["instruments"][0]
    candidate_dates = instrument.get("ohlcv", []) if instrument else []
    dates = candidate_dates if type(candidate_dates) is list else []
    first_date = dates[0].get("date") if dates and type(dates[0]) is dict else None
    last_date = dates[-1].get("date") if dates and type(dates[-1]) is dict else None
    identity = strategy if type(strategy) is dict else raw_strategy_identity
    material = {
        "input_hash": input_hash,
        "strategy_hash": strategy_hash,
        "engine_version": ENGINE_VERSION,
        "engine_checkpoint": CHECKPOINT_ID,
        "engine_source_digest": engine_source_digest,
    }
    return {
        "run_id": "TRL-RUN-" + canonical_sha256(material)[:20].upper(),
        "project_id": PROJECT_ID,
        "release_id": RELEASE_ID,
        "checkpoint_id": CHECKPOINT_ID,
        "engine": {
            "name": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "checkpoint_id": CHECKPOINT_ID,
            "digest_algorithm": ENGINE_SOURCE_DIGEST_ALGORITHM,
            "source_normalization": ENGINE_SOURCE_NORMALIZATION,
            "engine_source_digest": engine_source_digest,
            "engine_source_manifest": copy.deepcopy(engine_source_manifest),
            "committed_base_revision": COMMITTED_BASE_REVISION,
        },
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "public_schema_type_policy": PUBLIC_SCHEMA_TYPE_POLICY,
        "strategy_id": (_safe_for_hash(identity.get("strategy_id"))
                        if type(identity) is dict else None),
        "strategy_name": (_safe_for_hash(strategy.get(
            "name", "SMA Close Crossing Long-Only Research Rule"))
            if type(strategy) is dict else None),
        "strategy_version": (_safe_for_hash(strategy.get("strategy_version"))
                             if type(strategy) is dict else
                             _safe_for_hash(identity.get("strategy_version"))
                             if type(identity) is dict else None),
        "strategy_status": STRATEGY_STATUS,
        "strategy_author": (_safe_for_hash(strategy.get(
            "author", "ALSAKKAF Trading Research Lab"))
            if type(strategy) is dict else None),
        "strategy_review_status": (
            _safe_for_hash(strategy.get("review_status", "NOT_FOUNDER_APPROVED"))
            if type(strategy) is dict else None
        ),
        "strategy_founder_approved": False,
        "strategy_parameters": (_safe_for_hash(strategy)
                                 if type(strategy) is dict else None),
        "strategy_definition_hash": (
            canonical_sha256(strategy) if type(strategy) is dict else None
        ),
        "raw_strategy_identity": (
            _safe_for_hash(raw_strategy_identity)
            if type(raw_strategy_identity) is dict else None
        ),
        "raw_strategy_identity_hash": (
            canonical_sha256(raw_strategy_identity)
            if type(raw_strategy_identity) is dict else None
        ),
        "configuration_hash": strategy_hash,
        "pack_id": (_safe_for_hash(historical_pack.get("pack_id"))
                    if type(historical_pack) is dict else None),
        "data_as_of": (_safe_for_hash(historical_pack.get("as_of"))
                       if type(historical_pack) is dict else None),
        "instrument": {
            "symbol": _safe_for_hash(instrument.get("symbol")),
            "asset_class": _safe_for_hash(instrument.get("asset_class")),
            "data_source": _safe_for_hash(instrument.get("data_source")),
            "data_quality_note": _safe_for_hash(instrument.get("data_quality_note")),
        } if instrument else None,
        "input_data_hash": input_hash,
        "engine_source_digest": engine_source_digest,
        "engine_source_manifest": copy.deepcopy(engine_source_manifest),
        "canonical_serialization": "UTF-8 JSON; SORTED KEYS; COMPACT SEPARATORS; NO NaN/Infinity",
        "effective_system_risk_limits": copy.deepcopy(policy),
        "execution_assumptions": _assumptions(),
        "run_start_timestamp": _safe_for_hash(first_date),
        "run_end_timestamp": _safe_for_hash(last_date),
        "paper_research_only": True,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
    }


def _reproducibility_failure_metadata(historical_pack, input_hash,
                                      strategy_hash, raw_strategy_identity):
    material = {
        "input_hash": input_hash,
        "strategy_hash": strategy_hash,
        "engine_version": ENGINE_VERSION,
        "engine_checkpoint": CHECKPOINT_ID,
        "engine_source_digest": None,
        "reproducibility_status": "FAILED_CLOSED",
    }
    return {
        "run_id": "TRL-RUN-" + canonical_sha256(material)[:20].upper(),
        "project_id": PROJECT_ID,
        "release_id": RELEASE_ID,
        "checkpoint_id": CHECKPOINT_ID,
        "engine": {
            "name": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "checkpoint_id": CHECKPOINT_ID,
            "digest_algorithm": ENGINE_SOURCE_DIGEST_ALGORITHM,
            "source_normalization": ENGINE_SOURCE_NORMALIZATION,
            "engine_source_digest": None,
            "engine_source_manifest": None,
            "committed_base_revision": COMMITTED_BASE_REVISION,
        },
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "public_schema_type_policy": PUBLIC_SCHEMA_TYPE_POLICY,
        "strategy_id": (raw_strategy_identity.get("strategy_id")
                        if type(raw_strategy_identity) is dict else None),
        "strategy_name": None,
        "strategy_version": (raw_strategy_identity.get("strategy_version")
                             if type(raw_strategy_identity) is dict else None),
        "strategy_status": STRATEGY_STATUS,
        "strategy_author": None,
        "strategy_review_status": None,
        "strategy_founder_approved": False,
        "strategy_parameters": None,
        "strategy_definition_hash": None,
        "raw_strategy_identity": _safe_for_hash(raw_strategy_identity),
        "raw_strategy_identity_hash": canonical_sha256(raw_strategy_identity),
        "configuration_hash": strategy_hash,
        "pack_id": (_safe_for_hash(historical_pack.get("pack_id"))
                    if type(historical_pack) is dict else None),
        "data_as_of": (_safe_for_hash(historical_pack.get("as_of"))
                       if type(historical_pack) is dict else None),
        "instrument": None,
        "input_data_hash": input_hash,
        "engine_source_digest": None,
        "engine_source_manifest": None,
        "canonical_serialization": "UTF-8 JSON; SORTED KEYS; COMPACT SEPARATORS; NO NaN/Infinity",
        "effective_system_risk_limits": _system_risk_limits(),
        "execution_assumptions": _assumptions(),
        "run_start_timestamp": None,
        "run_end_timestamp": None,
        "paper_research_only": True,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
        "reproducibility_status": "FAILED_CLOSED",
    }


def _empty_result(metadata, outcome, reason_code, validation_errors=None):
    event = {
        "event_id": "EVT-0001",
        "outcome": outcome,
        "reason_code": reason_code,
        "timestamp": metadata.get("data_as_of"),
        "strategy_id": metadata.get("strategy_id"),
        "context": {},
    }
    return {
        "report_type": "BacktestReport",
        "outcome": outcome,
        "reason_code": reason_code,
        "reason_codes": [reason_code],
        "validation": {
            "outcome": "VALID" if not validation_errors else "INVALID",
            "reason_codes": [] if not validation_errors else [reason_code],
            "errors": validation_errors or [],
        },
        "metadata": metadata,
        "assumptions": metadata["execution_assumptions"],
        "events": [event],
        "decisions": [],
        "hypothetical_fills": [],
        "trade_list": [],
        "equity_curve": [],
        "open_position": None,
        "starting_cash": STARTING_CASH,
        "final_cash": STARTING_CASH,
        "final_equity": STARTING_CASH,
        "realized_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "cumulative_commission": 0.0,
        "cumulative_slippage_cost": 0.0,
        "cumulative_costs": 0.0,
        "max_drawdown_pct": 0.0,
        "halted": outcome == OUTCOME_HALT,
        "assumption_violations": validation_errors or [],
        "disclaimer": DISCLAIMER,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
    }


def _event(events, outcome, reason, timestamp, strategy, context=None):
    events.append({
        "event_id": "EVT-%04d" % (len(events) + 1),
        "outcome": outcome,
        "reason_code": reason,
        "timestamp": timestamp,
        "strategy_id": strategy["strategy_id"],
        "context": context or {},
    })


def _decision(decisions, action, timestamp, status, reason, target_notional=None):
    record = {
        "decision_id": "SIG-%04d" % (len(decisions) + 1),
        "action": action,
        "signal_timestamp": timestamp,
        "information_cutoff": "BAR_CLOSE_T",
        "eligible_fill_rule": "NEXT_VALIDATED_BAR_OPEN",
        "status": status,
        "reason_code": reason,
    }
    if target_notional is not None:
        record["target_gross_notional"] = target_notional
    decisions.append(record)
    return record


def _run_validated(strategy, pack, policy, metadata, initial_last_loss_size_pct=None,
                   _sma_function=None):
    """Internal deterministic state machine; the optional state is a test seam."""
    instrument = pack["instruments"][0]
    bars = instrument["ohlcv"]
    symbol = instrument["symbol"]
    strategy_size = _checked_result(
        strategy["paper_size_pct"], "strategy size conversion",
    )
    closes = [bar["close"] for bar in bars]
    calculate_sma = sma if _sma_function is None else _sma_function
    fast_series = calculate_sma(closes, strategy["fast"])
    slow_series = calculate_sma(closes, strategy["slow"])
    signals = _sma_cross_signals_from_series(bars, fast_series, slow_series)

    cash = _checked_result(STARTING_CASH, "starting cash initialization")
    units = 0.0
    position = None
    realized_pnl = 0.0
    cumulative_commission = 0.0
    cumulative_slippage = 0.0
    peak = STARTING_CASH
    max_drawdown = 0.0
    halted = False
    pending = None
    last_loss_size_pct = copy.deepcopy(initial_last_loss_size_pct or {})
    events = []
    decisions = []
    fills = []
    trades = []
    curve = []

    for index, bar in enumerate(bars):
        timestamp = bar["date"]
        raw_open = _checked_result(bar["open"], "opening price conversion")

        if pending is not None:
            action = pending["action"]
            if action == "enter":
                allowed, block_reason = check_entry_allowed(
                    {symbol: position} if position else {}, last_loss_size_pct,
                    symbol, instrument["asset_class"], strategy["paper_size_pct"],
                    policy,
                )
                if halted:
                    allowed, block_reason = False, BLOCKED_DRAWDOWN_HALT
                if not allowed:
                    pending["decision"]["status"] = "BLOCKED"
                    pending["decision"]["reason_code"] = block_reason
                    _event(events, OUTCOME_BLOCKED, block_reason, timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"]})
                else:
                    try:
                        fill_price = _checked_multiply(
                            raw_open, 1.0 + SLIPPAGE_RATE, "buy slippage",
                        )
                        target_notional = pending["target_notional"]
                        if target_notional <= 0:
                            raise NumericSafetyError(
                                "zero target notional during entry allocation"
                            )
                        units = _checked_divide(
                            target_notional, fill_price, "entry units",
                        )
                        commission = _checked_multiply(
                            target_notional, COMMISSION_RATE, "entry commission",
                        )
                        slippage_delta = _checked_subtract(
                            fill_price, raw_open, "entry slippage delta",
                        )
                        if slippage_delta <= 0:
                            raise NumericSafetyError(
                                "zero slippage cost basis during entry allocation"
                            )
                        slippage_cost = _checked_multiply(
                            units, slippage_delta, "entry slippage cost",
                        )
                        entry_debit = _checked_effective_add(
                            target_notional, commission, "entry cash debit",
                        )
                        next_cash = _checked_cash_subtract(
                            cash, entry_debit, "entry cash",
                        )
                        next_commission = _checked_accumulate(
                            cumulative_commission, commission,
                            "cumulative commission",
                        )
                        next_slippage = _checked_accumulate(
                            cumulative_slippage, slippage_cost,
                            "cumulative slippage",
                        )
                    except NumericSafetyError as error:
                        raise AllocationSafetyError(
                            "entry allocation rejected: %s" % error
                        ) from error
                    cash = next_cash
                    cumulative_commission = next_commission
                    cumulative_slippage = next_slippage
                    position = {
                        "symbol": symbol,
                        "units": units,
                        "requested_position_pct": float(strategy["paper_size_pct"]),
                        "entry_signal_time": pending["signal_timestamp"],
                        "entry_fill_time": timestamp,
                        "raw_opening_price": raw_open,
                        "slipped_fill_price": fill_price,
                        "entry_filled_notional": target_notional,
                        "entry_commission": commission,
                        "entry_slippage_cost": slippage_cost,
                    }
                    fill = {
                        "fill_id": "FILL-%04d" % (len(fills) + 1),
                        "side": "BUY",
                        "signal_timestamp": pending["signal_timestamp"],
                        "fill_timestamp": timestamp,
                        "raw_opening_price": raw_open,
                        "slipped_fill_price": fill_price,
                        "units": units,
                        "filled_notional": target_notional,
                        "commission": commission,
                        "slippage_cost": slippage_cost,
                    }
                    fills.append(fill)
                    pending["decision"]["status"] = "FILLED"
                    pending["decision"]["fill_id"] = fill["fill_id"]
                    _event(events, OUTCOME_FILL, ENTRY_HYPOTHETICALLY_FILLED,
                           timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"],
                            "fill_id": fill["fill_id"]})
            else:
                if position is None:
                    pending["decision"]["status"] = "NO_TRADE"
                    pending["decision"]["reason_code"] = NO_TRADE_NO_OPEN_POSITION
                    _event(events, OUTCOME_NO_TRADE, NO_TRADE_NO_OPEN_POSITION,
                           timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"]})
                else:
                    try:
                        fill_price = _checked_multiply(
                            raw_open, 1.0 - SLIPPAGE_RATE, "sell slippage",
                        )
                        exit_notional = _checked_multiply(
                            units, fill_price, "exit notional",
                        )
                        commission = _checked_multiply(
                            exit_notional, COMMISSION_RATE, "exit commission",
                        )
                        slippage_delta = _checked_subtract(
                            raw_open, fill_price, "exit slippage delta",
                        )
                        if slippage_delta <= 0:
                            raise NumericSafetyError(
                                "zero slippage cost basis during exit allocation"
                            )
                        slippage_cost = _checked_multiply(
                            units, slippage_delta, "exit slippage cost",
                        )
                        exit_credit = _checked_effective_subtract(
                            exit_notional, commission, "exit cash credit",
                        )
                        next_cash = _checked_cash_add(
                            cash, exit_credit, "exit cash",
                        )
                        next_commission = _checked_accumulate(
                            cumulative_commission, commission,
                            "cumulative commission",
                        )
                        next_slippage = _checked_accumulate(
                            cumulative_slippage, slippage_cost,
                            "cumulative slippage",
                        )
                    except NumericSafetyError as error:
                        raise AllocationSafetyError(
                            "exit allocation rejected: %s" % error
                        ) from error
                    cash = next_cash
                    cumulative_commission = next_commission
                    cumulative_slippage = next_slippage
                    try:
                        trade_net = _checked_effective_subtract(
                            exit_credit, position["entry_filled_notional"],
                            "trade net before entry commission",
                        )
                        trade_net = _checked_effective_subtract(
                            trade_net, position["entry_commission"], "trade net",
                        )
                        next_realized_pnl = _checked_effective_add(
                            realized_pnl, trade_net, "realized P&L",
                        )
                    except NumericSafetyError as error:
                        raise AllocationSafetyError(
                            "exit allocation rejected: %s" % error
                        ) from error
                    realized_pnl = next_realized_pnl
                    fill = {
                        "fill_id": "FILL-%04d" % (len(fills) + 1),
                        "side": "SELL",
                        "signal_timestamp": pending["signal_timestamp"],
                        "fill_timestamp": timestamp,
                        "raw_opening_price": raw_open,
                        "slipped_fill_price": fill_price,
                        "units": units,
                        "filled_notional": exit_notional,
                        "commission": commission,
                        "slippage_cost": slippage_cost,
                    }
                    fills.append(fill)
                    trade = {
                        "trade_id": "TRADE-%04d" % (len(trades) + 1),
                        "symbol": symbol,
                        "entry_signal_time": position["entry_signal_time"],
                        "entry_fill_time": position["entry_fill_time"],
                        "exit_signal_time": pending["signal_timestamp"],
                        "exit_fill_time": timestamp,
                        "entry_raw_opening_price": position["raw_opening_price"],
                        "entry_fill_price": position["slipped_fill_price"],
                        "exit_raw_opening_price": raw_open,
                        "exit_fill_price": fill_price,
                        "units": units,
                        "entry_commission": position["entry_commission"],
                        "exit_commission": commission,
                        "gross_pnl": _checked_subtract(
                            exit_notional, position["entry_filled_notional"],
                            "gross P&L",
                        ),
                        "net_realized_pnl": trade_net,
                        "requested_position_pct": position["requested_position_pct"],
                    }
                    trades.append(trade)
                    if trade_net < 0:
                        last_loss_size_pct[symbol] = position["requested_position_pct"]
                    else:
                        last_loss_size_pct.pop(symbol, None)
                    units = 0.0
                    position = None
                    pending["decision"]["status"] = "FILLED"
                    pending["decision"]["fill_id"] = fill["fill_id"]
                    _event(events, OUTCOME_FILL, EXIT_HYPOTHETICALLY_FILLED,
                           timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"],
                            "fill_id": fill["fill_id"]})
            pending = None

        close = _checked_result(bar["close"], "closing price conversion")
        try:
            marked_value = _checked_multiply(units, close, "position value")
            if position is None:
                unrealized_pnl = 0.0
                equity = _checked_add(cash, marked_value, "marked equity")
            else:
                unrealized_pnl = _checked_effective_subtract(
                    marked_value, position["entry_filled_notional"],
                    "unrealized P&L before commission",
                )
                unrealized_pnl = _checked_effective_subtract(
                    unrealized_pnl, position["entry_commission"],
                    "unrealized P&L",
                )
                equity = _checked_effective_add(
                    cash, marked_value, "marked equity",
                )
        except NumericSafetyError as error:
            if position is not None:
                raise AllocationSafetyError(
                    "position accounting rejected: %s" % error
                ) from error
            raise
        peak = max(peak, equity)
        drawdown_amount = _checked_subtract(equity, peak, "drawdown amount")
        drawdown_ratio = _checked_divide(
            drawdown_amount, peak, "drawdown ratio",
        )
        drawdown = _checked_multiply(
            drawdown_ratio, 100.0, "drawdown percentage",
        )
        max_drawdown = min(max_drawdown, drawdown)
        if drawdown_halt_triggered(
                drawdown, policy["drawdown_halt_pct"], halted):
            halted = True
            _event(events, OUTCOME_HALT, BLOCKED_DRAWDOWN_HALT, timestamp,
                   strategy, {"drawdown_pct": drawdown,
                              "halt_threshold_pct": policy["drawdown_halt_pct"]})

        curve.append({
            "accounting_row_id": "ACCT-%06d" % (len(curve) + 1),
            "timestamp": timestamp,
            "cash": cash,
            "position_units": units,
            "position_value": marked_value,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "cumulative_commission": cumulative_commission,
            "cumulative_slippage_cost": cumulative_slippage,
            "cumulative_costs": _checked_add(
                cumulative_commission, cumulative_slippage, "cumulative costs",
            ),
            "total_marked_equity": equity,
            "equity_peak": peak,
            "drawdown_pct": drawdown,
            "close": close,
            "fast_sma": fast_series[index],
            "slow_sma": slow_series[index],
        })

        action = signals[index][1]
        has_next_bar = index + 1 < len(bars)
        if action == "enter":
            if halted:
                _decision(decisions, action, timestamp, "BLOCKED",
                          BLOCKED_DRAWDOWN_HALT)
                _event(events, OUTCOME_BLOCKED, BLOCKED_DRAWDOWN_HALT,
                       timestamp, strategy)
            elif position is not None:
                _decision(decisions, action, timestamp, "NO_TRADE",
                          NO_TRADE_ALREADY_POSITIONED)
                _event(events, OUTCOME_NO_TRADE, NO_TRADE_ALREADY_POSITIONED,
                       timestamp, strategy)
            else:
                allowed, block_reason = check_entry_allowed(
                    {}, last_loss_size_pct, symbol, instrument["asset_class"],
                    strategy["paper_size_pct"], policy,
                )
                try:
                    target_notional = _checked_multiply(
                        equity, strategy_size,
                        "target notional percentage",
                    )
                    target_notional = _checked_divide(
                        target_notional, 100.0, "target notional",
                    )
                    if target_notional <= 0:
                        raise NumericSafetyError(
                            "zero target notional during entry allocation"
                        )
                except NumericSafetyError as error:
                    raise AllocationSafetyError(
                        "entry allocation rejected: %s" % error
                    ) from error
                if not allowed:
                    _decision(decisions, action, timestamp, "BLOCKED", block_reason,
                              target_notional)
                    _event(events, OUTCOME_BLOCKED, block_reason, timestamp,
                           strategy, {"requested_position_pct": strategy["paper_size_pct"]})
                elif not has_next_bar:
                    _decision(decisions, action, timestamp, "NO_FILL",
                              NO_FILL_END_OF_DATA, target_notional)
                    _event(events, OUTCOME_NO_FILL, NO_FILL_END_OF_DATA,
                           timestamp, strategy, {"action": "enter"})
                else:
                    decision = _decision(
                        decisions, action, timestamp, "SCHEDULED",
                        ENTRY_SIGNAL_SCHEDULED, target_notional,
                    )
                    pending = {
                        "action": action,
                        "signal_timestamp": timestamp,
                        "target_notional": target_notional,
                        "decision": decision,
                    }
                    _event(events, OUTCOME_SIGNAL, ENTRY_SIGNAL_SCHEDULED,
                           timestamp, strategy,
                           {"eligible_fill_timestamp": bars[index + 1]["date"]})
        elif action == "exit":
            if position is None:
                _decision(decisions, action, timestamp, "NO_TRADE",
                          NO_TRADE_NO_OPEN_POSITION)
                _event(events, OUTCOME_NO_TRADE, NO_TRADE_NO_OPEN_POSITION,
                       timestamp, strategy)
            elif not has_next_bar:
                _decision(decisions, action, timestamp, "NO_FILL",
                          NO_FILL_END_OF_DATA)
                _event(events, OUTCOME_NO_FILL, NO_FILL_END_OF_DATA,
                       timestamp, strategy, {"action": "exit"})
            else:
                decision = _decision(decisions, action, timestamp, "SCHEDULED",
                                     EXIT_SIGNAL_SCHEDULED)
                pending = {
                    "action": action,
                    "signal_timestamp": timestamp,
                    "decision": decision,
                }
                _event(events, OUTCOME_SIGNAL, EXIT_SIGNAL_SCHEDULED,
                       timestamp, strategy,
                       {"eligible_fill_timestamp": bars[index + 1]["date"]})
        else:
            reason = (NO_TRADE_INSUFFICIENT_HISTORY
                      if index < strategy["slow"] else NO_TRADE_NO_CROSS)
            _event(events, OUTCOME_NO_TRADE, reason, timestamp, strategy)

    open_position = None
    if position is not None:
        open_position = copy.deepcopy(position)
        open_position.update({
            "market_timestamp": bars[-1]["date"],
            "market_close": _checked_result(
                bars[-1]["close"], "terminal closing price conversion",
            ),
            "market_value": curve[-1]["position_value"],
            "unrealized_pnl": curve[-1]["unrealized_pnl"],
            "terminal_status": "OPEN_MARKED_TO_MARKET",
        })

    reason_codes = []
    for item in events:
        if item["reason_code"] not in reason_codes:
            reason_codes.append(item["reason_code"])
    if halted:
        outcome, reason_code = OUTCOME_HALT, BLOCKED_DRAWDOWN_HALT
    elif any(item["outcome"] == OUTCOME_NO_FILL for item in events):
        outcome, reason_code = OUTCOME_NO_FILL, NO_FILL_END_OF_DATA
    elif any(item["reason_code"] == BLOCKED_INCREASE_TO_LOSER for item in events):
        outcome, reason_code = OUTCOME_BLOCKED, BLOCKED_INCREASE_TO_LOSER
    elif fills:
        outcome = OUTCOME_FILL
        reason_code = OPEN_TERMINAL_POSITION if open_position else COMPLETED_TRADE_HISTORY
        if reason_code not in reason_codes:
            reason_codes.append(reason_code)
    elif len(bars) <= strategy["slow"]:
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_INSUFFICIENT_HISTORY
    elif any(item["reason_code"] == NO_TRADE_ALREADY_POSITIONED for item in events):
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_ALREADY_POSITIONED
    elif any(item["reason_code"] == NO_TRADE_NO_OPEN_POSITION for item in events):
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_NO_OPEN_POSITION
    else:
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_NO_CROSS

    final_row = curve[-1]
    violations = [
        item["reason_code"] for item in events
        if item["outcome"] in (OUTCOME_BLOCKED, OUTCOME_HALT, OUTCOME_NO_FILL)
    ]
    return {
        "report_type": "BacktestReport",
        "outcome": outcome,
        "reason_code": reason_code,
        "reason_codes": reason_codes,
        "validation": {"outcome": "VALID", "reason_codes": [], "errors": []},
        "metadata": metadata,
        "assumptions": metadata["execution_assumptions"],
        "events": events,
        "decisions": decisions,
        "hypothetical_fills": fills,
        "trade_list": trades,
        "equity_curve": curve,
        "open_position": open_position,
        "starting_cash": STARTING_CASH,
        "final_cash": cash,
        "final_equity": final_row["total_marked_equity"],
        "realized_pnl": realized_pnl,
        "unrealized_pnl": final_row["unrealized_pnl"],
        "cumulative_commission": cumulative_commission,
        "cumulative_slippage_cost": cumulative_slippage,
        "cumulative_costs": _checked_add(
            cumulative_commission, cumulative_slippage, "final cumulative costs",
        ),
        "max_drawdown_pct": max_drawdown,
        "halted": halted,
        "assumption_violations": violations,
        "disclaimer": DISCLAIMER,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
    }


def run_backtest(strategy_rules, historical_pack, risk_policy=None,
                 _engine_source_digest_function=None,
                 _engine_source_snapshot_function=None,
                 _run_validated_function=None):
    """Validate and evaluate one declarative SMA-001 rule and one instrument."""
    raw_strategy_identity = _safe_raw_strategy_identity(strategy_rules)
    strategy, strategy_errors, position_limit = validate_strategy(strategy_rules)
    data_errors = validate_market_pack(historical_pack)
    policy = None
    policy_errors = []
    if not strategy_errors:
        policy, policy_errors = _effective_policy(risk_policy, strategy)

    if data_errors:
        input_hash, input_hash_issues = _canonical_sha256_with_issues(
            historical_pack
        )
    else:
        input_hash_issues = []
        try:
            input_hash = _streaming_canonical_sha256(historical_pack)
        except _CanonicalStreamingError as error:
            input_hash, input_hash_issues = _canonical_sha256_with_issues(
                historical_pack
            )
            data_errors.append(
                "pack canonical hashing failed closed: %s" % error.error_name
            )

    raw_strategy_material = {
        "strategy": strategy_rules,
        "risk_policy": risk_policy,
        "system_limits": _system_risk_limits(),
        "costs": {"commission_rate": COMMISSION_RATE,
                  "slippage_rate": SLIPPAGE_RATE},
        "execution": "BAR_CLOSE_T_TO_NEXT_VALIDATED_BAR_OPEN",
        "terminal": "MARK_TO_MARKET_OPEN",
        "starting_cash": STARTING_CASH,
    }
    if strategy_errors or policy_errors:
        raw_strategy_hash, strategy_hash_issues = (
            _canonical_sha256_with_issues(raw_strategy_material)
        )
    else:
        strategy_hash_issues = []
        try:
            raw_strategy_hash = _streaming_canonical_sha256(
                raw_strategy_material
            )
        except _CanonicalStreamingError as error:
            raw_strategy_hash, strategy_hash_issues = (
                _canonical_sha256_with_issues(raw_strategy_material)
            )
            strategy_errors.append(
                "strategy canonical hashing failed closed: %s" % error.error_name
            )
    try:
        if _engine_source_snapshot_function is not None:
            engine_source_digest, engine_source_manifest = (
                _engine_source_snapshot_function()
            )
        elif _engine_source_digest_function is not None:
            engine_source_digest = _engine_source_digest_function()
            _captured_digest, engine_source_manifest = _engine_source_snapshot()
        else:
            engine_source_digest, engine_source_manifest = (
                _engine_source_snapshot()
            )
    except ReproducibilityError:
        metadata = _reproducibility_failure_metadata(
            historical_pack, input_hash, raw_strategy_hash, raw_strategy_identity,
        )
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_REPRODUCIBILITY_ERROR,
            ["engine source digest could not be established; execution failed closed"],
        )

    if input_hash_issues:
        data_errors.extend(
            "pack canonicalization rejected: %s" % issue
            for issue in sorted(set(input_hash_issues))
        )
    if strategy_hash_issues:
        strategy_errors.extend(
            "strategy canonicalization rejected: %s" % issue
            for issue in sorted(set(strategy_hash_issues))
        )
    if data_errors:
        metadata_policy = policy if policy is not None else _system_risk_limits()
        metadata = _metadata(
            historical_pack,
            strategy if not strategy_errors else None,
            input_hash,
            raw_strategy_hash,
            metadata_policy,
            engine_source_digest=engine_source_digest,
            engine_source_manifest=engine_source_manifest,
            raw_strategy_identity=(None if not strategy_errors
                                   else raw_strategy_identity),
        )
        return _empty_result(metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_INPUT,
                             data_errors)

    symbol = historical_pack["instruments"][0]["symbol"]
    if not strategy_errors and strategy["symbol"] != symbol:
        strategy_errors.append("strategy symbol does not match instrument symbol")
    base_policy = _system_risk_limits()
    if strategy_errors:
        metadata = _metadata(
            historical_pack, None, input_hash, raw_strategy_hash, base_policy,
            engine_source_digest=engine_source_digest,
            engine_source_manifest=engine_source_manifest,
            raw_strategy_identity=raw_strategy_identity,
        )
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_STRATEGY_PARAMETERS,
            strategy_errors,
        )
    if position_limit:
        metadata_policy = policy if policy is not None else base_policy
        metadata = _metadata(historical_pack, strategy, input_hash,
                             raw_strategy_hash, metadata_policy,
                             engine_source_digest=engine_source_digest,
                             engine_source_manifest=engine_source_manifest)
        return _empty_result(metadata, OUTCOME_BLOCKED, BLOCKED_POSITION_LIMIT,
                             [position_limit])
    if policy_errors:
        metadata = _metadata(historical_pack, strategy, input_hash,
                             raw_strategy_hash, base_policy,
                             engine_source_digest=engine_source_digest,
                             engine_source_manifest=engine_source_manifest)
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_RISK_OVERRIDE_ATTEMPT,
            policy_errors,
        )
    if strategy["paper_size_pct"] > policy["max_position_pct"]:
        metadata = _metadata(historical_pack, strategy, input_hash,
                             raw_strategy_hash, policy,
                             engine_source_digest=engine_source_digest,
                             engine_source_manifest=engine_source_manifest)
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_POSITION_LIMIT,
            ["requested paper_size_pct exceeds the effective stricter limit"],
        )

    strategy_hash = canonical_sha256({
        "strategy": strategy,
        "effective_policy": policy,
        "costs": {"commission_rate": COMMISSION_RATE,
                  "slippage_rate": SLIPPAGE_RATE},
        "execution": "BAR_CLOSE_T_TO_NEXT_VALIDATED_BAR_OPEN",
        "terminal": "MARK_TO_MARKET_OPEN",
        "starting_cash": STARTING_CASH,
    })
    metadata = _metadata(
        historical_pack, strategy, input_hash, strategy_hash, policy,
        engine_source_digest=engine_source_digest,
        engine_source_manifest=engine_source_manifest,
    )
    try:
        validated_function = (
            _run_validated
            if _run_validated_function is None
            else _run_validated_function
        )
        return validated_function(strategy, historical_pack, policy, metadata)
    except AllocationSafetyError as error:
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_STRATEGY_PARAMETERS,
            ["allocation calculation rejected: %s" % error],
        )
    except NumericSafetyError as error:
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_INPUT,
            ["numeric calculation rejected: %s" % error],
        )
