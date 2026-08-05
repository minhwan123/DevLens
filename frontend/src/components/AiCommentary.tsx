import ReactMarkdown from 'react-markdown'

export function AiCommentary({ commentary }: { commentary: string }) {
  return (
    <div className="ai-commentary">
      <ReactMarkdown>{commentary}</ReactMarkdown>
    </div>
  )
}
