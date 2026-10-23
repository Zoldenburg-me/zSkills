"use client";
import { useState } from "react";

export default function DeleteUserForm() {
  const [id, setId] = useState("");
  const [status, setStatus] = useState("");

  async function submit() {
    if (!confirm(`Delete user ${id}? This cannot be undone.`)) return;
    const res = await fetch("/api/admin/users", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    setStatus(res.ok ? "Deleted." : "Failed.");
  }

  return (
    <div>
      <label>User id <input value={id} onChange={(e) => setId(e.target.value)} /></label>
      <button onClick={submit} disabled={!id}>Delete user</button>
      <p role="status">{status}</p>
    </div>
  );
}
