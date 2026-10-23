import { NextResponse } from "next/server";
import { requireUser } from "@/lib/supabase/server";

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const { data, error } = await supabase
    .from("documents")
    .select("id, title, content, created_at")
    .eq("id", params.id)
    .eq("owner_id", user.id)
    .single();
  if (error) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(data);
}
