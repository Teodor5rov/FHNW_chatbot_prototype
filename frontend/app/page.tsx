'use client'

import { useState, useEffect, useRef } from 'react'
import { Chat } from '@/components/chat'
import { ChatInput } from '@/components/chat-input'
import { ModeToggle } from '@/components/theme-select'
import { Button } from "@/components/ui/button"

type Message = {
  content: string
  role: 'user' | 'assistant'
  animated: boolean
  isTyping: boolean
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [openingMessageShown, setOpeningMessageShown] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false);
  const [isSimulatedMessage, setIsSimulatedMessage] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!openingMessageShown) {
      simulateStreamingMessage("Welcome to FHNW! I'm your chatbot assistant, and I'm here to help answer any questions you may have about our university. Feel free to ask me about our programs, services, or research opportunities. How can I assist you today?")
      setOpeningMessageShown(true)
    }
  }, [openingMessageShown])

  const simulateStreamingMessage = async (message: string) => {
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsLoading(true);
    setIsSimulatedMessage(true);
    let streamedMessage = ''
    const words = message.split(' ')
    for (let i = 0; i < words.length; i++) {
      if (abortController.signal.aborted) return;
      const word = words[i]
      for (let j = 0; j < word.length; j += 5) {
        if (abortController.signal.aborted) return;
        const portion = word.slice(j, j + 5)
        streamedMessage += (j === 0 && i !== 0 ? ' ' : '') + portion
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant') {
            return [
              ...prev.slice(0, -1),
              { role: 'assistant', content: streamedMessage, animated: false, isTyping: false },
            ];
          } else {
            return [
              ...prev,
              { role: 'assistant', content: streamedMessage, animated: true, isTyping: false },
            ];
          }
        });
        await new Promise(resolve => setTimeout(resolve, 25))
      }
    }
    setIsLoading(false);
    setIsSimulatedMessage(false);
  }

  const handleSubmit = async (input: string) => {
    const userMessage: Message = { role: 'user', content: input, animated: true, isTyping: false }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setIsLoading(true);
    setIsStreaming(false);
    setIsSimulatedMessage(false);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages: updatedMessages }),
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Failed to get response reader')
      }

      let assistantMessage = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split('\n\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              break
            }
            try {
              const parsed = JSON.parse(data)
              assistantMessage += parsed.text
              if (!isStreaming) {
                setIsStreaming(true)
              }
              setMessages(prev => {
                const newMessages = [...prev]
                if (newMessages[newMessages.length - 1].role === 'assistant') {
                  newMessages[newMessages.length - 1].content = assistantMessage
                } else {
                  newMessages.push({ role: 'assistant', content: assistantMessage, animated: false, isTyping: false })
                }
                return newMessages
              })
            } catch (error) {
              console.error('Error parsing JSON:', error)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error)
      simulateStreamingMessage('Sorry, an error occurred. Please try again.')
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
    }
  };

  const handleNewChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
    setOpeningMessageShown(false);
    setIsLoading(false);
    setIsStreaming(false);
    setIsSimulatedMessage(false);
  };

  return (
    <div className="flex flex-col h-dvh">
      <header className="grid grid-cols-2 items-center p-2 sm:p-4 border-b">
        <div className="flex items-center space-x-2 sm:space-x-4">
          <div className="relative sm:h-8 h-7 flex-none aspect-[300/178] mx-2">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 178" className="absolute w-full h-full object-contain fill-foreground" preserveAspectRatio="xMidYMid meet">
              <g transform="matrix(1.25,0,0,-1.25,-113.38625,205.90166)" id="g12">
                  <path d="m 195.21518,164.66451 -4.86892,0 0,-142.286363 4.86892,0 0,142.286363 z" id="path712"/>
                  <path d="m 117.17296,117.364 c 2.30898,3.26268 7.60735,13.44113 23.07861,13.44113 10.89791,0 16.69265,-4.34466 18.99603,-6.51421 6.65366,-6.51978 7.06078,-15.88396 7.06078,-21.17675 l 0,-45.147701 -27.95866,0 0,39.682009 c 0,0.80312 -0.13398,10.078062 -9.50359,10.078062 -9.91076,0 -10.17288,-9.102047 -10.17288,-11.539297 l 0,-38.220774 -27.964252,0 0,71.076251 26.463962,0 0,-11.67872 z" id="path716"/>
                  <path d="m 319.29745,130.67128 c -5.2426,0 -9.49245,-4.24985 -9.49245,-9.48688 0,-5.23702 4.24985,-9.48687 9.49245,-9.48687 4.802,0 6.92692,3.46347 6.98269,3.29057 2.71612,-8.28777 -11.68987,-51.271502 -31.37751,-51.271502 -6.3692,0 -8.34911,5.15894 -8.34911,11.834887 0,7.891785 2.2811,15.939731 5.16451,26.865535 3.0396,10.78079 5.76686,21.09867 7.29502,26.62571 l -18.97374,0 c -2.58784,-9.31956 -21.15444,-63.95971 -36.88781,-63.95971 -1.97433,0 -4.10484,2.124924 -4.10484,5.917444 0,2.119348 1.82374,9.564954 2.73841,12.292218 l 6.21305,21.249258 c 1.3664,4.40602 3.34076,10.16172 3.34076,14.41715 0,7.44003 -5.15893,11.68988 -11.22698,11.68988 -17.14998,0 -24.28326,-15.33181 -27.78019,-21.55043 l 2.889,-1.82375 c 1.66761,2.72727 9.2582,15.6274 14.41716,15.6274 0.76408,0 1.37198,-0.90909 1.37198,-3.63635 0,-1.82376 -1.05966,-5.91745 -2.13048,-9.71554 l -6.52538,-21.544857 c -1.06524,-3.954259 -3.6475,-11.544872 -3.6475,-17.004982 0,-10.016708 7.59062,-15.025065 14.26657,-15.025065 24.33904,0 34.91346,29.447787 38.4048,37.941913 l 0.30119,-0.301171 c -0.45734,-1.67317 -2.5767,-10.624627 -2.5767,-15.181226 0,-13.050725 5.82822,-22.459516 18.57777,-22.459516 36.94917,0 57.12202,74.695884 31.61733,74.695884" id="path720"/>
              </g>
            </svg>
          </div>
          <Button onClick={handleNewChat} variant="outline">New Chat</Button>
        </div>
        <div className="justify-self-end">
          <ModeToggle />
        </div>
      </header>
      <Chat messages={messages} isLoading={isLoading} isStreaming={isStreaming} isSimulatedMessage={isSimulatedMessage} />
      <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  )
}
