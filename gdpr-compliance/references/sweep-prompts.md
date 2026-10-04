# Four parallel sweeps

Launch all four as `Explore` agents in one message. Replace `<REPO>`,
`<SERVER_SRC>` and `<FRONTEND>` with real paths. Each must return a concise
structured report with file:line refs and an explicit gap list, not file dumps.

## 1. Accounts, login, sessions, devices

> GDPR data-inventory research in <REPO>. Very thorough. Read-only.
> Scope: USER ACCOUNT, LOGIN, SESSION, DEVICE data. Cover: signup fields and
> validation and where stored; passwords/passkeys/WebAuthn (credential ids,
> attestation, keys), session tokens and their storage and TTL; every
> localStorage/sessionStorage/IndexedDB/cookie key in <FRONTEND>; email/SMS
> verification and the sending provider; account recovery data; profile edit,
> account deletion and data export routes (exist?); IP/user-agent capture,
> rate-limit keys, request logs, audit logs; identity data held only per call.
> For each: fields, file:line, stored where (server db / browser / on-chain /
> third party), retention and deletion behaviour. List gaps.

## 2. Partners and third parties

> GDPR data-inventory research in <REPO>. Very thorough. Read-only.
> Scope: EVERY THIRD PARTY that receives or sends personal data. Grep
> <SERVER_SRC> (non-test) for fetch(, axios, SDK clients and https URLs. For
> each integration: what is sent (user ids, emails, names, IBANs, addresses,
> IPs), what is fetched and stored (tokens, profiles, snapshots — encrypted?),
> scopes requested, disconnect behaviour (revoked upstream?), default on/off,
> file:line. Also: frontend third-party loads (CDNs, fonts, analytics, maps),
> hosting/CDN/tunnel providers that see traffic, and data written to public
> ledgers if any. List gaps.

## 3. Business, invoicing, bookkeeping (third-party data)

> GDPR data-inventory research in <REPO>. Very thorough. Read-only.
> Scope: business/team features and anything bookkeeping. Find personal data
> about THIRD PARTIES (customers, suppliers, payees, employees, invitees):
> organisations and members and invites; address book / payees; invoices in
> and out and their public links; receipts, uploads, OCR/AI providers;
> ledger, statements, exports (CSV, DATEV, Lexware, ZIP) and accounting
> integrations; payment requests, pay pages, shop integrations (incl. the
> platform's mandatory GDPR webhooks); plans/billing. For each: fields,
> file:line, stored where, who can see it (which roles, public?), deletion
> behaviour, any retention logic (§147 AO / GoBD). List gaps: erasure vs
> retention, copies that survive a delete, missing export.

## 4. Infra, logs, legal text

> GDPR data-inventory research in <REPO>. Medium-thorough. Read-only.
> Scope: database type and location, encryption at rest, key handling,
> backups and stray copies; hosting provider and region (read deployment
> docs); every log line that includes personal data (file:line); error
> tracking / analytics / telemetry; existing privacy policy, Impressum,
> terms, cookie notice and what they claim (check claims against code);
> operator/admin routes that read user data and how operators authenticate;
> age checks. List gaps.
