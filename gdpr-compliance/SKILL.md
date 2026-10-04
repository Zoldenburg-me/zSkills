---
name: gdpr-compliance
description: Audit a codebase for GDPR / DSGVO compliance and produce an Art. 30 data map — every place the app collects, stores, logs or sends personal data, who receives it, legal basis, retention, data-subject-rights coverage, and a ranked gap list with fixes. Also reviews a diff or PR for new personal-data exposure. Use whenever the user mentions GDPR, DSGVO, data protection, privacy policy / Datenschutzerklärung, Impressum, AVV / DPA, processors, data map, record of processing, right to erasure / export, retention, cookies / TDDDG, or asks "are we compliant", "what personal data do we store", "map our user data" — even if they only name one of these.
metadata:
  version: "1.0.0"
---

# GDPR compliance

An engineering audit, not legal advice. The output is the material a lawyer
needs (facts traced to file:line) plus the code fixes an engineer can make
now. Legal bases and retention periods are always marked "proposal, confirm
with counsel".

Three layers, same as any privacy work: **classification** (what is personal
data, whose), **flow** (where it is stored and who receives it), **control**
(rights, retention, security, transparency).

## Modes

Pick from the request; default is `audit`.

| Mode | Trigger | Output |
|---|---|---|
| `audit` | "map our data", "are we GDPR compliant", no diff named | Full data map document + gap list |
| `diff` | "check this PR / my changes for GDPR", pre-merge | Findings on the diff only |
| `notice` | "write the privacy policy / Datenschutzerklärung" | Art. 13 notice draft built from an existing data map |
| `fix` | "fix the GDPR gaps", after an audit | Code changes for the gaps the user picks |

## Audit workflow

1. **Ground truth first.** Read the repo's agent notes (AGENTS.md / CLAUDE.md /
   README), any existing privacy page, and `docs/`. Note what the project
   says it does with data; the audit checks the code against it.
2. **Deterministic scan.** Run
   `bash ~/.claude/skills/gdpr-compliance/scripts/pii_scan.sh <repo-root>`.
   It lists leak vectors (PII in logs, browser storage, PII in URLs, outbound
   hosts, cookies, trackers, IP handling, delete routes, external scripts).
   Hits are leads, not findings.
3. **Parallel sweeps.** Launch the four read-only Explore agents in
   `references/sweep-prompts.md` in ONE message (accounts & auth; partners &
   third parties; business / invoicing / bookkeeping data; infra, logs,
   legal text). Fill in the repo paths. Wait for all four.
4. **Classify roles.** For each data set decide controller vs processor
   (B2B tools usually make the app a *processor* for its customers' customer
   data, which needs an Art. 28 AVV/DPA). See `references/checklist.md` §1.
5. **Build the register.** One entry per processing activity using
   `references/report-template.md`: data, subjects, storage, purpose/basis,
   recipients, retention, gaps — each with file:line.
6. **Rank gaps** as Blocker (no notice, no erasure/export, unknown host or
   transfer, no DPA/AVV, plaintext sensitive store), Fix (concrete bugs:
   leaks in logs, public links, session not revoked), Tidy (minimisation).
7. **Publish.** Write the document as a shareable page (Artifact / doc) when
   the user wants to share it with counsel; otherwise `docs/gdpr-data-map.md`
   in the repo. End with a work plan (paperwork vs code, in PR order) and
   questions for counsel.
8. **Verify claims before stating them.** Any "X is never deleted" or "Y is
   sent to Z" must have a file:line from a sweep or your own grep. Line
   numbers drift: say so in the footer.

## Diff workflow

1. `git diff <base>...HEAD` (or the PR diff).
2. Run `pii_scan.sh` restricted to changed files (pass them as extra args).
3. For each change answer the gates below; report only real findings with
   file:line and a fix.

## Decision gates (every new field, route, log line, integration)

- Is it personal data? (directly or indirectly identifying: name, email,
  phone, IBAN, wallet address linked to a user, IP, device ids, free text
  about a person). Wallet addresses and hashes of emails are pseudonymous,
  still personal data.
- Whose? The user, or a third party (customer, supplier, payee, invitee)?
- Is it needed for the stated purpose (minimisation)? Store the fields the
  screen reads, not the whole upstream snapshot.
- Where does it go? Server db, browser storage, logs, URL, on-chain,
  third-party API. Each new recipient needs a notice line and usually a DPA.
- How long does it live, and what deletes it?
- Can the subject get it out (Art. 15/20) and get it erased or restricted
  (Art. 17/18)? Statutory retention means anonymise or restrict, not ignore.
- Is it publicly reachable without login (bearer links, pay pages, document
  verifiers)? Then: expiry, revoke, allowlisted projection.

## Guardrails when writing fixes

- Never put personal data in logs, error strings sent to clients, URLs or
  query strings, or analytics events. Log opaque ids and upstream error codes,
  not bodies.
- Prefer not storing over encrypting; prefer encrypting with a key held off
  the data host over encrypting with a key in the same env.
- Erasure that collides with retention: anonymise or mark restricted, keep
  the statutory record, document why.
- On-chain data cannot be erased: inform before the write, minimise what is
  linked to an address off-chain.
- Respect project invariants (e.g. "gating never deletes"): an explicit,
  audited account-closure path is a different thing from a side-effect
  delete. Update the project's agent notes when adding one.
- Sign-out must revoke the server session and clear local personal data.

## References

- `references/checklist.md` — article-by-article checklist, German specifics
  (DDG §5 Impressum, TDDDG §25 storage, BDSG §38 DPO, §147 AO / §14b UStG
  retention), leak vectors, DSR implementation patterns.
- `references/sweep-prompts.md` — the four parallel research prompts.
- `references/report-template.md` — document skeleton and register entry.
- `scripts/pii_scan.sh` — grep-based lead finder.

## Related skills

- `security-review` — auth, secrets, input handling (GDPR Art. 32 overlaps).
- `repo-leak-scan` — personal data or secrets already pushed to git history.
- `healthcare-phi-compliance` / `hipaa-compliance` — health data (Art. 9
  special category) and US overlay.
