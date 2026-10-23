import { NextResponse } from "next/server";
import Stripe from "stripe";
import { requireUser } from "@/lib/supabase/server";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST() {
  const { user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const session = await stripe.checkout.sessions.create({
    mode: "payment",
    line_items: [{ price: process.env.STRIPE_PRO_PRICE_ID!, quantity: 1 }],
    client_reference_id: user.id,
    success_url: "https://promptly.app/success",
    cancel_url: "https://promptly.app/pricing",
  });
  return NextResponse.json({ url: session.url });
}
