# Run 2026-10-22, vibecode-auditor on Opus 5.5

How it ran: the agent's prompt was given to a general-purpose subagent on Opus (the plugin isn't installed yet), read-only, offline, one run per fixture.

| Measure | Result |
|---|---|
| Recall, all flaws | 21/21 (20 planted + 1 real flaw the auditor found that the key now lists, F21) |
| Recall by level | Critical 6/6 · High 10/10 · Medium 3/3 · Low 2/2 |
| Severity within one level of the key | 21/21 |
| Extra findings on the seeded app | 3, all reasonable (no input validation, no tests, Editor error handling) |
| False positives on the clean app (Critical/High) | 0 |
| Clean-app Medium/Low findings | 11, all real gaps of a partial app (no login pages, no tests, no lockfile, Next.js patch level) |

## What changed during the run
- The first clean control was incomplete (no root layout or tsconfig, no profile-creation trigger, plan never enforced). The auditor rightly rated those High. The control was completed and re-audited; the first report is kept as `clean-v1-incomplete-fixture.md`.
- F03, F04 and F06 were matching the wrong report rows; their terms were tightened and the grader now prefers rows no other flaw has claimed.

## Observations
- The verdict on the clean app said "no" with zero Critical/High findings. Fixed in the next run (`../2026-10-22-verdict-rule`).
- The fixture is small and every flaw is textbook. A perfect score here is the floor, not proof of quality on real apps.
