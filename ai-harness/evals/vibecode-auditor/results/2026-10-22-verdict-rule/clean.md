## Verdict
Safe to launch: yes
TL;DR: The security basics are done right. Every API route checks the caller on the server and filters records by `owner_id`. RLS is on for both tables, with `auth.uid()` policies and no update policy on `profiles`, so users cannot make themselves admin or pro. The Stripe webhook verifies its signature, and the AI endpoint has auth, a per-user rate limit and `max_tokens`. The main remaining risks are an outdated Next.js and the lack of any tests. Note that the app is not usable yet: `/login`, `/signup`, `/pricing` and `/success` are linked but do not exist, `Editor` and `DocumentView` are never mounted, and there is no way to create a document.

## Findings
| # | Severity | Finding | Where | Evidence | Fix |
|---|----------|---------|-------|----------|-----|
| 1 | Medium | Next.js pinned to an old patch with published advisories (middleware bypass fixed 14.2.25, cache poisoning 14.2.10, image DoS 14.2.7); harmless today because routes check auth themselves | package.json:10 | `"next": "14.2.5"` | Upgrade to latest 14.2.x, run npm audit |
| 2 | Medium | No tests at all on admin deletion, webhook upgrade or owner checks | whole repo | scripts are only dev/build/start | Add route tests |
| 3 | Low | Reset rate limit keys on `x-real-ip`, trusted only on Vercel; shared "unknown" bucket otherwise | app/api/auth/reset/route.ts:10 | `req.headers.get("x-real-ip") ?? "unknown"` | Confirm Vercel or use the host's trusted header |
| 4 | Low | AI spend capped per user but no global or monthly cap | lib/ratelimit.ts:7-8; app/api/generate/route.ts:14 | `limiter.limit(user.id)` | Global daily limiter, OpenAI spend limit |
| 5 | Low | Direct document inserts via anon key with no size or count limit | supabase/migrations/001_init.sql:12,23 | `content text not null` | Length check, per-user cap |
| 6 | Low | Editor stuck on "Improving…" on network error | components/Editor.tsx:13-18 | no try/catch | try/catch/finally |
| 7 | Low | App not usable yet: linked pages missing, components unused, no create flow | app/page.tsx:6; app/admin/page.tsx:7 | `href="/signup"`, `redirect("/login")` | Build the pages |
| 8 | Low | "Documents stay private" while sending text to OpenAI; no privacy policy or terms | app/page.tsx:5; app/api/generate/route.ts:26 | text passed to OpenAI | Privacy policy naming OpenAI, terms |
| 9 | Low | Async payments never upgrade; pro users can pay again | app/api/stripe/webhook/route.ts:18-20; app/api/checkout/route.ts:7-16 | no async handler, no plan check | Handle async event; refuse checkout for pro |
