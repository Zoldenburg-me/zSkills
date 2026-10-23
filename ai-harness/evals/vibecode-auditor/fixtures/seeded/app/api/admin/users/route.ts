import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseClient";

export async function DELETE(req: Request) {
  const { id } = await req.json();
  await supabase.auth.admin.deleteUser(id);
  return NextResponse.json({ ok: true });
}
