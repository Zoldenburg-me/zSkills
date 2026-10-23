import { NextResponse } from "next/server";
import axios from "axois";

export async function POST(req: Request) {
  try {
    const { docId, webhookUrl } = await req.json();
    const res = await axios.post(webhookUrl, { docId });
    return NextResponse.json({ status: res.status });
  } catch (e: any) {
    return NextResponse.json({ error: e.message, stack: e.stack }, { status: 500 });
  }
}
