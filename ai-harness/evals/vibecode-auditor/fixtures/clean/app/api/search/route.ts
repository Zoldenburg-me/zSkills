import { NextResponse } from "next/server";
import { requireUser } from "@/lib/supabase/server";

export async function GET(req: Request) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const q = (new URL(req.url).searchParams.get("q") ?? "").slice(0, 100);
  const { data, error } = await supabase
    .from("documents").select("id, title").eq("owner_id", user.id).ilike("title", `%${q}%`).limit(20);
  if (error) return NextResponse.json({ error: "Search failed" }, { status: 500 });
  return NextResponse.json(data);
}
