import { NextResponse } from "next/server";
import { z } from "zod";
import { serverClient } from "@/lib/supabase/server";
import { authLimit, emailLimit } from "@/lib/ratelimit";

const Body = z.object({ email: z.string().email() });

export async function POST(req: Request) {
  // Vercel sets x-real-ip to the connecting client; it can't be supplied by the caller.
  const ip = req.headers.get("x-real-ip") ?? "unknown";
  const { success } = await authLimit.limit(ip);
  if (!success) return NextResponse.json({ error: "Too many requests" }, { status: 429 });

  const parsed = Body.safeParse(await req.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid email" }, { status: 400 });
  const perEmail = await emailLimit.limit(parsed.data.email.toLowerCase());
  if (!perEmail.success) return NextResponse.json({ ok: true });
  await serverClient().auth.resetPasswordForEmail(parsed.data.email);
  // Same answer whether or not the account exists.
  return NextResponse.json({ ok: true });
}
