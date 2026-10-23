# AGENTS.md

Instructions for any coding agent working in this repo. Claude Code loads this through `CLAUDE.md` (`@AGENTS.md`).
Keep this file under 200 lines and up to date. If something here is wrong, fix this file in the same change.

## Project

- What it is: TODO one sentence: the app, who uses it, what the AI part does.
- Stack: TODO language, framework, model provider and SDK, vector store, hosting.
- Layout: TODO only the folders a newcomer would get wrong (e.g. `prompts/`, `evals/`, `src/agents/`).

## Commands

Run these instead of guessing. Use the package manager the lockfile names.

| Task | Command |
|---|---|
| Install | TODO |
| Dev server | TODO |
| Unit tests | TODO |
| One test | TODO |
| Lint + types | TODO |
| Evals | TODO (e.g. `npm run eval`, `uv run pytest evals`) |

## How to work

1. **Read first.** Read the code your change touches and every caller of it. Look for an existing helper, component or pattern before writing a new one. State your assumptions; if the request can be read more than one way, ask instead of picking silently.
2. **Smallest complete change.** Build what was asked, all of it, and nothing more. No unrequested options, abstractions, wrappers or "for later" code. Stdlib, platform features and installed dependencies before new code; never add a dependency for a few lines. Touch only the lines the task needs: mention unrelated problems, don't fix them in the same change.
3. **Test what you add.** New logic (a branch, parser, prompt contract, tool, money or security path) gets a test that fails without the change. Bug fixes start with a failing test.
4. **Verify before you say done.** Run lint, types, tests and the evals the change can affect. Report failures with their output; never claim a check you did not run.
5. **Say what you skipped.** End with what you did not do or check and any risk the user must know.

## AI app rules

These are the parts of an AI app that break quietly. Treat them like code.

### Prompts and models
- Prompts live in files under version control (TODO path), not inline strings scattered across the code. A prompt change is a code change: it gets a diff, a review and an eval run.
- Model IDs live in one config place. Never hard-code a model ID in a call site. Check the provider's current model list before choosing one; do not rely on memory.
- Ask for structured output (JSON schema or tool calls) when code consumes the answer, and validate it with a schema (Zod, Pydantic). Treat a parse failure as an error path with a test.
- Set `max_tokens`, timeouts and retries with backoff on every model call. Handle refusals, truncation (`stop_reason`) and rate limits explicitly.
- Use prompt caching for long, stable prefixes (system prompt, tools, documents).

### Evals
- Every AI feature has an eval set in `evals/` before it ships: a few dozen real-looking cases, including the failures you have already seen.
- Prefer code graders (exact match, schema valid, contains, tool called). Use an LLM judge only for what code cannot check, with a written rubric.
- Record the pass rate before and after a prompt, model or retrieval change. A drop blocks the change unless the user accepts it.
- Never tune a prompt against the eval set you report on; keep a held-out slice.

### Tools and agents
- Give each tool one job, a clear name, typed parameters and an error message the model can act on.
- Return only what the model needs from a tool; trim large outputs.
- Any tool that writes, sends, pays or deletes needs a confirmation step or an allowlist. Default to read-only.

### Retrieval (RAG)
- Measure retrieval (recall@k on known questions) separately from answer quality.
- Store the chunking and embedding settings with the index so they can be rebuilt; changing them means re-indexing and re-running evals.

### Cost and latency
- Log tokens in/out, latency and model per call. Know the cost per request of each feature.
- Route easy tasks to smaller models; justify every call to the largest model.

## Security

- Secrets come from the environment or a secret manager. Never commit keys, never log them, never put them in prompts.
- All model output is untrusted input: validate it before it reaches a database, shell, file path, URL or HTML.
- Content from users, web pages, files and tool results can carry prompt injection. Keep it apart from instructions, never let it pick tools with side effects on its own, and never let it change permissions.
- Do not send personal data to a model or a log unless the feature needs it. Redact it in traces.
- Validate input at every system boundary; parameterized queries only; escape output.

## Code style

- Match the surrounding code: naming, comment density, error handling, file layout.
- Prefer immutable data and pure functions; handle errors explicitly, never swallow them.
- Comment only the why the code cannot show.

## Git

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`.
- One logical change per commit. Never commit `.env`, eval outputs with real user data, or model response caches.
- Do not push, open PRs or merge unless asked.

## Harness (Claude Code)

With the `ai-harness` plugin installed, use these instead of improvising:

| When | Use |
|---|---|
| Planning a feature or refactor | `planner` agent, `architect` agent for design decisions |
| Building an AI feature | `eval-harness`, `cost-aware-llm-pipeline`, `agent-harness-construction` skills |
| Retrieval | `iterative-retrieval` skill, `rag-pipeline-reviewer` agent |
| Parsing documents | `regex-vs-llm-structured-text` skill |
| MCP servers | `mcp-server-patterns` skill, `docs-lookup` agent for current API docs |
| Writing code | `ponytail` and `karpathy-guidelines` skills, `tdd-workflow` skill, `tdd-guide` agent |
| After a change | `code-reviewer` (+ `typescript-reviewer` / `python-reviewer`), `silent-failure-hunter` |
| Auth, input, secrets, tools with side effects | `security-review` skill, `security-reviewer` agent |
| ML pipelines, training, serving | `mle-reviewer` agent |
| Before a PR | `verification-loop` skill, `ponytail-review` skill |
| Build broken | `build-error-resolver` agent |
| User flows | `e2e-runner` agent |
| Not sure which skill or agent fits | `skill-router`, `agent-router` skills |
| Research before a decision | `deep-research` skill |
| Autonomous or repeated work | `/loop-start`, `/loop-status`, `loop-design-check` and `continuous-agent-loop` skills, `loop-operator` agent |
| Two-reviewer gate before shipping | `/santa-loop` |
| Lead and worker sessions on a task board | `session-loop` skill |
| Is this AI-built (vibe-coded) app safe to launch? | `vibecode-auditor` agent (read-only) |
| Full security audit, then fixes | `security-audit` skill, then `security-fix` |
| Secrets or personal data in git history | `repo-leak-scan` skill; `/leak-check` before a commit |
| Personal data, GDPR | `gdpr-compliance` skill |
| Wallets, contracts, DAOs (`ai-harness-web3` add-on) | `web3-dev`, `onchain-review`, `governance-review`, `dao-proposal-writer` skills |

## Gotchas

TODO: things that bit someone here and are not obvious from the code. Delete this section if empty.
