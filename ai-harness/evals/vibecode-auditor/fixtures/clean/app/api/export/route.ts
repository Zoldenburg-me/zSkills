import { NextResponse } from "next/server";
import { z } from "zod";
import { requireUser } from "@/lib/supabase/server";

const Body = z.object({ docId: z.string().uuid() });

export async function POST(req: Request) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = Body.safeParse(await req.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request" }, { status: 400 });

  const { data, error } = await supabase
    .from("documents").select("title, content").eq("id", parsed.data.docId).eq("owner_id", user.id).single();
  if (error) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return new NextResponse(JSON.stringify(data), {
    headers: { "Content-Type": "application/json", "Content-Disposition": 'attachment; filename="document.json"' },
  });
}
