# Data map document skeleton

Title: "<Product> GDPR Data Map". Date, source branch, scope, "not legal advice".

1. **Where we stand** — 4–6 facts: store and encryption, host location,
   erasure/export, notice status, what is already good, controller/processor
   split.
2. **Who is controller** — table: data set → role → consequence.
3. **Processing register** — one entry per activity:

   ```
   N. <Activity> — <main file refs>
   Data:        fields (bold the sensitive / surprising ones)
   Subjects:    users | customers | suppliers | invitees | ...
   Stored:      server db / browser / on-chain / third party
   Purpose/basis: Art. 6(1)(x) — proposal
   Recipients:  who gets what, default on/off
   Retention:   current behaviour → proposed period
   Gaps:        concrete, with file:line
   ```

4. **Recipients and processors** — table: recipient, what it gets, default,
   role, to-do (DPA, notice line, transfer mechanism). Countries only where
   the code/docs state them.
5. **Public / permanent data** — on-chain, public pages, bearer links.
6. **Storage, logs, access** — db, copies, backups, logs, audit, operators.
7. **Data subject rights** — Art. 13/15/16/17/18/20/21: today vs needed.
8. **Retention schedule (proposal)** — record, period, basis, what happens after.
9. **Gaps** — ranked Blocker / Fix / Tidy, each with the fix in one line.
10. **Work plan** — paperwork (no code) and code in PR order.
11. **Questions for counsel**.

Footer: built from a read-only sweep on <date>; line numbers drift.
