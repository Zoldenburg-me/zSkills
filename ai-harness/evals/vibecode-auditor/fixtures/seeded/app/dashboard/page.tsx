import { supabase } from "@/lib/supabaseClient";

export default async function Dashboard() {
  const { data: docs } = await supabase.from("documents").select("id, title, owner_id");
  const rows = [];
  for (const doc of docs ?? []) {
    const { data: owner } = await supabase
      .from("profiles").select("email").eq("id", doc.owner_id).single();
    rows.push({ ...doc, ownerEmail: owner?.email });
  }
  return (
    <ul>
      {rows.map((r) => <li key={r.id}>{r.title} by {r.ownerEmail}</li>)}
    </ul>
  );
}
