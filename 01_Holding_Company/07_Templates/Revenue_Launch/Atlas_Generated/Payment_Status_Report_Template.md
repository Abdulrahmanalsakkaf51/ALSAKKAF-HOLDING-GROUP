# Payment Status Report — Template

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RLAG-006 |
| Owner | Abdulrahman Alsakkaf |
| Status | Active |
| Version | 1.0 |
| Created | 2026-07-13 |
| Related Documents | PRJ-007, STRAT-014, ACC-003 |

---

## Purpose

The shape of a payment status report Atlas's `atlas.py payment-report` command generates from `Client_Pipeline.csv`.

**This report never connects to PayPal directly and never requests, stores, or displays any PayPal login, password, 2FA code, recovery code, API key, or bank detail. It only reflects what the CEO has manually recorded in the tracker.**

---

## Template

| Client | Service | Quoted Price (USD) | Payment Link Sent | Payment Status | Delivery Status | Next Action |
|--------|---------|---------------------|--------------------|-----------------|-------------------|-------------|
| [Client Name] | [Service] | $[N] | [Yes/No] | [Not Sent / Sent / Paid] | [Status] | [Action] |

**Summary:** [N] paid, [N] link sent awaiting payment, [N] not yet sent.

---

## How to Use

1. Update `Client_Pipeline.csv` manually when a payment is confirmed (e.g. via PayPal notification checked by the CEO) — Atlas never checks PayPal itself.
2. Never add a column or field for PayPal credentials to this report or its source CSV.
