# vibecode-auditor eval

Measures how many planted flaws the auditor finds (recall) and how often it raises false alarms on clean code.

- `fixtures/seeded/`: a small Next.js + Supabase + Stripe + OpenAI app ("Promptly") with 20 planted flaws. All keys are fake.
- `fixtures/clean/`: the same app with every flaw fixed properly. It has no known flaws, so any Critical or High finding there is a false positive.
- `answer-key.json`: the planted flaws, their expected severity and the terms a finding must contain to count. Never let the auditor see this file.
- `grade.py`: scores two reports against the key. `python3 grade.py --self-test` checks the grader itself.
- `results/`: one folder per run with both reports and the score.

## Run it

1. Copy each fixture to its own folder outside this repo, both named `promptly`, so neither the folder name nor the answer key gives anything away.
2. Run `vibecode-auditor` on each and save the reports as `seeded.md` and `clean.md`.
3. Score them:

```bash
python3 grade.py answer-key.json results/<run>/seeded.md results/<run>/clean.md
```

Read `seeded_extra_findings` and `clean_false_positives_critical_high` by hand: an extra finding can be a real flaw the key doesn't list yet. If it is, add it to the key.

## Limits

- One small Next.js/Supabase app. It says nothing about Firebase, Convex, Python backends or large codebases.
- Matching is by keywords in the findings row, so a correct finding worded oddly can be missed. Check `missed` against the report before trusting a low score.
- No git history in the fixtures, so the "committed .env in history" check is only tested as a file in the tree.
- Results vary between runs; run it more than once before comparing two versions of the agent.
