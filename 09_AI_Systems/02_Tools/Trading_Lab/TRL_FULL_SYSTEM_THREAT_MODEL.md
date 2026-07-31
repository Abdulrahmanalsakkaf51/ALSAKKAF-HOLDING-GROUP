# TRL Full-Vision System Threat Model

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | Full-vision program, Phase 2 |
| Status | Living document — update whenever a new attack surface is added in a later phase |
| Scope | Everything from TRL-R2-006 through Phase 10 (signal generation, MT5 execution, baskets, TradingView intake, private online/mobile, live arming, reconciliation) |

## 1. Assets to protect

1. Broker account funds and open positions (the highest-value asset).
2. Broker credentials (never stored in this repo or sent to a browser).
3. The append-only audit timeline's integrity (a compromised timeline could hide a loss or a duplicate order).
4. The Founder's authentication session and reauthentication tokens.
5. The local machine's ability to keep running unattended automation safely (a stuck/looping automation is itself a risk to funds even without an external attacker).

## 2. Actors

| Actor | Motivation | Capability |
|---|---|---|
| Remote unauthenticated attacker | Financial gain, disruption | Network access to any exposed port |
| Authenticated but unauthorized viewer (stolen VIEWER session) | Reconnaissance | Read access to account state |
| Compromised FOUNDER_OPERATOR session (stolen cookie/device) | Financial gain | Full mutation capability unless mitigated |
| Malicious or spoofed TradingView webhook sender | Trigger unwanted trades | Crafted HTTP POST to the intake endpoint |
| A buggy or manipulated LLM/generative component | Unintentional harmful proposal content | Text-only influence on proposal explanation/summary fields |
| The system itself, malfunctioning (stale data, clock skew, storage corruption, runaway loop) | None (non-adversarial but still dangerous) | Whatever authority the automated path currently holds |

## 3. Attack surfaces and mitigations

### 3.1 Local HTTP API (loopback)
- **Threat:** host-header/DNS-rebinding tricking a browser into treating a remote page as same-origin with the loopback server.
- **Mitigation:** existing R2-005 host-header allowlist protection carries forward unchanged; extended to all new routes.
- **Threat:** a new mutation route added in a later phase forgets authentication.
- **Mitigation:** a single shared authorization decorator/middleware used by every mutating route (Phase 8); acceptance tests assert *every* registered mutating route requires it, not just the ones remembered at design time.

### 3.2 Private online tunnel
- **Threat:** tunnel misconfiguration exposes the loopback port publicly.
- **Mitigation:** R2-008 refuses to claim "online" without detecting the tunnel; startup never rebinds to `0.0.0.0`; periodic self-check that the bound address is still loopback.

### 3.3 Session/auth layer
- **Threat:** stolen session cookie used for a mutation.
- **Mitigation:** mutation reauthentication (Section 3, R2-008 contract) means a cookie alone is insufficient; CSRF token additionally required; short session idle timeout.
- **Threat:** brute-force login.
- **Mitigation:** throttling/lockout, audited.

### 3.4 TradingView webhook intake (optional, Phase 7)
- **Threat:** spoofed alert triggers an unwanted trade.
- **Mitigation:** signed/authenticated payload required, source allowlist where practical, replay nonce, timestamp tolerance, idempotency key; the result is always an `UNTRUSTED_PROPOSAL` that must clear the full R2-006 pipeline — a forged webhook can at worst waste a pipeline evaluation, never place an order directly.
- **Threat:** replay of a previously valid alert.
- **Mitigation:** nonce + nonce-reuse rejection + alert expiry.

### 3.5 MT5 execution adapter
- **Threat:** account/broker/server mismatch sends a live order intended for demo, or vice versa.
- **Mitigation:** allowlisted fingerprint check (login/company/server) is mandatory preflight (R2-007 contract Section 3), fails closed on mismatch.
- **Threat:** duplicate order after crash/restart or network timeout ambiguity.
- **Mitigation:** a deterministic, nonce-free lookup key (R2-007 contract Section 5.1) — derived only from stable fields (proposal, account/broker fingerprint, instrument, side, approved size, basket-child identity, strategy, risk-policy hash, mode, authorization identity) — is searched *before* any nonce or new intent is created (Section 5.2), so a genuinely repeated submission always resolves to the existing intent rather than risking a fresh, differently-keyed one. The immutable execution-intent identity itself (Section 5.3) additionally never depends on price, spread, or tick, which legitimately change between attempts. An ambiguous outcome freezes the intent and forces reconciliation (R2-007 contract Section 7) before any further attempt; only a `NOT_FOUND_SAFE_TO_RETRY` classification permits a new attempt, and only under the same intent. A lookup or durable-store failure fails closed to manual review rather than ever falling back to creating a new intent.
- **Threat:** unprotected live position after a partial failure.
- **Mitigation:** mandatory stop validation before entry, reconciliation flags any position missing a confirmed stop (R2-007 contract Section 8).
- **Threat:** the broker's smallest tradeable size alone exceeds the intended risk on a system that has never placed a live order before.
- **Mitigation:** the first-live-activation risk floor (R2-007 contract Section 4) computes the exact risk of the broker's minimum volume before any first live order and fails closed with `FIRST_LIVE_MINIMUM_VOLUME_EXCEEDS_TARGET_RISK` if it exceeds 0.1% of equity, requiring a separate, single-use, proposal-specific Founder override — and prohibiting the trade outright, with no override possible, above 0.5%.

### 3.6 Controlled basket execution
- **Threat:** basket construction inflates risk beyond the parent proposal's approved budget.
- **Mitigation:** aggregate risk budget shared across all child orders, enforced before any child is sent, not summed after the fact.
- **Threat:** browser refresh resubmits a basket.
- **Mitigation:** each basket child order carries its own stable `basket_child_id` and its own execution intent (R2-007 contract Sections 5.1, 5.6) anchored to the basket's approved aggregate-risk identity; a resubmission of the parent basket resolves every child, via the deterministic lookup key, to its existing intent — never a new basket, and never a dropped or duplicated child.

### 3.7 LLM/generative components
- **Threat:** prompt injection via news text or a crafted TradingView payload causes the LLM to suggest an oversized or malformed proposal.
- **Mitigation:** LLM output only ever populates explanation/summary/classification fields; every numeric field that matters (size, stop, target, risk) is computed and re-validated by the deterministic pipeline (R2-006 contract Section 6), which has no path for an LLM string to override a number.

### 3.8 Non-adversarial system failure
- **Threat:** stale market data feeds a stale-but-plausible price into sizing/fill logic.
- **Mitigation:** freshness bounds on every observation, reused from R2-005, enforced again at the MT5 preflight layer.
- **Threat:** clock skew between the host and the broker server.
- **Mitigation:** clock-anomaly watchdog (Phase 9) halts automation rather than trusting a suspicious timestamp.
- **Threat:** storage corruption silently loses state.
- **Mitigation:** R2-005's fail-closed corruption handling extends to every new storage document introduced in later phases; a corrupted document never falls back to "assume empty."
- **Threat:** a runaway automated loop keeps submitting proposals faster than a human can intervene.
- **Mitigation:** arming state machine (Phase 9) requires deliberate arming with expiry; watchdog halts on repeated rejection.

## 4. Out of scope for this program

- Physical security of the host machine.
- Operating-system-level compromise of the Windows host itself (assumed trusted).
- Broker-side infrastructure security (trusted third party).
- Deriv digit/binary-contract execution (explicitly excluded from this program).

## 5. Residual risk accepted by the Founder

Even with every mitigation above, automated live trading carries irreducible
market and execution risk that no software control eliminates: slippage,
gaps, broker outages, and genuine strategy underperformance. This threat
model addresses *unauthorized or unintended* actions and *silent failures* —
it does not and cannot promise trading profitability, which is why no
confidence or performance figure in this system is ever presented as a
guarantee.

## 6. Review cadence

This document is updated at the start of every phase from Phase 3 onward,
before that phase's implementation begins; again if that phase's
implementation reveals a surface not anticipated here; and immediately,
outside the normal cadence, whenever a security-relevant design decision
changes mid-phase (for example, a preflight bound is widened, a new
mutation route is added, or an identity/idempotency scheme changes) — the
review is not deferred to the next phase boundary in that case.
