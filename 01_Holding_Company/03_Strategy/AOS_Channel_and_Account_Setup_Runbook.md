# ALSAKKAF HOLDING GROUP

# AOS Channel and Account Setup Runbook

> "The CEO owns every account. Atlas prepares the words. No password ever lives in Markdown."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | STRAT-009 |
| Document Type | Strategy / Operations Runbook |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | STRAT-005, STRAT-010, GRCA-001, PRJ-007 |

---

# 1. Purpose

This is a **manual account setup runbook, not an automation script.**

It gives the Founder a ready-to-use checklist for creating and securing every company email, social, website, and marketplace account AOS will eventually need. Nothing in this document creates an account, publishes anything, sends anything, or stores a credential. Every real account is created and owned by the CEO, by hand, when the CEO chooses to act.

---

# 2. What Atlas May and May Not Do

| Atlas may | Atlas may not |
|-----------|----------------|
| Prepare account names, handles, and bios for CEO review | Create any account automatically or on its own authority |
| Draft channel purpose and content pillar descriptions | Enter or generate passwords, recovery codes, or 2FA secrets |
| Prepare a recovery-email plan and password manager checklist | Store any credential, password, recovery code, API key, or payment detail anywhere, including Markdown |
| Prepare a security checklist for CEO and Guardian review | Approve its own security checklist as sufficient — Guardian and the CEO must review it |

---

# 3. Shared Rules for Every Account

1. Never store passwords, recovery codes, API keys, or payment data in Markdown or any file in this repository. Use a dedicated password manager outside this repo.
2. Every account uses 2-factor authentication (2FA) where the platform supports it, with an authenticator app preferred over SMS.
3. Every account's recovery email points to a company-controlled address the CEO controls directly (see Section 4).
4. The CEO is the legal owner of every account. Atlas is an informational assistant only and never appears as an account owner, admin contact, or billing contact.
5. Account metadata (handle, bio, purpose, creation date, linked recovery email — never credentials) is logged in `09_AI_Systems/03_Account_Registry/` (proposed new folder, consistent with the existing `09_AI_Systems` numbering; requires Founder approval to create, per CLAUDE.md Section 4).
6. The Librarian indexes only public-facing metadata: handle, display name, bio, platform, and purpose. The Librarian never indexes credentials, recovery codes, or payment data.
7. No account is used for real business activity (posting, messaging, selling) until **Section 11 — Guardian Review Gate** is satisfied.

---

# 4. Company Email Naming System

| Field | Convention |
|-------|-----------|
| Naming pattern | `firstname@alsakkafholding.com` (or interim free-tier equivalent until a domain is active) for the Founder; `role@alsakkafholding.com` for shared inboxes |
| Example addresses | `abdulrahman@alsakkafholding.com`, `hello@alsakkafholding.com`, `services@alsakkafholding.com`, `support@alsakkafholding.com` |
| Interim option (no domain yet) | `alsakkafholdinggroup@gmail.com` or `aosaiservices@gmail.com` as a placeholder, migrated to a domain address once the website domain (STRAT-012) is active |
| Bio/signature template | `[Name] — ALSAKKAF HOLDING GROUP • AOS AI Services • [website link]` |
| Security checklist | Strong unique password in password manager; 2FA via authenticator app; recovery phone set to CEO's own number; recovery email set to a second CEO-controlled address |
| 2FA checklist | Authenticator app enabled; backup codes generated and stored in password manager (never in Markdown); SMS 2FA only as fallback |
| Recovery email checklist | A second, separate CEO-owned mailbox set as recovery; never a Partner-suggested or automatically generated address |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Email_Accounts.md` (proposed) |
| Librarian indexes | Address, purpose, owner — never password or recovery codes |

---

# 5. YouTube Channels

| Field | Convention |
|-------|-----------|
| Naming convention | `AOS AI Services` or `ALSAKKAF AI` as the channel display name |
| Handle ideas | `@AOSAIServices`, `@AlsakkafAI`, `@AOSbyAlsakkaf` |
| Bio template | "AOS AI Services helps small businesses use AI the practical way — workflows, dashboards, and automation that actually get used. Built by ALSAKKAF HOLDING GROUP." |
| Security checklist | Google Account secured per Section 4 email rules; channel linked to the company email, not a personal one |
| 2FA checklist | Authenticator app on the linked Google Account; backup codes in password manager |
| Recovery email checklist | Linked Google Account recovery email is a second CEO-owned address |
| Owner | Abdulrahman Alsakkaf (Founder/CEO); Atlas has no login access |
| Metadata storage | `09_AI_Systems/03_Account_Registry/YouTube_Channels.md` (proposed) |
| Librarian indexes | Channel name, handle, bio, content pillars, purpose |

---

# 6. Instagram

| Field | Convention |
|-------|-----------|
| Naming convention | Business account, matching handle across platforms where available |
| Handle ideas | `@aos.aiservices`, `@alsakkaf.ai`, `@aosbuilds` |
| Bio template | "AI systems for small business 🤖 • AOS by ALSAKKAF HOLDING GROUP • Workflows • Dashboards • Automation • [website link]" |
| Security checklist | Business account linked to Facebook Page (Section 7); strong unique password |
| 2FA checklist | Authenticator app enabled in Instagram security settings |
| Recovery email checklist | Recovery email and phone set to CEO-controlled contacts |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Social_Accounts.md` (proposed) |
| Librarian indexes | Handle, bio, content pillars, purpose |

---

# 7. Facebook Page

| Field | Convention |
|-------|-----------|
| Naming convention | Page name: "AOS AI Services" or "ALSAKKAF HOLDING GROUP" |
| Handle ideas | `facebook.com/aosaiservices`, `facebook.com/alsakkafholding` |
| Bio template | "AOS AI Services — practical AI workflows, dashboards, and automation for small business, from ALSAKKAF HOLDING GROUP." |
| Security checklist | Page created under a personal Facebook account secured with a strong password and 2FA; Business Manager access limited to the CEO only |
| 2FA checklist | Authenticator app on the linked personal Facebook account |
| Recovery email checklist | Linked account recovery email is CEO-controlled |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Social_Accounts.md` (proposed) |
| Librarian indexes | Page name, handle, bio, purpose |

---

# 8. TikTok

| Field | Convention |
|-------|-----------|
| Naming convention | Business account, same handle family as Instagram |
| Handle ideas | `@aos.aiservices`, `@alsakkaf.ai` |
| Bio template | "AI made practical 🤖 • Small business workflows & automation • ALSAKKAF HOLDING GROUP" |
| Security checklist | Business account; email + phone verified with CEO-controlled contacts |
| 2FA checklist | Authenticator app or SMS 2FA enabled in account security settings |
| Recovery email checklist | Recovery email is CEO-controlled, separate from the login email where possible |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Social_Accounts.md` (proposed) |
| Librarian indexes | Handle, bio, content pillars, purpose |

---

# 9. Threads

| Field | Convention |
|-------|-----------|
| Naming convention | Linked to the Instagram business account; same handle |
| Handle ideas | `@aos.aiservices` (inherits from Instagram) |
| Bio template | Same as Instagram bio, shortened if needed |
| Security checklist | Inherits Instagram/Meta account security — see Section 6 |
| 2FA checklist | Inherits Instagram 2FA setting |
| Recovery email checklist | Inherits Instagram recovery settings |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Social_Accounts.md` (proposed) |
| Librarian indexes | Handle, bio, purpose |

---

# 10. LinkedIn

| Field | Convention |
|-------|-----------|
| Naming convention | Personal profile (Abdulrahman Alsakkaf) plus a Company Page: "ALSAKKAF HOLDING GROUP" |
| Handle ideas | `linkedin.com/company/alsakkaf-holding-group` |
| Bio template | "AOS AI Services — practical AI systems for small business. Part of ALSAKKAF HOLDING GROUP." |
| Security checklist | Strong unique password; Company Page admin limited to the CEO |
| 2FA checklist | Authenticator app enabled on the personal profile |
| Recovery email checklist | Recovery email is CEO-controlled |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Social_Accounts.md` (proposed) |
| Librarian indexes | Profile/Page name, handle, bio, purpose |

---

# 11. Website Hosting — GitHub Pages / Cloudflare Pages / Netlify

| Field | Convention |
|-------|-----------|
| Naming convention | Repository/site name matching the brand, e.g. `aos-ai-services` |
| Handle ideas | `aosaiservices.github.io`, a Cloudflare Pages project named `aos-ai-services`, or a Netlify site `aos-ai-services.netlify.app` |
| Bio template | Not applicable — see STRAT-012 for website copy structure |
| Security checklist | Hosting account linked to the company GitHub/Cloudflare/Netlify account, not a personal throwaway account; strong password; no payment method added until a paid tier is explicitly approved |
| 2FA checklist | Authenticator app enabled on the hosting platform account |
| Recovery email checklist | Recovery email is CEO-controlled |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Website_Hosting.md` (proposed) |
| Librarian indexes | Site name, URL, purpose |

---

# 12. Future Ecommerce Stores (General)

| Field | Convention |
|-------|-----------|
| Naming convention | Store name aligned with the product niche chosen during the Dropshipping and Marketplace Experiment (STRAT-011); not created until a product passes validation |
| Security checklist | Separate account from personal shopping accounts; strong password; 2FA enabled |
| Recovery email checklist | Recovery email is CEO-controlled |
| Owner | Abdulrahman Alsakkaf (Founder/CEO) |
| Metadata storage | `09_AI_Systems/03_Account_Registry/Ecommerce_Accounts.md` (proposed) |
| Librarian indexes | Store name, platform, purpose |

No ecommerce store account is created before a product passes the validation gates in STRAT-011.

---

# 13. eBay Seller Setup Checklist

- Register as a seller using a company-controlled email (Section 4), not a personal account already used for buying.
- Enable 2FA on the eBay account.
- Set recovery email/phone to CEO-controlled contacts.
- Confirm seller policies (returns, shipping, handling time) before any listing — draft only, no listing published without CEO approval.
- Confirm payment payout method is set up correctly and separately (never entered or stored in Markdown).
- Owner: Abdulrahman Alsakkaf (Founder/CEO).
- Metadata storage: `09_AI_Systems/03_Account_Registry/Ecommerce_Accounts.md` (proposed) — seller ID, store name, purpose only.

---

# 14. Amazon Seller Setup Checklist

- Register as a Professional or Individual seller using a company-controlled email (Section 4).
- Enable 2FA (Amazon requires this for Seller Central).
- Set recovery email/phone to CEO-controlled contacts.
- Complete identity verification with CEO's own legal documents — never delegated.
- Confirm tax/business information is entered correctly and stored only in Amazon's own system, never duplicated into this repository.
- Owner: Abdulrahman Alsakkaf (Founder/CEO).
- Metadata storage: `09_AI_Systems/03_Account_Registry/Ecommerce_Accounts.md` (proposed) — seller name, marketplace, purpose only.

---

# 15. Noon Seller Setup Checklist

- Register as a Noon seller/partner using a company-controlled email (Section 4).
- Enable 2FA if available; otherwise use the strongest available login protection.
- Set recovery email/phone to CEO-controlled contacts.
- Complete UAE/GCC business verification with CEO's own legal documents.
- Confirm payout bank details are entered directly into Noon's system only, never stored in this repository.
- Owner: Abdulrahman Alsakkaf (Founder/CEO).
- Metadata storage: `09_AI_Systems/03_Account_Registry/Ecommerce_Accounts.md` (proposed) — seller name, marketplace, purpose only.

---

# 16. Guardian Review Gate

No real account created under this runbook may be used for actual business activity — posting, messaging, listing, or selling — until:

1. Guardian has reviewed the account's security setup (2FA, recovery email, password manager use) against `PARTNER-016_Guardian.md` (GUARD-001) rules, and
2. The CEO has explicitly approved the account for active use.

This gate applies to every account type in this document without exception.

---

# 17. What Must Never Be Stored in Markdown

Passwords, recovery codes, API keys, and payment data must never be stored in Markdown or any file in this repository, for any account listed in this document. This rule has no exceptions and applies retroactively if such data is ever found in the repository — it must be moved to a password manager and removed.

---

# 18. Related Documents

- STRAT-005 — AOS Revenue Launch Master Plan
- STRAT-010 — AOS Multi-Platform Content Factory
- STRAT-012 — AOS Static Website and Free Hosting Plan
- GRCA-001 — AOS Governance, Risk, Compliance & Assurance Roadmap
- GUARD-001 — Guardian Partner Profile
- PRJ-007 — Launch AOS Revenue Engine

---

# 19. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-12 | Initial version created as part of the AOS Revenue Launch Operating Package |
