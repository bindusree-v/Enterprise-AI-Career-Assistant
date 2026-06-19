/**
 * AI Chat page — multi-turn conversational assistant with resume context.
 */

import { clsx } from 'clsx'
import { MessageSquare, Send, Sparkles } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { chatApi } from '../lib/api'
import { useResumeStore } from '../store/resumeStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  suggestions?: string[]
}

const STARTER_PROMPTS = [
  'What are my strongest skills based on my resume?',
  'How can I improve my resume for software engineering roles?',
  'What salary range should I target given my experience?',
  'What are my biggest skill gaps for a senior engineer role?',
]

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 p-3 bg-gray-800 rounded-2xl w-16">
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  )
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'

  return (
    <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={clsx('max-w-[80%] space-y-2')}>
        {!isUser && (
          <div className="flex items-center gap-2 mb-1">
            <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="text-xs text-gray-500">CareerGPT</span>
          </div>
        )}

        <div
          className={clsx(
            'rounded-2xl px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-indigo-600 text-white rounded-tr-sm'
              : 'bg-gray-800 text-gray-200 rounded-tl-sm'
          )}
        >
          {msg.content}
        </div>

        {/* Sources */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {msg.sources.map((s, i) => (
              <span key={i} className="text-xs text-gray-600 bg-gray-800 px-2 py-0.5 rounded-full">
                📎 {s}
              </span>
            ))}
          </div>
        )}

        {/* Suggestion chips */}
        {msg.suggestions && msg.suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {msg.suggestions.map((s, i) => (
              <button
                key={i}
                className="text-xs text-indigo-400 border border-indigo-800 rounded-full px-3 py-1 hover:bg-indigo-900/30 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function ChatPage() {
  const { state, dispatch } = useResumeStore()
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `Hi! I'm CareerGPT, your AI career assistant. I've analyzed your resume and I'm ready to help. Ask me anything about your career, skills, or how to land your next role! 🚀`,
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isTyping) return

      const userMsg: Message = { role: 'user', content: text }
      setMessages((prev) => [...prev, userMsg])
      setInput('')
      setIsTyping(true)

      try {
        const history = messages.map((m) => ({ role: m.role, content: m.content }))

        const res = await chatApi.send({
          resumeId: state.resumeId!,
          message: text,
          sessionId: state.chatSessionId ?? undefined,
          history,
        })

        if (!state.chatSessionId) {
          dispatch({ type: 'SET_CHAT_SESSION', sessionId: res.session_id })
        }

        const assistantMsg: Message = {
          role: 'assistant',
          content: res.message,
          sources: res.sources,
          suggestions: res.suggested_actions,
        }
        setMessages((prev) => [...prev, assistantMsg])
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Failed to send message')
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
          },
        ])
      } finally {
        setIsTyping(false)
      }
    },
    [messages, isTyping, state.resumeId, state.chatSessionId, dispatch]
  )

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="animate-fade-in flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-600/40 flex items-center justify-center">
          <MessageSquare className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">AI Career Chat</h1>
          <p className="text-gray-400 text-sm">Ask anything about your career, resume, or next steps</p>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-1">
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <TypingIndicator />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starter prompts (shown only when no user messages) */}
      {messages.filter((m) => m.role === 'user').length === 0 && (
        <div className="grid grid-cols-2 gap-2 mb-4">
          {STARTER_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => sendMessage(p)}
              className="text-left text-xs text-gray-400 bg-gray-800 border border-gray-700
                         rounded-lg px-3 py-2 hover:border-indigo-600/50 hover:text-gray-200 transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div className="flex gap-3 items-end">
        <textarea
          className="input flex-1 resize-none min-h-[44px] max-h-[120px] py-2.5"
          placeholder="Ask about your career, skills, interview tips..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || isTyping}
          className="btn-primary h-11 px-4 flex items-center gap-2 flex-shrink-0"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>
    </div>
  )
}
