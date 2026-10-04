# GDPR checklist for code audits

Proposals, not legal advice. Statute numbers are given so counsel can check
them quickly; verify periods and names against current law before relying.

## 1. Roles

| Situation | Role | Consequence |
|---|---|---|
| App's own users (account, login, payments they make) | Controller | Art. 13 notice, Art. 30 record, handle rights |
| Data a business customer puts in about *its* customers/suppliers/staff | Processor | Art. 28 AVV/DPA with each customer, sub-processor list, delete/return at contract end, customer answers its own data subjects |
| Licensed partner doing its own regulated job (bank, EMI, KYC provider) | Independent controller | Notice says what the app sends and when; no DPA, maybe a data-sharing clause |
| Hosting, CDN/tunnel, email, SMS, bundler, recovery service | Processor | DPA, listed in notice, transfer check |
| Public authority lookup (e.g. EU VIES) | Recipient | Listed in notice |

## 2. Article checklist

- **Art. 5** principles: minimisation (store what the UI reads), accuracy,
  storage limitation (every collection has a period), integrity.
- **Art. 6** a basis per purpose: (b) contract, (c) legal duty, (f)
  legitimate interest (needs balancing note), (a) consent only when nothing
  else fits.
- **Art. 7** consent records: what, version, time; withdrawable.
- **Art. 8** children: DE age 16. Financial apps usually set 18+ in terms.
- **Art. 9** special categories (health, biometrics used for ID, etc.):
  passkeys verify locally and are NOT biometric data processing by the app.
- **Art. 12–14** notice: controller + contact, purposes and bases,
  recipients, transfers, retention, rights, complaint authority, source of
  data not collected from the subject (Art. 14).
- **Art. 15/20** export: everything tied to the subject, machine-readable.
- **Art. 16** rectification: email and name change paths.
- **Art. 17** erasure, **Art. 18** restriction, **Art. 21** objection.
- **Art. 25** privacy by design and default.
- **Art. 28** processor contracts; **Art. 30** record of processing.
- **Art. 32** security: encryption at rest and in transit, key separation,
  access control, backups and restore (32(1)(c)), testing.
- **Art. 33/34** breach: 72 h to authority; procedure written down.
- **Art. 35** DPIA: likely for financial data + new tech + large scale.
- **Art. 37** DPO; DE: BDSG §38 when ≥20 persons regularly process
  personal data automatically, or when a DPIA is mandatory.
- **Art. 44–49** transfers outside EEA: adequacy (incl. EU-US DPF), SCCs.
  Unknown hosting location = unassessed transfer = blocker.

## 3. German specifics

- **Impressum**: DDG §5 (replaced TMG §5) — operator name, address, register,
  VAT id, contact.
- **Device storage / cookies**: TDDDG §25 (formerly TTDSG). Strictly
  necessary storage needs no consent; everything else does.
- **Retention (business records)**: books, annual accounts 10 years
  (§147 AO, §257 HGB); Buchungsbelege and invoices 8 years after the
  Bürokratieentlastungsgesetz IV (§147 AO, §14b UStG, from 2025); business
  letters 6 years. Period starts at the end of the calendar year. Confirm.
- **Supervisory authority**: the Land authority where the company sits
  (e.g. BayLDA for private companies in Bavaria).

## 4. Leak vectors to grep for

- `console.*` / logger lines with name, email, IBAN, phone, address, full
  objects, upstream error bodies.
- Personal data in URLs: `?email=`, `params.set("email", …)`, path segments.
- Browser storage: `localStorage` / `sessionStorage` / IndexedDB holding
  other people's data, drafts with customer data, secrets keyed by email.
- Public bearer links: invoice/document/pay links with no expiry, revoked
  items still served, enumerable ids, CORS-open endpoints.
- Outbound calls: every `fetch(` / SDK client — what fields leave.
- Frontend third parties: CDN scripts, Google Fonts, analytics, maps
  (each one sends the visitor's IP).
- Audit logs: unsalted hashes of emails are linkable — use HMAC.
- Stored raw upstream snapshots (`profiles[]`, `any[]` blobs).
- Sign-out that clears only the client and leaves the server session live.
- Backups and preview copies of the db lying around.

## 5. Data-subject-rights patterns

- **Export**: `GET /users/:id/export` → JSON of every row keyed by the user
  (account, consents, sessions metadata, transfers, audit rows, recovery,
  partner links). Authenticated, rate-limited, audited.
- **Account closure**: explicit, audited route. Delete what has no
  retention duty; anonymise (replace identifiers with a tombstone id) what
  must be kept; set `restrictedAt` so retained rows only feed statutory
  exports. Never a side effect of plan gating.
- **Retention sweep**: one job (or load-time pass) per collection with the
  period from the schedule; log counts, not contents.
- **Processor deletion**: org closure → export for the customer, then delete
  or anonymise after the agreed window; propagate to sub-processors.

## 6. Ranking

- **Blocker**: no Art. 13 notice / Impressum; no erasure or export; unknown
  host or unassessed transfer; no DPA/AVV where needed; plaintext store of
  sensitive data with the key on the same host; no backups.
- **Fix**: concrete leaks and bugs (logs, URLs, public links, session not
  revoked, revoked docs still served, missing platform GDPR webhooks).
- **Tidy**: minimisation, retention of small artefacts, role-based field
  hiding, operator accountability.
