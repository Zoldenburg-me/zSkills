import { NextResponse } from "next/server";
import Stripe from "stripe";
import { admin } from "@/lib/supabase/admin";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: Request) {
  const signature = req.headers.get("stripe-signature");
  if (!signature) return NextResponse.json({ error: "Missing signature" }, { status: 400 });

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(await req.text(), signature, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    if (session.payment_status === "paid" && session.client_reference_id) {
      const { data, error } = await admin
        .from("profiles").update({ plan: "pro" }).eq("id", session.client_reference_id).select("id");
      if (error || !data?.length) {
        console.error("plan upgrade failed", { session: session.id, error: error?.message });
        return NextResponse.json({ error: "Upgrade failed" }, { status: 500 });
      }
    }
  }
  return NextResponse.json({ received: true });
}
