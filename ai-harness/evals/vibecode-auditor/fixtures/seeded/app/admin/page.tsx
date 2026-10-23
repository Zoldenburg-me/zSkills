"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";

export default function AdminPage() {
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getUser().then(async ({ data }) => {
      const { data: profile } = await supabase
        .from("profiles").select("role").eq("id", data.user?.id).single();
      setRole(profile?.role ?? null);
    });
  }, []);

  async function deleteUser(id: string) {
    await fetch("/api/admin/users", { method: "DELETE", body: JSON.stringify({ id }) });
  }

  if (role !== "admin") return <p>Not allowed</p>;
  return <button onClick={() => deleteUser(prompt("User id") ?? "")}>Delete user</button>;
}
