'use client'

import { useRef, useEffect, useState } from 'react'
import { ChatMessage } from "@/components/chat-message"

type Message = {
  content: string
  role: 'user' | 'assistant'
  animated: boolean
  isTyping: boolean
}

interface ChatProps {
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  isSimulatedMessage: boolean
}

export function Chat({ messages, isLoading, isStreaming, isSimulatedMessage }: ChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showLoadingMessage, setShowLoadingMessage] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, showLoadingMessage])

  useEffect(() => {
    if (isLoading && !isStreaming && !isSimulatedMessage) {
      const timer = setTimeout(() => setShowLoadingMessage(true), 400)
      return () => clearTimeout(timer)
    } else {
      setShowLoadingMessage(false)
    }
  }, [isLoading, isStreaming, isSimulatedMessage])

  return (
    <div className="scrollable-container flex flex-col h-full w-full relative overflow-y-auto overflow-x-hidden px-2 sm:px-4">
      <div className="w-full max-w-4xl mx-auto mt-2 sm:mt-4">
        {messages.map((message, index) => (
          <ChatMessage key={index} content={message.content} role={message.role} animated={message.animated} isTyping={message.isTyping} />
        ))}
        {showLoadingMessage && (
          <ChatMessage content="..." role="assistant" animated={true} isTyping={true} />
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

