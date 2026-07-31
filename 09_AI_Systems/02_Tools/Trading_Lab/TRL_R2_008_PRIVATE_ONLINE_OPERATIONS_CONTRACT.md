# TRL-R2-008 Private Online and Mobile Operations Contract

> **AUTHENTICATED PRIVATE ACCESS ONLY — NEVER A PUBLIC ENDPOINT — NO BROKER CREDENTIAL EVER REACHES THE BROWSER**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-008 |
| Status | Design contract — implementation not yet started |
| Depends on | TRL-R2-005 (dashboard), TRL-R2-006 (proposals), TRL-R2-007 (execution) |

## 1. Boundary

The backend keeps binding to `127.0.0.1` wherever possible; this checkpoint
adds an authenticated layer in front of it and a mobile-friendly PWA shell —
it does not open a public port. If no secure tunnel (Tailscale or equivalent
already-authenticated tunnel) is detected, the system reports the exact
missing prerequisite and stops short of claiming to be "online." It never
opens a router port automatically and never disables Windows Firewall.

## 2. PWA requirements

- Responsive layout for phone-width viewports (reuses the existing dashboard's semantic sections, restyled with breakpoints — no separate mobile codebase).
- Installable web app manifest (`name`, `short_name`, `icons`, `start_url`, `display: standalone`).
- Service worker scope limited to **safe static assets only**: HTML shell, CSS, JS, icons. It never caches an API response, and explicitly never caches anything under `/api/` or any future mutation route.
- Mode badge, broker connection status, account mode (DEMO/LIVE), balance, equity, margin, free margin, margin level, realized/unrealized/daily P&L, drawdown, open risk, positions, pending orders, proposals, rejected proposals, baskets, execution history, timeline, health, and emergency state are all present on the mobile layout, not just desktop.
- Start/stop automation, disable-new-entries, and governed close controls are reachable from mobile, gated by the same authorization as desktop (Section 3) — no separate, weaker mobile auth path.

## 3. Authentication and authorization

- No anonymous route can trigger a mutation. Read-only dashboard views may remain behind the same login as everything else — there is no unauthenticated tier once this checkpoint is active.
- Passwords are never stored in plaintext or reversible form — password hashes only (a strong, salted KDF; no custom hashing scheme).
- Sessions use secure, `HttpOnly`, `SameSite` cookies.
- CSRF tokens required on every mutating request.
- Login throttling (exponential backoff or fixed lockout window after repeated failures) recorded as an audit event.
- Session expiry after a configured idle window; expired sessions are rejected server-side, not just hidden client-side.
- Two roles: `VIEWER` (read-only) and `FOUNDER_OPERATOR` (read + governed mutation). No role may be self-escalated through any client-supplied field.
- Mutation endpoints require reauthentication (fresh credential or short-lived step-up token) beyond just having a valid session cookie — a stolen session cookie alone cannot arm or execute.
- Every login attempt (success and failure) and every mutation attempt (success and rejection) is an audit event.
- Broker credentials are never sent to, stored in, or derivable from anything the browser receives. Account identifiers are redacted where full disclosure isn't needed (e.g. login number is shown, but nothing that could reconstruct a credential).
- No secret of any kind appears in JavaScript source, inline or bundled.

### Lockout recovery (added in the Phase 2 correction pass)

The system has exactly one `FOUNDER_OPERATOR` account. Login throttling
(above) must never be able to permanently strand the Founder out of their own
system, but recovery must not become a hidden bypass either. The procedure:

1. Recovery is initiated **only** by running a local command
   (`trading_lab_app --recover-founder-account`) directly on the host
   machine — never through any HTTP route, browser page, or remote/tunnel
   call. The ability to run a local process on the host **is** the proof of
   control over the host; there is no network-reachable recovery path of any
   kind.
2. Running it generates a single-use, randomly generated recovery token —
   never a fixed, default, or predictable value — printed only to that local
   console session. It is never written to a file, never written to a log,
   and never committed to Git.
3. The token is valid for a short, fixed window (target: 10 minutes) and
   must be exchanged, over the loopback-only local interface, for a
   Founder-chosen new password. Completing this exchange requires having
   actually run the command on the machine and read its console output —
   browser-only access can never complete it, so this is not a privilege
   escalation path reachable from the network.
4. Generating a new recovery token immediately invalidates any
   previously issued, unused recovery token. Only one recovery token is ever
   live at a time.
5. Successfully using a recovery token immediately rotates out (invalidates)
   every existing session held under the `FOUNDER_OPERATOR` role, forcing a
   fresh login everywhere with the new credential.
6. Both the generation and the use of a recovery token — successful or
   failed — are audit events.
7. Recovery resets only the login credential. It never touches, weakens, or
   bypasses mutation reauthentication or the live-trading arming flow
   (`TRL_LIVE_EXECUTION_RUNBOOK.md` Section 3) — a Founder who just recovered
   account access still must complete the full arming procedure separately
   before anything can execute against a broker.

## 4. Online deployment

- Backend stays bound to loopback; the private HTTPS layer terminates in front of it (a local authenticated reverse proxy or tunnel), never the reverse.
- Startup detects whether Tailscale (or an equivalent already-authenticated tunnel) is installed and configured; if not, it reports this exact gap rather than silently running loopback-only while claiming "private online operation complete."
- Raw port 8765 (or whatever the configured port is) is never exposed publicly — no automatic router port-forwarding, no `0.0.0.0` bind change, ever.
- Health, readiness, and liveness endpoints (Phase 10) are available to the tunnel/proxy for monitoring but carry no sensitive account data.
- Startup/shutdown scripts and an optional Windows startup task are provided for the *local* service only; nothing is installed system-wide without being explicitly reported to the Founder first.

## 5. Data boundary for cached/offline PWA state

- The service worker's cache is static-asset-only (Section 2); there is no offline account/position cache, so a stale phone can never show stale balances as if current.
- On reconnect, the client always re-fetches live state before rendering any account figures — no optimistic/stale rendering of financial data.

## 6. Acceptance tests

- CSRF test: a mutation request without a valid token is rejected.
- Session-expiry test: an expired session cannot read or mutate.
- Role test: a `VIEWER` session cannot reach a mutation endpoint even with a valid CSRF token.
- Credential-leak test: full response/JS/manifest/service-worker source scan finds no broker credential, password hash, or session secret.
- Cache-safety test: the service worker's cache manifest contains no `/api/` path.
- Public-exposure test: default configuration binds only to loopback; enabling the tunnel requires an explicit, logged operator action.
- Login-throttling test: repeated failed logins trigger the configured lockout and an audit event.
- Recovery-locality test: no HTTP route (loopback or tunneled) can generate or redeem a recovery token; only the local CLI command can.
- Recovery-single-use test: generating a second recovery token invalidates the first; redeeming a token twice fails on the second attempt.
- Recovery-session-rotation test: redeeming a recovery token invalidates every pre-existing `FOUNDER_OPERATOR` session.
- Recovery-does-not-weaken-arming test: immediately after a successful recovery, an automated live-arming attempt still requires the full reauthentication and confirmation-phrase flow — recovery grants no execution shortcut.
