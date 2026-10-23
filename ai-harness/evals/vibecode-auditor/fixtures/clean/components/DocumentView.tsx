type Doc = { id: string; title: string; content: string };

export default function DocumentView({ doc }: { doc: Doc }) {
  return (
    <article>
      <h1>{doc.title}</h1>
      <div style={{ whiteSpace: "pre-wrap" }}>{doc.content}</div>
    </article>
  );
}
