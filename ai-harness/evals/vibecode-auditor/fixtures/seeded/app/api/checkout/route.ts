import { NextResponse } from "next/server";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: Request) {
  const { amount, userId } = await req.json();
  const session = await stripe.checkout.sessions.create({
    mode: "payment",
    line_items: [{
      price_data: { currency: "usd", product_data: { name: "Promptly Pro" }, unit_amount: amount },
      quantity: 1,
    }],
    metadata: { user_id: userId },
    success_url: "https://promptly.app/success",
    cancel_url: "https://promptly.app/pricing",
  });
  return NextResponse.json({ url: session.url });
}
