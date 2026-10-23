import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseClient";

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const { data, error } = await supabase
    .from("documents")
    .select("*")
    .eq("id", params.id)
    .single();
  if (error) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(data);
}
