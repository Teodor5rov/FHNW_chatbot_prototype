'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ArrowUp, Loader2 } from 'lucide-react'
import { Card } from "@/components/ui/card"

interface ChatInputProps {
  onSubmit: (input: string) => void
  isLoading: boolean
}

export function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { 
      e.preventDefault()
      handleSubmit(e as React.FormEvent)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    onSubmit(input)
    setInput('')
  }

  return (
    <div className="bg-background border-t p-2 sm:p-4">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit}>
          <Card className="relative bg-secondary rounded-md">
            <Textarea
              ref={textareaRef}
              placeholder="Type your question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="max-h-64 resize-none pb-12"
              rows={1}
              aria-label="Chat input"
            />
            <div className="absolute bottom-0 pointer-events-none bg-secondary min-w-full h-12 rounded-b-md" aria-hidden="true"/>
            <Button type="submit" disabled={isLoading} size="icon" aria-label="Send message" className="absolute bottom-2 right-2">
              {isLoading ? <Loader2 className="animate-spin" /> : <ArrowUp className='aspect-square' />}
            </Button>
          </Card>
        </form>
      </div>
    </div>
  )
}

