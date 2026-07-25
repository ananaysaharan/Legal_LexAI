"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
  Bot, Download, FilePlus2, FileText, History,
  LoaderCircle, RotateCcw, Save, Sparkles, WandSparkles,
} from "lucide-react"
import api from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

type DocumentType = "legal_summary" | "case_report" | "draft_contract" | "response_letter" | "internal_legal_note"
type EditAction = "rewrite" | "improve" | "simplify" | "expand" | "shorten" | "explain"
interface CaseItem { id: string; title: string }
interface LegalDocument { id: string; case_id: string; title: string; content: string; document_type: DocumentType; version: number; status: string; edit_operation: string; edit_instructions?: string | null; citations: string[]; created_at?: string }
interface Job { id: string; status: "queued" | "running" | "succeeded" | "failed"; job_type: string; result?: { document_id?: string; storage_path?: string; filename?: string }; error?: { message?: string } }

const typeLabels: Record<DocumentType, string> = { legal_summary: "Legal summary", case_report: "Case report", draft_contract: "Draft contract", response_letter: "Response letter", internal_legal_note: "Internal legal note" }
const editActions: { value: EditAction; label: string }[] = [
  { value: "rewrite", label: "Rewrite" }, { value: "improve", label: "Improve" }, { value: "simplify", label: "Simplify" }, { value: "expand", label: "Expand" }, { value: "shorten", label: "Shorten" }, { value: "explain", label: "Explain" },
]

function progressValue(status?: Job["status"]) { return status === "queued" ? 18 : status === "running" ? 62 : status === "succeeded" ? 100 : 100 }
function formatDate(value?: string) { return value ? new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value)) : "Current draft" }

export function DocumentWorkspace() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [caseId, setCaseId] = useState("")
  const [documents, setDocuments] = useState<LegalDocument[]>([])
  const [active, setActive] = useState<LegalDocument | null>(null)
  const [versions, setVersions] = useState<LegalDocument[]>([])
  const [content, setContent] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [job, setJob] = useState<Job | null>(null)
  const [error, setError] = useState("")
  const [generationOpen, setGenerationOpen] = useState(false)
  const [generation, setGeneration] = useState({ title: "", type: "case_report" as DocumentType, instructions: "" })
  const [editInstruction, setEditInstruction] = useState("")

  const loadDocuments = useCallback(async (selectedCaseId: string) => {
    if (!selectedCaseId) return
    const response = await api.get<LegalDocument[]>(`/generated-documents/cases/${selectedCaseId}`)
    setDocuments(response.data)
    if (!active && response.data[0]) setActive(response.data[0])
  }, [active])

  useEffect(() => {
    api.get<CaseItem[]>("/cases").then(({ data }) => { setCases(data); if (data[0]) setCaseId(data[0].id) }).catch(() => setError("Cases could not be loaded.")).finally(() => setLoading(false))
  }, [])
  useEffect(() => { loadDocuments(caseId).catch(() => setError("Generated documents could not be loaded.")) }, [caseId, loadDocuments])
  useEffect(() => { if (active) { setContent(active.content); api.get<LegalDocument[]>(`/generated-documents/${active.id}/versions`).then(({ data }) => setVersions(data)).catch(() => setVersions([])) } }, [active])

  useEffect(() => {
    if (!job || job.status === "succeeded" || job.status === "failed") return
    const timer = window.setInterval(async () => { try { const { data } = await api.get<Job>(`/jobs/${job.id}`); setJob(data) } catch { setError("Job progress could not be refreshed.") } }, 1800)
    return () => window.clearInterval(timer)
  }, [job])
  useEffect(() => { if (job?.status === "succeeded" && caseId) loadDocuments(caseId).catch(() => undefined) }, [job?.status, caseId, loadDocuments])

  const selectDocument = (document: LegalDocument) => { setActive(document); setError("") }
  const save = async () => { if (!active || saving) return; setSaving(true); try { const { data } = await api.post<LegalDocument>(`/generated-documents/${active.id}/save`, { content, instructions: "Manual workspace edit" }); setActive(data); await loadDocuments(caseId) } catch { setError("The draft could not be saved as a new version.") } finally { setSaving(false) } }
  const aiEdit = async (action: EditAction) => { if (!active) return; const instructions = editInstruction.trim() || `${action} this document while preserving legal meaning.`; setSaving(true); try { const { data } = await api.post<LegalDocument>(`/generated-documents/${active.id}/edit`, { operation: action, instructions }); setActive(data); setEditInstruction(""); await loadDocuments(caseId) } catch { setError("The AI edit could not be completed.") } finally { setSaving(false) } }
  const restore = async (version: LegalDocument) => { try { const { data } = await api.post<LegalDocument>(`/generated-documents/${version.id}/restore`); setActive(data); await loadDocuments(caseId) } catch { setError("The selected version could not be restored.") } }
  const queueExport = async (format: "pdf" | "docx" | "markdown") => { if (!active) return; try { const { data } = await api.post<Job>(`/generated-documents/${active.id}/exports`, { format, include_citations: true }); setJob(data) } catch { setError("Export could not be queued.") } }
  const generate = async (event: FormEvent) => { event.preventDefault(); if (!caseId) return; try { const { data } = await api.post<Job>("/generated-documents/jobs", { case_id: caseId, document_type: generation.type, title: generation.title, instructions: generation.instructions, top_k: 5 }); setJob(data); setGenerationOpen(false); setGeneration({ title: "", type: "case_report", instructions: "" }) } catch { setError("Document generation could not be queued.") } }
  const selectedCase = cases.find((item) => item.id === caseId)
  const dirty = Boolean(active && content !== active.content)
  const visibleVersions = useMemo(() => versions.slice().sort((a, b) => b.version - a.version), [versions])

  return <div className="mx-auto max-w-[1500px] space-y-5 pb-10">
    <header className="flex flex-col gap-4 rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between"><div className="flex items-center gap-3"><span className="flex size-11 items-center justify-center rounded-xl bg-violet-100 text-violet-700"><FileText className="size-5" /></span><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-violet-600">Legal drafting</p><h1 className="mt-1 text-xl font-semibold text-zinc-950">Document workspace</h1></div></div><div className="flex flex-wrap items-center gap-2"><select value={caseId} onChange={(event) => { setActive(null); setCaseId(event.target.value) }} className="h-8 rounded-lg border border-zinc-200 bg-white px-2 text-xs text-zinc-700">{cases.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select><Button onClick={() => setGenerationOpen(true)} className="bg-violet-600 text-white hover:bg-violet-700"><FilePlus2 className="size-4" /> Generate</Button></div></header>
    {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    {job && <Card className={cn("border shadow-sm", job.status === "failed" ? "border-red-200 bg-red-50" : "border-violet-200 bg-white")}><CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center"><span className="flex size-8 items-center justify-center rounded-full bg-violet-100 text-violet-700">{job.status === "running" || job.status === "queued" ? <LoaderCircle className="size-4 animate-spin" /> : <Sparkles className="size-4" />}</span><div className="min-w-0 flex-1"><div className="flex justify-between gap-3"><p className="text-sm font-medium text-zinc-800">{job.job_type.replaceAll("_", " ")}</p><Badge variant={job.status === "failed" ? "destructive" : "secondary"}>{job.status}</Badge></div><Progress value={progressValue(job.status)} className="mt-2 text-violet-600" /><p className="mt-1 text-xs text-zinc-500">{job.status === "succeeded" ? job.result?.filename ? `${job.result.filename} is ready in secure storage.` : "Document generation completed." : job.status === "failed" ? job.error?.message ?? "The job failed." : "Processing in a background worker…"}</p></div></CardContent></Card>}
    <div className="grid min-h-[680px] overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm xl:grid-cols-[255px_minmax(0,1fr)_265px]">
      <aside className="border-b border-zinc-200 bg-zinc-50/70 p-4 xl:border-r xl:border-b-0"><div className="mb-4 flex items-center justify-between"><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-zinc-500">Generated documents</p><span className="text-xs text-zinc-400">{documents.length}</span></div><div className="space-y-1.5">{loading ? <p className="p-3 text-sm text-zinc-400">Loading…</p> : documents.length ? documents.map((document) => <button key={document.id} onClick={() => selectDocument(document)} className={cn("w-full rounded-xl border p-3 text-left transition", active?.id === document.id ? "border-violet-300 bg-violet-50" : "border-transparent hover:border-zinc-200 hover:bg-white")}><p className="truncate text-sm font-medium text-zinc-800">{document.title}</p><p className="mt-1 text-[11px] text-zinc-500">{typeLabels[document.document_type]} · v{document.version}</p></button>) : <div className="rounded-xl border border-dashed border-zinc-200 p-5 text-center text-xs text-zinc-400">Generate a case artifact to start drafting.</div>}</div></aside>
      <main className="flex min-w-0 flex-col"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 px-5 py-3"><div>{active ? <><h2 className="text-sm font-semibold text-zinc-900">{active.title}</h2><p className="mt-0.5 text-xs text-zinc-500">{selectedCase?.title} · Version {active.version} · {dirty ? "Unsaved changes" : "Saved"}</p></> : <p className="text-sm text-zinc-500">Select a generated document to open it.</p>}</div><div className="flex items-center gap-1"><Button size="sm" variant="outline" disabled={!active || saving} onClick={save}><Save className="size-3.5" /> {saving ? "Saving" : "Save version"}</Button><div className="relative group"><Button size="sm" variant="outline" disabled={!active}><Download className="size-3.5" /> Export</Button><div className="invisible absolute right-0 z-10 mt-1 w-28 rounded-lg border border-zinc-200 bg-white p-1 shadow-lg group-hover:visible"><button onClick={() => queueExport("pdf")} className="w-full rounded px-2 py-1.5 text-left text-xs hover:bg-zinc-100">PDF</button><button onClick={() => queueExport("docx")} className="w-full rounded px-2 py-1.5 text-left text-xs hover:bg-zinc-100">DOCX</button><button onClick={() => queueExport("markdown")} className="w-full rounded px-2 py-1.5 text-left text-xs hover:bg-zinc-100">Markdown</button></div></div></div></div>
        {active ? <><div className="border-b border-zinc-200 bg-zinc-50 px-5 py-2"><div className="flex flex-wrap items-center gap-2"><span className="flex items-center gap-1 text-xs text-zinc-500"><WandSparkles className="size-3.5 text-violet-600" /> AI actions</span>{editActions.map((action) => <Button key={action.value} size="xs" variant="ghost" disabled={saving} onClick={() => aiEdit(action.value)}>{action.label}</Button>)}</div><Input value={editInstruction} onChange={(event) => setEditInstruction(event.target.value)} placeholder="Optional instruction for the next AI edit…" className="mt-2 h-8 border-zinc-200 bg-white text-xs" /></div><textarea value={content} onChange={(event) => setContent(event.target.value)} className="min-h-[505px] flex-1 resize-none p-7 text-[15px] leading-7 text-zinc-800 outline-none placeholder:text-zinc-400" spellCheck placeholder="Your legal document will appear here." /><footer className="flex items-center justify-between border-t border-zinc-200 px-5 py-2 text-xs text-zinc-500"><span>{content.trim().split(/\s+/).filter(Boolean).length} words</span><span>{active.citations.length} source references</span></footer></> : <div className="flex flex-1 flex-col items-center justify-center text-center"><Bot className="size-8 text-zinc-300" /><p className="mt-3 text-sm font-medium text-zinc-600">Open a legal artifact</p><p className="mt-1 text-xs text-zinc-400">Select a document or generate a new draft for this case.</p></div>}</main>
      <aside className="border-t border-zinc-200 bg-zinc-50/70 p-4 xl:border-t-0 xl:border-l"><div className="flex items-center gap-2"><History className="size-4 text-violet-600" /><p className="text-[11px] font-semibold uppercase tracking-[.14em] text-zinc-500">Version history</p></div><div className="mt-4 space-y-1">{visibleVersions.length ? visibleVersions.map((version, index) => <div key={version.id} className={cn("relative rounded-xl p-3", version.id === active?.id ? "bg-white ring-1 ring-violet-200" : "")}>{index < visibleVersions.length - 1 && <span className="absolute left-[21px] top-10 h-5 w-px bg-zinc-200" />}<div className="flex items-center justify-between"><span className="text-xs font-semibold text-zinc-800">Version {version.version}</span>{version.id === active?.id ? <Badge className="bg-violet-600">Open</Badge> : <button onClick={() => selectDocument(version)} className="text-[11px] text-violet-700 hover:underline">Open</button>}</div><p className="mt-1 text-[11px] text-zinc-500">{version.edit_operation.replaceAll("_", " ")} · {formatDate(version.created_at)}</p>{version.edit_instructions && <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-zinc-400">{version.edit_instructions}</p>}{version.id !== active?.id && <button onClick={() => restore(version)} className="mt-2 flex items-center gap-1 text-[11px] font-medium text-zinc-600 hover:text-violet-700"><RotateCcw className="size-3" /> Restore as new</button>}</div>) : <p className="mt-4 text-xs text-zinc-400">Version history will appear here.</p>}</div></aside>
    </div>
    <Dialog open={generationOpen} onOpenChange={setGenerationOpen}><DialogContent className="max-w-lg bg-white"><DialogHeader><DialogTitle>Generate a legal document</DialogTitle></DialogHeader><form onSubmit={generate} className="space-y-4"><div><Label htmlFor="document-title">Title</Label><Input id="document-title" required value={generation.title} onChange={(event) => setGeneration((current) => ({ ...current, title: event.target.value }))} className="mt-1.5" placeholder="e.g. Preliminary risk assessment" /></div><div><Label htmlFor="document-type">Document type</Label><select id="document-type" value={generation.type} onChange={(event) => setGeneration((current) => ({ ...current, type: event.target.value as DocumentType }))} className="mt-1.5 h-9 w-full rounded-lg border border-zinc-200 bg-white px-3 text-sm">{Object.entries(typeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div><Label htmlFor="document-instructions">Instructions</Label><textarea id="document-instructions" required value={generation.instructions} onChange={(event) => setGeneration((current) => ({ ...current, instructions: event.target.value }))} className="mt-1.5 min-h-28 w-full rounded-lg border border-zinc-200 p-3 text-sm outline-none focus:border-violet-500" placeholder="Describe the intended scope, audience, and outcome…" /></div><div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setGenerationOpen(false)}>Cancel</Button><Button type="submit" className="bg-violet-600 text-white hover:bg-violet-700"><Sparkles className="size-4" /> Queue generation</Button></div></form></DialogContent></Dialog>
  </div>
}
