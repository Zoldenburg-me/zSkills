---
description: Adversarial dual-review convergence loop — two independent model reviewers must both approve before code ships.
---

Adversarial dual-review convergence loop using the santa-method skill. Two independent reviewers — different models, no shared context — must both return NICE before code ships.

## Purpose

Run two independent reviewers (Claude Opus + an external model) against the current task output. Both must return NICE before the code is pushed. If either returns NAUGHTY, fix all flagged issues, commit, and re-run fresh reviewers — up to 3 rounds.

## Usage

```
/santa-loop [file-or-glob | description]
```

## Workflow

### Step 1: Identify What to Review

Determine the scope from `$ARGUMENTS` or fall back to uncommitted changes:

```bash
git diff --name-only HEAD
```

Read all changed files to build the full review context. If `$ARGUMENTS` specifies a path, file, or description, use that as the scope instead.

### Step 2: Build the Rubric

Construct a rubric appropriate to the file types under review. Every criterion must have an objective PASS/FAIL condition. Include at minimum:

| Criterion | Pass Condition |
|-----------|---------------|
| Correctness | Logic is sound, no bugs, handles edge cases |
| Security | No secrets, injection, XSS, or OWASP Top 10 issues |
| Error handling | Errors handled explicitly, no silent swallowing |
| Completeness | All requirements addressed, no missing cases |
| Internal consistency | No contradictions between files or sections |
| No regressions | Changes don't break existing behavior |

Add domain-specific criteria based on file types.

### Step 3: Dual Independent Review

Launch two reviewers **in parallel**. Both must complete before proceeding to the verdict gate.

Each reviewer evaluates every rubric criterion as PASS or FAIL, then returns structured JSON:

```json
{
  "verdict": "PASS" | "FAIL",
  "checks": [
    {"criterion": "...", "result": "PASS|FAIL", "detail": "..."}
  ],
  "critical_issues": ["..."],
  "suggestions": ["..."]
}
```

The verdict gate maps these to NICE/NAUGHTY: both PASS → NICE, either FAIL → NAUGHTY.

#### Reviewer A: Claude Agent (always runs)

Launch an Agent (subagent_type: `code-reviewer`, model: `opus`) with the full rubric + all files under review. The prompt must include:
- The complete rubric
- All file contents under review
- "You are an independent quality reviewer. You have NOT seen any other review."
- Return the structured JSON verdict above

#### Reviewer B: External Model (Claude fallback if no external reviewer is ready)

Run detection, prompt creation, and the selected external review together in a single Bash subshell.

```bash
(
  set -e
  set -o pipefail

  REVIEWER_WRAPPER="$HOME/.claude/bin/codeagent-wrapper"
  REVIEWER_ROLE="$HOME/.claude/.ccg/prompts/antigravity/reviewer.md"
  if command -v codex >/dev/null 2>&1; then
    REVIEWER_BACKEND=codex
  elif command -v gemini >/dev/null 2>&1; then
    REVIEWER_BACKEND=gemini
  elif [ -x "$REVIEWER_WRAPPER" ] && [ -f "$REVIEWER_ROLE" ] && [ -r "$REVIEWER_ROLE" ]; then
    REVIEWER_BACKEND=antigravity
  else
    printf '%s\n' 'CLAUDE_FALLBACK'
    exit 0
  fi

  umask 077
  PROMPT_FILE=$(mktemp "${TMPDIR:-/tmp}/santa-reviewer-b.XXXXXX")
  cat > "$PROMPT_FILE" << 'EOF'
... full rubric + file contents + reviewer instructions ...
EOF

  case "$REVIEWER_BACKEND" in
    codex)
      codex exec --sandbox read-only -m gpt-5.4 -C "$(pwd)" - < "$PROMPT_FILE"
      ;;
    gemini)
      REVIEWER_PROMPT=$(cat "$PROMPT_FILE")
      gemini -p "$REVIEWER_PROMPT" -m gemini-2.5-pro
      ;;
    antigravity)
      {
        printf 'ROLE_FILE: %s\n' "$REVIEWER_ROLE"
        cat "$PROMPT_FILE"
      } | "$REVIEWER_WRAPPER" --backend antigravity - "$PWD"
      ;;
  esac
  rm -f "$PROMPT_FILE"
)
```

If the subshell prints `CLAUDE_FALLBACK`, launch a second Claude Agent with the rubric and file contents directly.

### Step 4: Verdict Gate

- **Both PASS** → **NICE** — proceed to push
- **Either FAIL** → **NAUGHTY** — merge all critical issues, deduplicate, proceed to fix cycle

### Step 5: Fix Cycle (NAUGHTY path)

1. Display all critical issues from both reviewers
2. Fix every flagged issue
3. Commit all fixes:
   ```
   fix: address santa-loop review findings (round N)
   ```
4. Re-run Step 3 with fresh reviewers
5. Repeat until both return PASS (max 3 iterations)

### Step 6: Push (NICE path)

```bash
git push -u origin HEAD
```

### Step 7: Final Report

```
SANTA VERDICT: [NICE / NAUGHTY (escalated)]

Reviewer A (Claude Opus):   [PASS/FAIL]
Reviewer B ([model used]):  [PASS/FAIL]

Agreement:
  Both flagged:      [issues caught by both]
  Reviewer A only:   [issues only A caught]
  Reviewer B only:   [issues only B caught]

Iterations: [N]/3
Result:     [PUSHED / ESCALATED TO USER]
```
