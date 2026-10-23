"use client";
import { useState } from "react";

export default function Editor() {
  const [text, setText] = useState("");
  const [result, setResult] = useState("");

  async function improve() {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.NEXT_PUBLIC_OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o",
        messages: [{ role: "user", content: `Improve this text:\n${text}` }],
      }),
    });
    const data = await res.json();
    setResult(data.choices[0].message.content);
  }

  return (
    <div>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={improve}>Improve</button>
      <p>{result}</p>
    </div>
  );
}
