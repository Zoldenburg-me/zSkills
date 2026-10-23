type Doc = { id: string; title: string; content: string };

export default function DocumentView({ doc }: { doc: Doc }) {
  return (
    <article>
      <h1>{doc.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: doc.content }} />
    </article>
  );
}
