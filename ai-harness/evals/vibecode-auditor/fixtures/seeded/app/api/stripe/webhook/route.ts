import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseClient";

export async function POST(req: Request) {
  const event = JSON.parse(await req.text());
  if (event.type === "checkout.session.completed") {
    const userId = event.data.object.metadata.user_id;
    await supabase.from("profiles").update({ plan: "pro" }).eq("id", userId);
  }
  return NextResponse.json({ received: true });
}
