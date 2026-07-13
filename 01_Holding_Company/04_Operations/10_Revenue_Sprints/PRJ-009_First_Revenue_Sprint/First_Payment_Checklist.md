# ALSAKKAF HOLDING GROUP

# First Payment Checklist

> "The first payment must be as clean as the hundredth."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RSP-012 |
| Document Type | Payment Process Checklist |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-13 |
| Owner | Founder / CEO |
| Related System | AOS |
| Related Project | PRJ-009 |
| Related Documents | RSP-007, STRAT-014, RSP-013 |

---

# 1. Before Sending Any Payment Request

- [ ] The client has said yes in writing (email/DM) to a specific offer at a specific price
- [ ] Scope confirmed in writing: exactly what they get, delivery time, one revision round
- [ ] The proposal they agreed to is saved in the client's folder

# 2. Path A — $399 AI Workflow Starter Pack (active link)

- [ ] Send the approved PayPal link by email, together with a one-paragraph scope recap: `https://www.paypal.com/ncp/payment/2AN8FH99X682C`
- [ ] Update `Client_Pipeline.csv`: Payment Link Sent = Yes, Payment Status = Link Sent
- [ ] When PayPal confirms payment (check your own PayPal account manually): Payment Status = Paid, record date and amount
- [ ] Send a same-day confirmation email: thank you + intake form + delivery timeline
- [ ] Open `First_Client_Delivery_Start_Checklist.md` and start it

# 3. Path B — $450 AI Agent Starter Pack (no link yet)

- [ ] Do NOT improvise a payment method. The $450 offer has no approved payment link.
- [ ] Founder action required: create the $450 PayPal payment link in your own PayPal account (manual, outside Claude/Atlas), then approve it explicitly before it is used or stored anywhere in AOS
- [ ] Until that exists: confirm the agreement in writing and tell the client payment details follow within 1 business day
- [ ] If the Founder chooses, the existing manual PayPal invoice feature (sent from your own account) may bridge one deal — Founder's own action, never stored in the repo
- [ ] After payment confirms: same as Path A — pipeline updated, confirmation + intake sent, delivery checklist started

# 4. Always

- [ ] No credential, login, bank detail, or API key is ever typed into any AOS file — only the public link and the payment status
- [ ] Every status change lands in `Client_Pipeline.csv` the same day
- [ ] Run `py 09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py payment-report` after any change

# 5. If Payment Fails or Stalls

- [ ] One polite reminder after 2 business days
- [ ] After 5 business days of silence: mark Payment Status = Stalled, move on, keep the relationship warm
- [ ] Never start delivery before payment is confirmed (this protects both sides)

---

# 6. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version (PRJ-009) |
