import { redirect } from "next/navigation";
import { requireUser } from "@/lib/supabase/server";
import DeleteUserForm from "./DeleteUserForm";

export default async function AdminPage() {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  const { data: profile } = await supabase.from("profiles").select("role").eq("id", user.id).single();
  if (profile?.role !== "admin") redirect("/");
  return <DeleteUserForm />;
}
