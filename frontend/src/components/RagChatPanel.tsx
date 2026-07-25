"use client"

import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react"
import {
  ArrowUp,
  BookOpenText,
  Bot,
  ChevronRight,
  FileText,
  LoaderCircle,
  MessageSquarePlus,
  Quote,
  TriangleAlert,
  UserRound,
} from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export interface ChatDocument {
  id: string
  filename: string
  storage_path: string
}

interface Citation {
  source_label: string
  document_name: string
  page_number: number
  chunk_id: string
}

interface RetrievedSource {
  document_id: string
  chunk_id: string
  document_filename: string
  page_number: number
  text_content: string
}

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: Citation[]
  sources?: RetrievedSource[]
}

interface Conversation {
  id: string
  messages: ChatMessage[]
  updatedAt: number
}

interface ChatApiResponse {
  conversation_id: string
  message_id: string
  answer: string
  citations: Citation[]
  sources: RetrievedSource[]
}

interface RagChatPanelProps {
  caseId: string
  documents: ChatDocument[]
  onCitationClick: (document: ChatDocument, page: number, chunkId: string) => void
}

const storageKey = (caseId: string) => `legal-rag-conversations:${caseId}`

function loadSavedConversations(caseId: string): Conversation[] {
  if (typeof window === "undefined") return []
  const saved = window.localStorage.getItem(storageKey(caseId))
  if (!saved) return []
  try {
    return JSON.parse(saved) as Conversation[]
  } catch {
    window.localStorage.removeItem(storageKey(caseId))
    return []
  }
}

function conversationTitle(conversation: Conversation) {
  const firstQuestion = conversation.messages.find((message) => message.role === "user")
  if (!firstQuestion) return "New research"
  return firstQuestion.content.length > 46
    ? `${firstQuestion.content.slice(0, 46)}…`
    : firstQuestion.content
}

function renderInline(value: string): ReactNode[] {
  return value.split(/(\*\*[^*]+\*\*|`[^`]+`|\[Source \d+\])/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index} className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.82em] text-slate-800 border border-slate-200">{part.slice(1, -1)}</code>
    }
    if (/^\[Source \d+\]$/.test(part)) {
      return <span key={index} className="font-bold text-slate-900 underline">{part}</span>
    }
    return part
  })
}

function MarkdownAnswer({ content }: { content: string }) {
  const lines = content.split("\n")
  const blocks: ReactNode[] = []
  let listItems: string[] = []

  const flushList = () => {
    if (!listItems.length) return
    blocks.push(
      <ul key={`list-${blocks.length}`} className="my-2 list-disc space-y-1 pl-5 marker:text-slate-700">
        {listItems.map((item, index) => <li key={index}>{renderInline(item)}</li>)}
      </ul>
    )
    listItems = []
  }

  lines.forEach((line, index) => {
    if (/^[-*]\s+/.test(line)) {
      listItems.push(line.replace(/^[-*]\s+/, ""))
      return
    }
    flushList()
    if (!line.trim()) return
    if (line.startsWith("### ") || line.startsWith("## ")) {
      blocks.push(<h4 key={index} className="mt-3 mb-1 font-bold text-slate-900">{renderInline(line.replace(/^#{2,3}\s+/, ""))}</h4>)
      return
    }
    blocks.push(<p key={index} className="leading-relaxed">{renderInline(line)}</p>)
  })
  flushList()
  return <div className="space-y-2">{blocks}</div>
}

function CitationCards({
  citations,
  sources,
  documents,
  onCitationClick,
}: {
  citations: Citation[]
  sources: RetrievedSource[]
  documents: ChatDocument[]
  onCitationClick: RagChatPanelProps["onCitationClick"]
}) {
  if (!citations.length) return null
  return (
    <div className="mt-3 border-t border-slate-200 pt-2.5">
      <p className="mb-2 flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-slate-500">
        <Quote className="size-3" /> Grounding Sources
      </p>
      <div className="grid gap-1.5 sm:grid-cols-2">
        {citations.map((citation) => {
          const source = sources.find((item) => item.chunk_id === citation.chunk_id)
          const document = documents.find((item) => item.id === source?.document_id)
          return (
            <button
              key={citation.chunk_id}
              type="button"
              disabled={!document}
              onClick={() => document && onCitationClick(document, citation.page_number, citation.chunk_id)}
              className="group flex min-w-0 items-center gap-2 rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-left transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="flex size-6 shrink-0 items-center justify-center rounded bg-slate-200 text-slate-700"><FileText className="size-3" /></span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-xs font-semibold text-slate-900">{citation.document_name}</span>
                <span className="block text-[10px] text-slate-500">{citation.source_label} · Page {citation.page_number}</span>
              </span>
              <ChevronRight className="size-3 shrink-0 text-slate-400 group-hover:text-slate-700" />
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function RagChatPanel({ caseId, documents, onCitationClick }: RagChatPanelProps) {
  const [conversations, setConversations] = useState<Conversation[]>(() => loadSavedConversations(caseId))
  const [activeConversationId, setActiveConversationId] = useState<string | null>(() => loadSavedConversations(caseId)[0]?.id ?? null)
  const [question, setQuestion] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    window.localStorage.setItem(storageKey(caseId), JSON.stringify(conversations))
  }, [caseId, conversations])

  const activeConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === activeConversationId) ?? null,
    [activeConversationId, conversations]
  )

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [activeConversation?.messages, isStreaming])

  const updateConversation = (id: string, update: (conversation: Conversation) => Conversation) => {
    setConversations((current) => current.map((conversation) => conversation.id === id ? update(conversation) : conversation))
  }

  const revealAnswer = async (conversationId: string, response: ChatApiResponse) => {
    const assistantId = response.message_id
    updateConversation(conversationId, (conversation) => ({
      ...conversation,
      id: response.conversation_id,
      updatedAt: Date.now(),
      messages: [...conversation.messages, { id: assistantId, role: "assistant", content: "", citations: response.citations, sources: response.sources }],
    }))
    setActiveConversationId(response.conversation_id)

    for (let index = 0; index < response.answer.length; index += 18) {
      const nextText = response.answer.slice(0, index + 18)
      setConversations((current) => current.map((conversation) => {
        if (conversation.id !== response.conversation_id) return conversation
        return {
          ...conversation,
          messages: conversation.messages.map((message) => message.id === assistantId ? { ...message, content: nextText } : message),
        }
      }))
      await new Promise((resolve) => window.setTimeout(resolve, 14))
    }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || isStreaming) return
    setError("")
    setQuestion("")
    setIsStreaming(true)

    const isNewConversation = !activeConversationId
    const localConversationId = activeConversationId ?? `local-${crypto.randomUUID()}`
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: trimmedQuestion }
    if (isNewConversation) {
      setConversations((current) => [{ id: localConversationId, messages: [userMessage], updatedAt: Date.now() }, ...current])
      setActiveConversationId(localConversationId)
    } else {
      updateConversation(localConversationId, (conversation) => ({ ...conversation, messages: [...conversation.messages, userMessage], updatedAt: Date.now() }))
    }

    try {
      const response = await api.post<ChatApiResponse>(`/cases/${caseId}/chat`, {
        question: trimmedQuestion,
        top_k: 5,
        ...(isNewConversation ? {} : { conversation_id: localConversationId }),
      })
      await revealAnswer(localConversationId, response.data)
    } catch {
      updateConversation(localConversationId, (conversation) => ({ ...conversation, messages: conversation.messages.slice(0, -1) }))
      setQuestion(trimmedQuestion)
      setError("The research response could not be completed. Please try again.")
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-2xs text-slate-900 font-sans">
      <div className="grid min-h-[580px] lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="flex flex-col border-b border-slate-200 bg-slate-50/50 lg:border-r lg:border-b-0">
          <div className="flex items-center justify-between px-3.5 py-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900"><BookOpenText className="size-3.5" /> Research Threads</div>
            <Button variant="ghost" size="icon-sm" onClick={() => setActiveConversationId(null)} disabled={isStreaming} className="text-slate-600 hover:text-slate-900" aria-label="Start new conversation"><MessageSquarePlus className="size-3.5" /></Button>
          </div>
          <div className="flex gap-2 overflow-x-auto px-2 pb-3 lg:block lg:space-y-1 lg:overflow-y-auto">
            {conversations.map((conversation) => (
              <button key={conversation.id} type="button" disabled={isStreaming} onClick={() => setActiveConversationId(conversation.id)} className={cn("min-w-40 rounded px-2.5 py-2 text-left transition lg:block lg:w-full", conversation.id === activeConversationId ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900")}>
                <span className="block truncate text-xs font-semibold">{conversationTitle(conversation)}</span>
                <span className="mt-0.5 block text-[10px] opacity-70">{conversation.messages.length} messages</span>
              </button>
            ))}
            {!conversations.length && <p className="px-3 py-3 text-xs text-slate-400">Research conversations will appear here.</p>}
          </div>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
            <div className="flex items-center gap-2"><Bot className="size-4 text-slate-700" /><div><h2 className="text-xs font-bold text-slate-900">Document Research Query</h2></div></div>
          </header>

          <div ref={scrollRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-5">
            {!activeConversation?.messages.length ? (
              <div className="mx-auto flex max-w-sm flex-col items-center py-12 text-center"><Bot className="size-8 text-slate-400 mb-2" /><h3 className="text-sm font-bold text-slate-900">Ask a question about this case</h3><p className="mt-1 text-xs text-slate-500">Ask about obligations, dates, clauses, or differences across case documents.</p><div className="mt-4 flex flex-wrap justify-center gap-1.5"><button type="button" onClick={() => setQuestion("What are the key obligations in this case?")} className="rounded border border-slate-300 px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-100">Key obligations</button><button type="button" onClick={() => setQuestion("What termination rights are described?")} className="rounded border border-slate-300 px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-100">Termination rights</button></div></div>
            ) : activeConversation.messages.map((message) => (
              <article key={message.id} className={cn("flex gap-2.5", message.role === "user" ? "justify-end" : "justify-start")}>
                {message.role === "assistant" && <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded bg-slate-100 text-slate-700"><Bot className="size-3.5" /></span>}
                <div className={cn("max-w-[85%] rounded-lg px-3.5 py-2.5 text-xs leading-relaxed", message.role === "user" ? "bg-slate-900 text-white font-medium" : "border border-slate-200 bg-slate-50 text-slate-800")}>
                  {message.role === "assistant" ? <MarkdownAnswer content={message.content || ""} /> : <p>{message.content}</p>}
                  {message.role === "assistant" && message.content && <CitationCards citations={message.citations ?? []} sources={message.sources ?? []} documents={documents} onCitationClick={onCitationClick} />}
                </div>
                {message.role === "user" && <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded bg-slate-200 text-slate-700"><UserRound className="size-3" /></span>}
              </article>
            ))}
            {isStreaming && <div className="flex items-center gap-2 text-xs text-slate-500"><LoaderCircle className="size-3.5 animate-spin" /> Querying documents...</div>}
          </div>

          <div className="border-t border-slate-200 p-3">
            {error && <div className="mb-2 flex items-center gap-2 rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700"><TriangleAlert className="size-3.5" />{error}</div>}
            <form onSubmit={submit} className="rounded border border-slate-300 bg-white p-1.5 focus-within:border-slate-900">
              <textarea value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} placeholder="Ask a question about this case..." rows={2} disabled={isStreaming || !documents.length} className="w-full resize-none bg-transparent px-2 py-1 text-xs text-slate-900 placeholder:text-slate-400 outline-none disabled:cursor-not-allowed" />
              <div className="flex items-center justify-between px-1"><span className="text-[10px] text-slate-400">Enter to send · Shift + Enter for new line</span><Button type="submit" size="icon-sm" disabled={!question.trim() || isStreaming || !documents.length} className="bg-slate-900 text-white hover:bg-slate-800 text-xs h-7 w-7"><ArrowUp className="size-3.5" /></Button></div>
            </form>
            {!documents.length && <p className="mt-1 text-[11px] text-slate-500">Upload a document before starting research.</p>}
          </div>
        </div>
      </div>
    </section>
  )
}
