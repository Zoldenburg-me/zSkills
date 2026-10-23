## Verdict
Safe to launch: after fixing the High findings. No Critical findings.
TL;DR: The security basics hold up. Every API route checks the caller and the record owner, RLS is on with `auth.uid()` policies, the Stripe webhook verifies its signature, and the AI route has auth, a per-user rate limit and `max_tokens`. What fails is the plumbing. The project as shipped will not build (no root layout, no tsconfig for the `@/` imports). Nothing ever creates a `profiles` row, so documents can't be saved, paid upgrades silently do nothing and admin deletes fail. And the "pro" plan people pay for is never checked anywhere.

## Findings
| # | Severity | Finding | Where | Evidence | Fix |
|---|----------|---------|-------|----------|-----|
| 1 | High | Nothing creates a profile row, so core flows break. Document inserts fail on the foreign key and paid upgrades update 0 rows silently | supabase/migrations/001_init.sql:1-10; app/api/stripe/webhook/route.ts:21 | `owner_id uuid not null references public.profiles(id)`; no insert into `profiles`, no trigger on `auth.users` | Add an `on insert on auth.users` trigger that inserts into `public.profiles`; check the webhook update's row count |
| 2 | High | Users pay for "pro" and get nothing: `plan` is written but never read | app/api/stripe/webhook/route.ts:21; app/api/generate/route.ts:12; lib/ratelimit.ts:6 | `plan` only appears in the webhook update; `aiLimit` is a flat 20/h | Read `profiles.plan` in /api/generate and apply a per-plan limit |
| 3 | High | The project will not build: no `app/layout.tsx`, no `tsconfig.json` for the `@/` alias, no lockfile | app/; project root; app/api/generate/route.ts:3 | `ls app` has no layout.tsx; imports `from "@/lib/supabase/server"` | Add a root layout, a tsconfig with `"paths": {"@/*": ["./*"]}`, and a lockfile |
| 4 | Medium | Admin delete-user fails for users with a profile or documents (no `on delete cascade`) | supabase/migrations/001_init.sql:2,10; app/api/admin/users/route.ts:16-17 | FKs without cascade | Add `on delete cascade` or delete rows first |
| 5 | Medium | No middleware refreshes the Supabase session; `setAll` has no try/catch | lib/supabase/server.ts:10; no middleware.ts | `setAll: (all) => all.forEach(...)` | Add the standard Supabase middleware and wrap `setAll` |
| 6 | Medium | A second database path skips RLS (raw `pg` pool); per-instance Pool on serverless | lib/db.ts:4; app/api/search/route.ts:9-12 | `new Pool({ connectionString: process.env.DATABASE_URL })` | Use the RLS-bound client, or a pooled non-superuser connection |
| 7 | Medium | Reset rate limit per IP only, via spoofable `x-forwarded-for`; no per-email limit | app/api/auth/reset/route.ts:9-10 | `req.headers.get("x-forwarded-for")...?? "unknown"` | Also limit per email; use the platform's trusted IP |
| 8 | Medium | No tests at all | whole project | No test files or runner | Add tests for owner checks, admin 403, webhook, rate limit |
| 9 | Medium | Next.js 14.2.5 is behind 14.2.x security patches (unconfirmed, offline) | package.json:9 | `"next": "14.2.5"` | Upgrade to latest 14.2.x and run npm audit |
| 10 | Low | Login and sign-up pages don't exist | app/page.tsx:6; app/dashboard/page.tsx:6 | `<a href="/signup">`, `redirect("/login")` | Add auth pages |
| 11 | Low | Dead code: Editor, DocumentView and the browser client are never imported | components/Editor.tsx:4; components/DocumentView.tsx:3 | no imports | Wire them in or delete |
| 12 | Low | Network error leaves the Editor stuck on "Improving…" | components/Editor.tsx:13-20 | no try/catch | try/catch/finally |
| 13 | Low | Async payments (e.g. SEPA) never upgrade the user | app/api/stripe/webhook/route.ts:18-20 | only `checkout.session.completed` handled | Also handle `async_payment_succeeded` |
| 14 | Low | Hardcoded production URLs in checkout; no rate limit on checkout sessions | app/api/checkout/route.ts:14-15 | `success_url: "https://promptly.app/success"` | Read base URL from env |
| 15 | Low | No privacy policy or terms although user text goes to OpenAI | app/page.tsx:5 | no /privacy or /terms | Add both, name OpenAI as processor |
