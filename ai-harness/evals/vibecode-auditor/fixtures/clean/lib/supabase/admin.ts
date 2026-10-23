import "server-only";
import { createClient } from "@supabase/supabase-js";

// Bypasses RLS: only for webhooks and admin routes that check the caller first.
export const admin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);
