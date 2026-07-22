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
  Sparkles,
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
      return <strong key={index} className="font-semibold text-zinc-100">{part.slice(2, -2)}</strong>
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index} className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[0.82em] text-violet-200">{part.slice(1, -1)}</code>
    }
    if (/^\[Source \d+\]$/.test(part)) {
      return <span key={index} className="font-medium text-violet-300">{part}</span>
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
      <ul key={`list-${blocks.length}`} className="my-2 list-disc space-y-1 pl-5 marker:text-violet-400">
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
      blocks.push(<h4 key={index} className="mt-3 mb-1 font-semibold text-zinc-100">{renderInline(line.replace(/^#{2,3}\s+/, ""))}</h4>)
      return
    }
    blocks.push(<p key={index} className="leading-6">{renderInline(line)}</p>)
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
    <div className="mt-4 border-t border-zinc-800/80 pt-3">
      <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-zinc-500">
        <Quote className="size-3" /> Grounding sources
      </p>
      <div className="grid gap-2 sm:grid-cols-2">
        {citations.map((citation) => {
          const source = sources.find((item) => item.chunk_id === citation.chunk_id)
          const document = documents.find((item) => item.id === source?.document_id)
          return (
            <button
              key={citation.chunk_id}
              type="button"
              disabled={!document}
              onClick={() => document && onCitationClick(document, citation.page_number, citation.chunk_id)}
              className="group flex min-w-0 items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950/70 px-2.5 py-2 text-left transition hover:border-violet-500/40 hover:bg-violet-500/5 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-violet-500/10 text-violet-300"><FileText className="size-3.5" /></span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-xs font-medium text-zinc-300 group-hover:text-violet-200">{citation.document_name}</span>
                <span className="block text-[11px] text-zinc-500">{citation.source_label} · Page {citation.page_number}</span>
              </span>
              <ChevronRight className="size-3.5 shrink-0 text-zinc-600 group-hover:text-violet-300" />
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
    <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/20">
      <div className="grid min-h-[680px] lg:grid-cols-[230px_minmax(0,1fr)]">
        <aside className="flex flex-col border-b border-zinc-800 bg-zinc-950/90 lg:border-r lg:border-b-0">
          <div className="flex items-center justify-between px-4 py-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200"><BookOpenText className="size-4 text-violet-400" /> Research</div>
            <Button variant="ghost" size="icon-sm" onClick={() => setActiveConversationId(null)} disabled={isStreaming} className="text-zinc-500 hover:text-zinc-200" aria-label="Start new conversation"><MessageSquarePlus /></Button>
          </div>
          <div className="flex gap-2 overflow-x-auto px-2 pb-3 lg:block lg:space-y-1 lg:overflow-y-auto">
            {conversations.map((conversation) => (
              <button key={conversation.id} type="button" disabled={isStreaming} onClick={() => setActiveConversationId(conversation.id)} className={cn("min-w-44 rounded-lg px-3 py-2.5 text-left transition lg:block lg:w-full", conversation.id === activeConversationId ? "bg-violet-500/10 text-violet-100 ring-1 ring-violet-500/25" : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300")}>
                <span className="block truncate text-xs font-medium">{conversationTitle(conversation)}</span>
                <span className="mt-1 block text-[10px] text-zinc-600">{conversation.messages.length} messages</span>
              </button>
            ))}
            {!conversations.length && <p className="px-3 py-4 text-xs leading-5 text-zinc-600">Your case research conversations will appear here.</p>}
          </div>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
            <div className="flex items-center gap-2.5"><span className="flex size-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-300"><Sparkles className="size-4" /></span><div><h2 className="text-sm font-semibold text-zinc-100">Ask your case documents</h2><p className="text-xs text-zinc-500">Answers are grounded in retrieved evidence</p></div></div>
            <span className="hidden rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-emerald-400 sm:block">Grounded</span>
          </header>

          <div ref={scrollRef} className="min-h-0 flex-1 space-y-5 overflow-y-auto px-5 py-6">
            {!activeConversation?.messages.length ? (
              <div className="mx-auto flex max-w-md flex-col items-center py-16 text-center"><span className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-300"><Bot className="size-6" /></span><h3 className="text-base font-semibold text-zinc-200">Start with a document question</h3><p className="mt-2 text-sm leading-6 text-zinc-500">Ask about obligations, dates, clauses, or differences across the documents in this case.</p><div className="mt-6 flex flex-wrap justify-center gap-2"><button type="button" onClick={() => setQuestion("What are the key obligations in this case?")} className="rounded-full border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 transition hover:border-violet-500/40 hover:text-violet-200">Key obligations</button><button type="button" onClick={() => setQuestion("What termination rights are described?")} className="rounded-full border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 transition hover:border-violet-500/40 hover:text-violet-200">Termination rights</button></div></div>
            ) : activeConversation.messages.map((message) => (
              <article key={message.id} className={cn("flex gap-3", message.role === "user" ? "justify-end" : "justify-start")}>
                {message.role === "assistant" && <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-violet-500/10 text-violet-300"><Bot className="size-4" /></span>}
                <div className={cn("max-w-[88%] rounded-2xl px-4 py-3 text-sm", message.role === "user" ? "bg-violet-600 text-white" : "border border-zinc-800 bg-zinc-900/60 text-zinc-300")}>
                  {message.role === "assistant" ? <MarkdownAnswer content={message.content || ""} /> : <p className="leading-6">{message.content}</p>}
                  {message.role === "assistant" && message.content && <CitationCards citations={message.citations ?? []} sources={message.sources ?? []} documents={documents} onCitationClick={onCitationClick} />}
                </div>
                {message.role === "user" && <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-zinc-800 text-zinc-300"><UserRound className="size-3.5" /></span>}
              </article>
            ))}
            {isStreaming && <div className="flex items-center gap-2 text-xs text-zinc-500"><LoaderCircle className="size-3.5 animate-spin text-violet-400" /> Researching retrieved documents…</div>}
          </div>

          <div className="border-t border-zinc-800 p-4">
            {error && <div className="mb-3 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-300"><TriangleAlert className="size-3.5" />{error}</div>}
            <form onSubmit={submit} className="rounded-xl border border-zinc-700 bg-zinc-900/80 p-2 shadow-inner shadow-black/10 focus-within:border-violet-500/60">
              <textarea value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} placeholder="Ask a question about this case…" rows={2} disabled={isStreaming || !documents.length} className="w-full resize-none bg-transparent px-2 py-1.5 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none disabled:cursor-not-allowed" />
              <div className="flex items-center justify-between px-1"><span className="text-[11px] text-zinc-600">Enter to send · Shift + Enter for a new line</span><Button type="submit" size="icon-sm" disabled={!question.trim() || isStreaming || !documents.length} className="bg-violet-600 text-white hover:bg-violet-500"><ArrowUp /></Button></div>
            </form>
            {!documents.length && <p className="mt-2 text-xs text-amber-400/80">Upload and process a document before starting research.</p>}
          </div>
        </div>
      </div>
    </section>
  )
}
