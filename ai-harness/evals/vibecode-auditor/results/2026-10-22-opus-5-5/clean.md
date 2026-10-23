## Verdict
Safe to launch: no. The security posture is good, but the product cannot be used as shipped. Fix the Medium items first (sign-up/login pages, mounting the editor, the Next.js upgrade).

## Findings
| # | Severity | Finding | Where | Evidence | Fix |
|---|----------|---------|-------|----------|-----|
| 1 | Medium | Sign-up and login pages are missing | app/page.tsx:6, app/dashboard/page.tsx:6, app/admin/page.tsx:7 | `<a href="/signup">`, `redirect("/login")`, no app/signup or app/login | Add Supabase Auth pages |
| 2 | Medium | The core feature is never rendered: Editor, DocumentView and the browser client are unused, and nothing creates documents | components/Editor.tsx:4, components/DocumentView.tsx:3, lib/supabase/browser.ts:3 | no imports | Mount Editor, add create/view flow, or delete |
| 3 | Medium | Next.js 14.2.5 is behind published security fixes (CVE-2025-29927, CVE-2024-46982); limited impact here | package.json:9 | `"next": "14.2.5"` | Upgrade to latest 14.2.x, run npm audit |
| 4 | Medium | No tests at all | whole repo | no test files or script | Add route tests |
| 5 | Medium | No lockfile; caret ranges | package.json:5-16 | no lockfile | Commit a lockfile, use npm ci |
| 6 | Low | Reset IP limit depends on `x-real-ip`; shared "unknown" bucket off Vercel | app/api/auth/reset/route.ts:9-11 | `req.headers.get("x-real-ip") ?? "unknown"` | Use verified client IP; skip IP limit when unknown |
| 7 | Low | Pro is never revoked on refund or dispute | app/api/checkout/route.ts:11, app/api/stripe/webhook/route.ts:18 | only `checkout.session.completed` handled | Handle refunds/disputes |
| 8 | Low | Malformed JSON bodies return a raw 500 | app/api/generate/route.ts:17 and others | `await req.json()` outside try | `.catch(() => null)` then Zod 400 |
| 9 | Low | Editor stuck on "Improving…" on network error | components/Editor.tsx:13-18 | no try/finally | try/catch/finally |
| 10 | Low | Admin can delete themselves; no audit log | app/api/admin/users/route.ts:16 | no self check | Reject own id, log deletions |
| 11 | Low | No security headers; no privacy or terms pages | next.config.js:1, app/page.tsx:5 | `module.exports = {};` | Add headers() and the pages |
