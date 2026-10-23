# Judging a candidate: leak or fine

The question for every candidate is the same one TypeSafe was asked: *would a
careful maintainer remove this from the public history?* The scorer is good at
surface cues; you are there for the cases that need context, so look at the
context.

## Secrets

- **Verified live** → leak, always. Nothing else matters.
- **Verified dead** → still a leak if it is a real credential (it proves a key
  of that shape was used, and the same secret may be reused elsewhere), but
  low urgency. Fine if it is a provider's documented test key.
- **Unverified** (no TruffleHog detector, e.g. a Monerium client secret, a
  webhook signing secret, an internal JWT secret) → judge by name and place:
  `.env`, config, `*_SECRET=`, a value with high entropy next to a real host
  is a leak. `sk_test_…`, `pk_test_…`, values in `*-test.ts` built from
  `randomBytes`, `"changeme"`, `"xxx"` are fine.
- Hardhat/anvil default accounts and `test test … junk` are public; the
  scanner already drops them.

## Private data

| Kind | Leak | Fine |
|---|---|---|
| IBAN | a real account (the company's, a person's, a partner's) anywhere, including tests | the bank-doc examples (`DE89 3704 …`), a value the code generates, a sandbox IBAN that the provider documents as shared |
| email | a personal address (webmail, a named person at a company), a customer's | `security@`/`support@`/`hello@` on the project's own domain, `git@github.com`, obvious fixtures (`a@b.de`, `*.example`) |
| phone | a real person's number | `+49 151 1234567`-style patterns, `+254700000000`, placeholders in UI hints |
| home path | `/Users/<realname>/…` (names a person, reveals machine layout) | CI paths (`/home/runner`), docs telling users to put their own name |
| commit identity | a personal webmail as author/committer | the project domain, GitHub noreply |

Sandbox or test IBANs that look real are the hard case. If the file is a test
and the value appears with a named fictional company, lean fine; if the same
IBAN also appears in a non-test file, a `.env`, or next to a real name, lean leak.

## Disclosures

The scorer flags text describing a security weakness. Being about security is
not enough to make it a leak — most good commit messages about fixes are fine
and useful. Mark **leak** when the text:

- describes a weakness that is **not fixed** (or accepted as a known gap:
  "we store X unwrapped because…", "anyone who can read localStorage can
  spend"), or
- gives a working recipe against the **live** system (endpoint + input +
  outcome), or
- reveals a security decision that an attacker can plan around (which check is
  skipped, which limit is not enforced, which key is held where).

Mark **fine** when it is a fixed bug described like a changelog entry, a test
name, generic hardening, or a design rule that is a strength rather than a gap
("the API never holds the guardian key").

Severity of a disclosure leak is about what an attacker gains *today*, so
check HEAD: if the described weakness is gone from the code, say "fixed since,
low" rather than escalating.
