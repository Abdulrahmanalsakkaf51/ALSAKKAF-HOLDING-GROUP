# ALSAKKAF HOLDING GROUP

# First Client Delivery Start Checklist

> "The first 24 hours after payment decide the testimonial."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RSP-013 |
| Document Type | Delivery Kickoff Checklist |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-13 |
| Owner | Founder / CEO |
| Related System | AOS |
| Related Project | PRJ-009 |
| Related Documents | RSP-012, RLCD-001, AIAD-001 |

---

# 1. Same Day as Payment Confirmation

- [ ] Confirmation email sent: thank you, what happens next, delivery window
- [ ] Intake form sent ($399: RLCD intake; $450: AI_Agent_Client_Intake_Form.md)
- [ ] Client folder created under `05_Client_Delivery` (client name, date, service)
- [ ] `Client_Pipeline.csv`: Payment Status = Paid, Delivery Status = Awaiting Intake
- [ ] Run `py 09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py payment-report`

# 2. When Intake Answers Arrive

- [ ] Read answers fully; email any clarifying questions within 24 hours
- [ ] Delivery clock starts now (5-7 business days) — note the target date in the pipeline
- [ ] Generate the working checklist:
  - $399 → `py 09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py delivery-checklist`
  - $450 → `py 09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py ai-agent-delivery`
- [ ] Follow the matching delivery workflow (RLCD-001 or AIAD-001) day by day

# 3. During Delivery

- [ ] One short progress note to the client mid-way (day 3) — unprompted communication builds trust
- [ ] All drafts reviewed by you before anything reaches the client
- [ ] Scope guard: anything outside the agreed deliverables list is logged for a future quote, not silently added

# 4. At Handover

- [ ] Full package delivered with the handover document ($450: AI_Agent_Final_Handover_Template.md)
- [ ] Setup/walkthrough session booked ($450 includes the 30-minute session)
- [ ] Revision window explained (dates in writing)
- [ ] `Client_Pipeline.csv`: Delivery Status = Delivered

# 5. Close-Out

- [ ] Revision round completed (if requested) within its window
- [ ] Testimonial requested once, politely, after value is visible
- [ ] Lessons logged in the sprint lessons file and PRJ-009 progress log
- [ ] Anonymized reusable structures indexed by The Librarian

---

# 6. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version (PRJ-009) |
