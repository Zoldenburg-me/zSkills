import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseClient";

export async function POST(req: Request) {
  const { email } = await req.json();
  const { data } = await supabase.from("profiles").select("id").eq("email", email).single();
  if (!data) return NextResponse.json({ error: "No account with that email" }, { status: 404 });
  await supabase.auth.resetPasswordForEmail(email);
  return NextResponse.json({ ok: true });
}
