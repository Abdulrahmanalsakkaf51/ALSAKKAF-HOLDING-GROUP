# -*- coding: utf-8 -*-
"""Compatibility facade and CLI for the deterministic paper-only kernel.

ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING -
NO PROFIT CLAIMS. Existing consumers continue to import this module; focused
implementation ownership lives in :mod:`trading_lab_core`.
"""
import json
import os
import sys as _sys


_facade_directory = os.path.dirname(os.path.abspath(__file__))
_sibling_core_directory = os.path.realpath(
    os.path.join(_facade_directory, "trading_lab_core")
)


def _same_real_directory(left, right):
    try:
        return os.path.normcase(os.path.realpath(left)) == os.path.normcase(
            os.path.realpath(right)
        )
    except (OSError, TypeError, ValueError):
        return False


def _module_resolves_from_sibling(module):
    module_file = getattr(module, "__file__", None)
    return (
        isinstance(module_file, str)
        and _same_real_directory(
            os.path.dirname(module_file), _sibling_core_directory,
        )
    )


def _declared_package_resolves_sibling():
    """Return whether relative imports resolve this facade's sibling core."""
    if not isinstance(__package__, str) or not __package__:
        return False
    parent_package = _sys.modules.get(__package__)
    package_paths = getattr(parent_package, "__path__", None)
    if package_paths is None:
        return False
    loaded_core = _sys.modules.get(__package__ + ".trading_lab_core")
    if loaded_core is not None and not _module_resolves_from_sibling(loaded_core):
        return False
    for package_path in package_paths:
        try:
            candidate_directory = os.path.join(
                os.fspath(package_path), "trading_lab_core",
            )
            candidate_module = os.path.join(
                os.fspath(package_path), "trading_lab_core.py",
            )
        except TypeError:
            continue
        if os.path.isfile(candidate_module):
            return False
        if os.path.isfile(os.path.join(candidate_directory, "__init__.py")):
            return _same_real_directory(
                candidate_directory, _sibling_core_directory,
            )
    return False


_use_package_relative_imports = _declared_package_resolves_sibling()

if _use_package_relative_imports:
    from .trading_lab_core import canonical as _canonical
    from .trading_lab_core import constants as _constants
    from .trading_lab_core import execution as _execution
    from .trading_lab_core import reporting as _reporting
    from .trading_lab_core import risk as _risk
    from .trading_lab_core import strategy as _strategy
    from .trading_lab_core import validation as _validation
    from .trading_lab_core.constants import (
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
        DRAWDOWN_HALT_PCT,
        ENGINE_NAME,
        ENGINE_SOURCE_DIGEST_ALGORITHM,
        ENGINE_SOURCE_NORMALIZATION,
        ENGINE_VERSION,
        ENTRY_HYPOTHETICALLY_FILLED,
        ENTRY_SIGNAL_SCHEDULED,
        EXIT_HYPOTHETICALLY_FILLED,
        EXIT_SIGNAL_SCHEDULED,
        MAX_OPEN_POSITIONS,
        MAX_POSITION_PCT,
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
        STRATEGY_FAMILY,
        STRATEGY_ID,
        STRATEGY_STATUS,
        STRATEGY_VERSION,
        SUPPORTED_ASSET_CLASSES,
        _BAR_FIELDS,
        _INSTRUMENT_FIELDS,
        _MAX_CANONICAL_DEPTH,
        _MAX_CANONICAL_INTEGER_BITS,
        _MAX_CANONICAL_NODES,
        _MAX_SAFE_INPUT_MAGNITUDE,
        _MIN_SAFE_PRICE,
        _PACK_ALLOWED,
        _PACK_REQUIRED,
        _SEMVER,
        _STRATEGY_ALLOWED,
        _STRATEGY_REQUIRED,
    )
    from .trading_lab_core.reporting import performance_report_markdown
    for _core_module in (
        _canonical, _constants, _execution, _reporting, _risk, _strategy,
        _validation,
    ):
        if not _module_resolves_from_sibling(_core_module):
            raise ImportError(
                "package-relative trading_lab_core module did not resolve "
                "from the facade sibling directory"
            )
else:
    _original_sys_path = list(_sys.path)
    try:
        _sys.path.insert(0, _facade_directory)
        _loaded_core_package = _sys.modules.get("trading_lab_core")
        if _loaded_core_package is None:
            import trading_lab_core as _loaded_core_package
        _loaded_core_file = getattr(_loaded_core_package, "__file__", None)
        if (
            not isinstance(_loaded_core_file, str)
            or os.path.normcase(os.path.realpath(
                os.path.dirname(_loaded_core_file)
            )) != os.path.normcase(_sibling_core_directory)
        ):
            raise ImportError(
                "trading_lab_core did not resolve from the facade sibling directory"
            )

        from trading_lab_core import canonical as _canonical
        from trading_lab_core import constants as _constants
        from trading_lab_core import execution as _execution
        from trading_lab_core import reporting as _reporting
        from trading_lab_core import risk as _risk
        from trading_lab_core import strategy as _strategy
        from trading_lab_core import validation as _validation
        for _core_module in (
            _canonical, _constants, _execution, _reporting, _risk, _strategy,
            _validation,
        ):
            _core_module_file = getattr(_core_module, "__file__", None)
            if (
                not isinstance(_core_module_file, str)
                or os.path.normcase(os.path.realpath(
                    os.path.dirname(_core_module_file)
                )) != os.path.normcase(_sibling_core_directory)
            ):
                raise ImportError(
                    "trading_lab_core module did not resolve from the facade "
                    "sibling directory"
                )
        from trading_lab_core.constants import (
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
            DRAWDOWN_HALT_PCT,
            ENGINE_NAME,
            ENGINE_SOURCE_DIGEST_ALGORITHM,
            ENGINE_SOURCE_NORMALIZATION,
            ENGINE_VERSION,
            ENTRY_HYPOTHETICALLY_FILLED,
            ENTRY_SIGNAL_SCHEDULED,
            EXIT_HYPOTHETICALLY_FILLED,
            EXIT_SIGNAL_SCHEDULED,
            MAX_OPEN_POSITIONS,
            MAX_POSITION_PCT,
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
            STRATEGY_FAMILY,
            STRATEGY_ID,
            STRATEGY_STATUS,
            STRATEGY_VERSION,
            SUPPORTED_ASSET_CLASSES,
            _BAR_FIELDS,
            _INSTRUMENT_FIELDS,
            _MAX_CANONICAL_DEPTH,
            _MAX_CANONICAL_INTEGER_BITS,
            _MAX_CANONICAL_NODES,
            _MAX_SAFE_INPUT_MAGNITUDE,
            _MIN_SAFE_PRICE,
            _PACK_ALLOWED,
            _PACK_REQUIRED,
            _SEMVER,
            _STRATEGY_ALLOWED,
            _STRATEGY_REQUIRED,
        )
        from trading_lab_core.reporting import performance_report_markdown
    finally:
        _sys.path[:] = _original_sys_path


BASE = os.path.dirname(os.path.abspath(__file__))

RiskPolicyViolation = _risk.RiskPolicyViolation
ReproducibilityError = _canonical.ReproducibilityError
NumericSafetyError = _canonical.NumericSafetyError
AllocationSafetyError = _canonical.AllocationSafetyError

_stable_type_name = _canonical._stable_type_name
_stable_short_type_name = _canonical._stable_short_type_name
_marker_text = _canonical._marker_text
_safe_string_for_hash = _canonical._safe_string_for_hash
_path_key = _canonical._path_key
_CanonicalTraversalLimit = _canonical._CanonicalTraversalLimit
_CanonicalStreamingError = _canonical._CanonicalStreamingError
_HashCanonicalizer = _canonical._HashCanonicalizer
_safe_for_hash_details = _canonical._safe_for_hash_details
_safe_for_hash = _canonical._safe_for_hash
_canonical_dump = _canonical._canonical_dump
canonical_json = _canonical.canonical_json
canonical_sha256 = _canonical.canonical_sha256
_streaming_canonical_sha256 = _canonical._streaming_canonical_sha256
_canonical_sha256_with_issues = _canonical._canonical_sha256_with_issues
_normalized_source_bytes = _canonical._normalized_source_bytes
_normalized_source_sha256 = _canonical._normalized_source_sha256
_engine_source_paths = _canonical._engine_source_paths
_engine_source_snapshot = _canonical._engine_source_snapshot
_engine_source_manifest = _canonical._engine_source_manifest
_engine_source_bundle_digest = _canonical._engine_source_bundle_digest
_engine_source_digest = _canonical._engine_source_digest
_production_engine_source_digest = _canonical._engine_source_digest
_nonempty_string = _canonical._nonempty_string
_is_number = _canonical._is_number
_finite_float = _canonical._finite_float
_checked_result = _canonical._checked_result
_checked_add = _canonical._checked_add
_checked_subtract = _canonical._checked_subtract
_checked_multiply = _canonical._checked_multiply
_checked_divide = _canonical._checked_divide
_checked_cash_subtract = _canonical._checked_cash_subtract
_checked_effective_subtract = _canonical._checked_effective_subtract
_checked_cash_add = _canonical._checked_cash_add
_checked_effective_add = _canonical._checked_effective_add
_checked_accumulate = _canonical._checked_accumulate
_allocation_validation_error = _canonical._allocation_validation_error

_field_list = _validation._field_list
_parse_iso = _validation._parse_iso
validate_market_pack = _validation.validate_market_pack
_coerce_single_strategy = _validation._coerce_single_strategy
validate_strategy = _validation.validate_strategy

_system_risk_limits = _risk._system_risk_limits
_effective_policy = _risk._effective_policy
check_entry_allowed = _risk.check_entry_allowed
drawdown_halt_triggered = _risk.drawdown_halt_triggered
decision_log_entry = _risk.decision_log_entry

sma = _strategy.sma
_sma_cross_signals_from_series = _strategy._sma_cross_signals_from_series
_safe_raw_strategy_identity = _strategy._safe_raw_strategy_identity

_assumptions = _execution._assumptions
_reproducibility_failure_metadata = _execution._reproducibility_failure_metadata
_empty_result = _execution._empty_result
_event = _execution._event
_decision = _execution._decision


def sma_cross_signals(ohlcv, fast, slow):
    """Compatibility wrapper preserving facade-level SMA monkey-patching."""
    return _strategy.sma_cross_signals(
        ohlcv, fast, slow, _sma_function=sma,
    )


def _facade_engine_source_snapshot():
    """Capture production provenance or pair an injected digest explicitly."""
    if _engine_source_digest is _production_engine_source_digest:
        return _engine_source_snapshot()
    injected_digest = _engine_source_digest()
    _captured_digest, captured_manifest = _engine_source_snapshot()
    return injected_digest, captured_manifest


def _metadata(historical_pack, strategy, input_hash, strategy_hash, policy,
              engine_source_digest=None, raw_strategy_identity=None,
              engine_source_manifest=None):
    """Compatibility wrapper for deterministic execution metadata."""
    if engine_source_digest is None and engine_source_manifest is None:
        engine_source_digest, engine_source_manifest = (
            _facade_engine_source_snapshot()
        )
    elif engine_source_manifest is None:
        _captured_digest, engine_source_manifest = _engine_source_snapshot()
    return _execution._metadata(
        historical_pack,
        strategy,
        input_hash,
        strategy_hash,
        policy,
        engine_source_digest=engine_source_digest,
        engine_source_manifest=engine_source_manifest,
        raw_strategy_identity=raw_strategy_identity,
    )


def _run_validated(strategy, pack, policy, metadata,
                   initial_last_loss_size_pct=None):
    """Compatibility seam for the validated execution state machine."""
    return _execution._run_validated(
        strategy,
        pack,
        policy,
        metadata,
        initial_last_loss_size_pct=initial_last_loss_size_pct,
        _sma_function=sma,
    )


def run_backtest(strategy_rules, historical_pack, risk_policy=None):
    """Validate and evaluate one declarative SMA-001 rule and one instrument."""
    return _execution.run_backtest(
        strategy_rules,
        historical_pack,
        risk_policy,
        _engine_source_snapshot_function=_facade_engine_source_snapshot,
        _run_validated_function=_run_validated,
    )


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        pack_path = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")
        with open(pack_path, encoding="utf-8") as handle:
            demo_pack = json.load(handle)
        demo_strategy = {
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "family": STRATEGY_FAMILY,
            "symbol": "DEMO-EQ-A",
            "fast": 5,
            "slow": 20,
            "paper_size_pct": 5.0,
        }
        demo_report = run_backtest(demo_strategy, demo_pack)
        print(canonical_json(demo_report))
