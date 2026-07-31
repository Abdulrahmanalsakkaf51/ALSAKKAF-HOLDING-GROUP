"""Generative/LLM component boundary (TRL-R2-006).

Generative components are disabled by default. In Phase 4:

- No external LLM/API call is required for normal operation.
- Automated tests make no external model call; ``NoOpGenerativeAdapter`` is
  the only adapter wired into ``signal_pipeline.py`` and is a pure
  deterministic function.
- No API key or model credential is required or read from anywhere.
- A model may only ever produce a bounded, sanitized *annotation* string
  (``model_annotation`` on the pipeline result) — never a numeric,
  eligibility, or outcome field. The governed ``TRL_SIGNAL_PROPOSAL.v1``
  schema (``signal_data.py``) has no field a generative adapter can write
  to; entry, stop, target, quantity, risk, eligibility, expiry, and the
  final BUY/SELL/HOLD/WAIT/BLOCKED outcome are always the deterministic
  pipeline's own values.
- Malformed, oversized, or adversarial (prompt-injection) adapter output
  is sanitized to an inert bounded string and never raises out of
  ``annotate`` — a failure here must never abort proposal generation.
"""

MAX_ANNOTATION_LENGTH = 500
MAX_HYPOTHESIS_ECHO_LENGTH = 200


def sanitize_model_text(value, maximum=MAX_ANNOTATION_LENGTH):
    """Bound and strip a piece of model-sourced text to an inert string.
    Never raises; unusable input becomes an empty string."""
    if not isinstance(value, str):
        return ""
    cleaned = "".join(character for character in value if ord(character) >= 32 and ord(character) != 127)
    return cleaned[:maximum]


class GenerativeAdapter:
    """Strict interface every generative/LLM adapter must implement.

    ``annotate`` receives only already-governed, already-decided pipeline
    output (role results, the final outcome, and any operator-supplied
    research hypothesis text) — never a live evidence feed, never write
    access to any proposal field, and no reference to the paper engine or
    a future execution adapter. Implementations must not make a network
    call from within this method during the automated test suite.
    """

    def annotate(self, pipeline_context):
        raise NotImplementedError


class NoOpGenerativeAdapter(GenerativeAdapter):
    """The default, disabled-by-default adapter: deterministic, no network
    call, no model credential. Only ever echoes back a sanitized, bounded
    copy of the operator-supplied research hypothesis (if any) — it does
    not classify, summarize, or invent anything, and it never sees or
    touches numeric/eligibility fields."""

    enabled = False

    def annotate(self, pipeline_context):
        hypothesis = pipeline_context.get("model_hypothesis")
        echo = sanitize_model_text(hypothesis, MAX_HYPOTHESIS_ECHO_LENGTH) if hypothesis else None
        return {
            "model_annotation": echo,
            "model_adapter_enabled": False,
            "model_adapter_name": "NoOpGenerativeAdapter",
        }


def annotate_safely(adapter, pipeline_context):
    """Invoke an adapter and fail closed to an inert result on any error,
    guaranteeing a malformed/hostile adapter can never abort or alter
    proposal generation. Governed timeline payloads reject empty strings
    (see ``timeline_data.sanitize_payload``), so "no annotation" is
    represented as ``None``, never ``""``."""
    try:
        result = adapter.annotate(pipeline_context)
    except Exception:
        return {
            "model_annotation": None,
            "model_adapter_enabled": False,
            "model_adapter_name": type(adapter).__name__,
        }
    if not isinstance(result, dict):
        return {
            "model_annotation": None,
            "model_adapter_enabled": False,
            "model_adapter_name": type(adapter).__name__,
        }
    annotation = sanitize_model_text(result.get("model_annotation")) or None
    return {
        "model_annotation": annotation,
        "model_adapter_enabled": bool(result.get("model_adapter_enabled", False)),
        "model_adapter_name": sanitize_model_text(result.get("model_adapter_name"), 100) or type(adapter).__name__,
    }


__all__ = (
    "MAX_ANNOTATION_LENGTH",
    "GenerativeAdapter",
    "NoOpGenerativeAdapter",
    "annotate_safely",
    "sanitize_model_text",
)
