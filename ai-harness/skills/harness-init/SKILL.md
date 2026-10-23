---
name: harness-init
description: Set up a project for the ai-harness by adding AGENTS.md and a CLAUDE.md that imports it. Use when the user says "init the harness", "add AGENTS.md", or starts a new AI app.
disable-model-invocation: true
---

# Harness init

The templates sit in `templates/` next to this file.

1. In the project root, check for an existing `AGENTS.md` or `CLAUDE.md`. If one exists, show the user what differs and merge on their yes; never overwrite.
2. Copy `templates/AGENTS.md` to `AGENTS.md` and `templates/CLAUDE.md` to `CLAUDE.md`.
3. Fill in the `Commands` and `Stack` sections from the repo (package.json, pyproject.toml, Makefile, lockfiles). Delete any line that does not apply. Leave `TODO` only where the repo cannot answer.
4. Keep `AGENTS.md` under 200 lines. Workflows that are only needed sometimes belong in a skill, not in this file.
