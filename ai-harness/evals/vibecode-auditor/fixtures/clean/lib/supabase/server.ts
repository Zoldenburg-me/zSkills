import "server-only";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

export function serverClient() {
  const store = cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => store.getAll(),
        setAll: (all) => {
          // Server Components can't set cookies; middleware.ts refreshes the session instead.
          try { all.forEach((c) => store.set(c.name, c.value, c.options)); } catch {}
        },
      },
    }
  );
}

export async function requireUser() {
  const supabase = serverClient();
  const { data: { user } } = await supabase.auth.getUser();
  return { supabase, user };
}
