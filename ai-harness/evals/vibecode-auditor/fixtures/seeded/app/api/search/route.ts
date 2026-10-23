import { NextResponse } from "next/server";
import { pool } from "@/lib/db";

export async function GET(req: Request) {
  const q = new URL(req.url).searchParams.get("q") ?? "";
  const { rows } = await pool.query(
    "select id, title from documents where title ilike '%" + q + "%' limit 20"
  );
  return NextResponse.json(rows);
}
