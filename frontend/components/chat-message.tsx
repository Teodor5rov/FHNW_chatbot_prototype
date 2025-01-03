import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { TypingIndicator } from "@/components/typing-indicator"

type Message = {
  content: string
  role: 'user' | 'assistant'
  animated: boolean
  isTyping: boolean
}

export function ChatMessage({ content, role, animated, isTyping }: Message) {
  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-2 sm:mb-4 ${animated ? 'animate-fade-in-up' : ''} min-w-0`}>
      <div className={`flex ${role === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start min-w-0`}>
        <Avatar className="w-8 h-8 shadow-sm">
          <AvatarFallback>{role === 'user' ? 'U' : 'A'}</AvatarFallback>
          <AvatarImage src={role === 'user' ? '' : '/Logo_FHNW.svg'} alt={role === 'user' ? 'User Avatar' : 'Assistant Avatar'} />
        </Avatar>
        <div className={`mx-2 sm:mx-4 px-4 py-2 rounded-md shadow-sm ${role === 'user' ? 'bg-primary text-primary-foreground ml-10 sm:ml-12' : 'bg-muted mr-10 sm:mr-12'} max-w-full min-w-0`}>
          {isTyping ? (
            <TypingIndicator />
          ) : role === 'user' ? (
            <p>{content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: (props) => <p className="mb-2 last:mb-0" {...props} />,
                ul: (props) => <ul className="list-disc pl-4 mb-2 last:mb-0" {...props} />,
                ol: (props) => <ol className="list-decimal pl-4 mb-2 last:mb-0" {...props} />,
                li: (props) => <li className="mb-1 last:mb-0" {...props} />,
                h1: (props) => <h1 className="text-2xl font-bold mb-2 last:mb-0" {...props} />,
                h2: (props) => <h2 className="text-xl font-bold mb-2 last:mb-0" {...props} />,
                h3: (props) => <h3 className="text-lg font-bold mb-2 last:mb-0" {...props} />,
                a: (props) => (
                  <a
                    className="text-blue-400 hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => {
                      e.preventDefault();
                      window.open(props.href, '_blank')?.focus();
                    }}
                    {...props}
                  />
                ),
                code: ({ inline, ...props }: { inline?: boolean } & React.HTMLProps<HTMLElement>) => (
                  inline
                    ? <code className="scrollable-container-horizontal border border-muted-foreground bg-secondary rounded-md p-1 sm:p-2 mb-2" {...props} />
                    : <pre className="scrollable-container-horizontal border border-muted-foreground bg-secondary rounded-md p-1 sm:p-2 mb-2 max-w-full overflow-x-auto"><code {...props} /></pre>
                ),
                table: (props) => <div className="scrollable-container-horizontal overflow-x-auto mb-2 last:mb-0"><table className="border-collapse table-auto m-2" {...props} /></div>,
                th: (props) => <th className="border border-muted-foreground p-1 sm:p-2 text-left text-lg" {...props} />,
                td: (props) => <td className="border border-muted-foreground p-1 sm:p-2" {...props} />,
                strong: (props) => <>{props.children}</>
              }}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  )
}

