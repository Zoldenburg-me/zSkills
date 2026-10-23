import { redirect } from "next/navigation";
import { requireUser } from "@/lib/supabase/server";

export default async function Dashboard() {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  const { data: docs, error } = await supabase
    .from("documents").select("id, title").eq("owner_id", user.id).order("created_at", { ascending: false });
  if (error) return <p role="alert">Could not load your documents.</p>;
  if (!docs?.length) return <p>No documents yet. Create your first one.</p>;
  return (
    <ul>
      {docs.map((d) => <li key={d.id}>{d.title}</li>)}
    </ul>
  );
}
