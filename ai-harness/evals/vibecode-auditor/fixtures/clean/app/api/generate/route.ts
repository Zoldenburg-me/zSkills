import { NextResponse } from "next/server";
import { z } from "zod";
import { requireUser } from "@/lib/supabase/server";
import { aiLimit } from "@/lib/ratelimit";
import { openai, MODEL, MAX_TOKENS } from "@/lib/ai";

const Body = z.object({ prompt: z.string().min(1).max(4000) });

export async function POST(req: Request) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const { data: profile } = await supabase.from("profiles").select("plan").eq("id", user.id).single();
  const limiter = profile?.plan === "pro" ? aiLimit.pro : aiLimit.free;
  const { success } = await limiter.limit(user.id);
  if (!success) return NextResponse.json({ error: "Too many requests" }, { status: 429 });

  const parsed = Body.safeParse(await req.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request" }, { status: 400 });

  try {
    const completion = await openai.chat.completions.create({
      model: MODEL,
      max_tokens: MAX_TOKENS,
      messages: [
        { role: "system", content: "Improve the user's text. Return only the improved text." },
        { role: "user", content: parsed.data.prompt },
      ],
    });
    return NextResponse.json({ text: completion.choices[0]?.message.content ?? "" });
  } catch (e) {
    console.error("generate failed", { userId: user.id, error: (e as Error).message });
    return NextResponse.json({ error: "Generation failed" }, { status: 502 });
  }
}
