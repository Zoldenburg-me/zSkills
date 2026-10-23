"use client";
import { useState } from "react";

export default function Editor() {
  const [text, setText] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function improve() {
    setLoading(true);
    setError("");
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: text }),
    });
    setLoading(false);
    if (!res.ok) return setError(res.status === 429 ? "Too many requests, try again later." : "Something went wrong.");
    setResult((await res.json()).text);
  }

  return (
    <div>
      <textarea value={text} onChange={(e) => setText(e.target.value)} maxLength={4000} />
      <button onClick={improve} disabled={loading || !text}>{loading ? "Improving…" : "Improve"}</button>
      {error && <p role="alert">{error}</p>}
      <p>{result}</p>
    </div>
  );
}
