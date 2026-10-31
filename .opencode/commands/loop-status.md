---
description: Inspect active loop state, progress, failure signals, and recommended intervention.
---

Inspect active loop state, progress, and failure signals.

If you need to inspect a wedged or sibling session, run the packaged CLI from another terminal:

```bash
npx --package ecc-universal ecc loop-status --json
```

The CLI scans local Claude transcript JSONL files under `~/.claude/projects/**` and reports stale `ScheduleWakeup` calls or `Bash` tool calls that have no matching `tool_result`.

## Usage

`/loop-status [--watch]`

## What to Report

- active loop pattern
- current phase and last successful checkpoint
- failing checks (if any)
- estimated time/cost drift
- recommended intervention (continue/pause/stop)

## Arguments

$ARGUMENTS:
- `--watch` optional
