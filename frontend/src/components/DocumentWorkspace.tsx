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
  const aiEdit = async (action: EditAction) => { if (!active) return; const instructions = editInstruction.trim() || `${action} this document while preserving legal meaning.`; setSaving(true); try { const { data } = await api.post<LegalDocument>(`/generated-documents/${active.id}/edit`, { operation: action, instructions }); setActive(data); setEditInstruction(""); await loadDocuments(caseId) } catch { setError("The edit could not be completed.") } finally { setSaving(false) } }
  const restore = async (version: LegalDocument) => { try { const { data } = await api.post<LegalDocument>(`/generated-documents/${version.id}/restore`); setActive(data); await loadDocuments(caseId) } catch { setError("The selected version could not be restored.") } }
  const queueExport = async (format: "pdf" | "docx" | "markdown") => { if (!active) return; try { const { data } = await api.post<Job>(`/generated-documents/${active.id}/exports`, { format, include_citations: true }); setJob(data) } catch { setError("Export could not be queued.") } }
  const generate = async (event: FormEvent) => { event.preventDefault(); if (!caseId) return; try { const { data } = await api.post<Job>("/generated-documents/jobs", { case_id: caseId, document_type: generation.type, title: generation.title, instructions: generation.instructions, top_k: 5 }); setJob(data); setGenerationOpen(false); setGeneration({ title: "", type: "case_report", instructions: "" }) } catch { setError("Document generation could not be queued.") } }
  const selectedCase = cases.find((item) => item.id === caseId)
  const dirty = Boolean(active && content !== active.content)
  const visibleVersions = useMemo(() => versions.slice().sort((a, b) => b.version - a.version), [versions])

  return (
    <div className="mx-auto max-w-[1500px] space-y-5 pb-10 font-sans text-slate-900">
      <header className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-2xs lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded bg-slate-100 text-slate-900"><FileText className="size-5" /></span>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Legal Drafting</p>
            <h1 className="mt-0.5 text-lg font-bold text-slate-900">Document Workspace</h1>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select value={caseId} onChange={(event) => { setActive(null); setCaseId(event.target.value) }} className="h-8 rounded border border-slate-300 bg-white px-2 text-xs text-slate-800">
            {cases.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <Button onClick={() => setGenerationOpen(true)} className="bg-slate-900 text-white hover:bg-slate-800 text-xs h-8">
            <FilePlus2 className="size-4" /> Generate Document
          </Button>
        </div>
      </header>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">{error}</div>}

      {job && (
        <Card className={cn("border shadow-2xs", job.status === "failed" ? "border-red-200 bg-red-50" : "border-slate-200 bg-white")}>
          <CardContent className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center">
            <span className="flex size-7 items-center justify-center rounded bg-slate-100 text-slate-900">
              {job.status === "running" || job.status === "queued" ? <LoaderCircle className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex justify-between gap-3">
                <p className="text-xs font-semibold text-slate-800">{job.job_type.replaceAll("_", " ")}</p>
                <Badge variant={job.status === "failed" ? "destructive" : "secondary"}>{job.status}</Badge>
              </div>
              <Progress value={progressValue(job.status)} className="mt-2 text-slate-900" />
              <p className="mt-1 text-[11px] text-slate-500">
                {job.status === "succeeded" ? job.result?.filename ? `${job.result.filename} is ready.` : "Generation complete." : job.status === "failed" ? job.error?.message ?? "Failed." : "Processing…"}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid min-h-[600px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-2xs xl:grid-cols-[250px_minmax(0,1fr)_250px]">
        <aside className="border-b border-slate-200 bg-slate-50/50 p-4 xl:border-r xl:border-b-0">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Documents</p>
            <span className="text-xs text-slate-400">{documents.length}</span>
          </div>
          <div className="space-y-1">
            {loading ? <p className="p-2 text-xs text-slate-400">Loading…</p> : documents.length ? documents.map((document) => (
              <button key={document.id} onClick={() => selectDocument(document)} className={cn("w-full rounded border p-2.5 text-left transition", active?.id === document.id ? "border-slate-900 bg-slate-900 text-white" : "border-transparent text-slate-700 hover:border-slate-300 hover:bg-white")}>
                <p className="truncate text-xs font-semibold">{document.title}</p>
                <p className="mt-0.5 text-[10px] opacity-70">{typeLabels[document.document_type]} · v{document.version}</p>
              </button>
            )) : <div className="rounded border border-dashed border-slate-200 p-4 text-center text-xs text-slate-400">No documents yet.</div>}
          </div>
        </aside>

        <main className="flex min-w-0 flex-col">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
            <div>
              {active ? (
                <>
                  <h2 className="text-xs font-bold text-slate-900">{active.title}</h2>
                  <p className="mt-0.5 text-[11px] text-slate-500">{selectedCase?.title} · v{active.version} · {dirty ? "Unsaved" : "Saved"}</p>
                </>
              ) : <p className="text-xs text-slate-400">Select a document to open it.</p>}
            </div>
            <div className="flex items-center gap-1">
              <Button size="sm" variant="outline" disabled={!active || saving} onClick={save} className="text-xs h-7">
                <Save className="size-3 mr-1" /> {saving ? "Saving..." : "Save"}
              </Button>
              <div className="relative group">
                <Button size="sm" variant="outline" disabled={!active} className="text-xs h-7">
                  <Download className="size-3 mr-1" /> Export
                </Button>
                <div className="invisible absolute right-0 z-10 mt-1 w-28 rounded border border-slate-200 bg-white p-1 shadow-md group-hover:visible">
                  <button onClick={() => queueExport("pdf")} className="w-full rounded px-2 py-1 text-left text-xs hover:bg-slate-100">PDF</button>
                  <button onClick={() => queueExport("docx")} className="w-full rounded px-2 py-1 text-left text-xs hover:bg-slate-100">DOCX</button>
                  <button onClick={() => queueExport("markdown")} className="w-full rounded px-2 py-1 text-left text-xs hover:bg-slate-100">Markdown</button>
                </div>
              </div>
            </div>
          </div>

          {active ? (
            <>
              <div className="border-b border-slate-200 bg-slate-50 px-4 py-2">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="flex items-center gap-1 text-[11px] font-bold text-slate-700"><WandSparkles className="size-3" /> Actions</span>
                  {editActions.map((action) => (
                    <Button key={action.value} size="xs" variant="outline" disabled={saving} onClick={() => aiEdit(action.value)} className="h-6 text-[11px] px-2">{action.label}</Button>
                  ))}
                </div>
                <Input value={editInstruction} onChange={(event) => setEditInstruction(event.target.value)} placeholder="Instruction for next edit…" className="mt-2 h-7 border-slate-300 bg-white text-xs" />
              </div>
              <textarea value={content} onChange={(event) => setContent(event.target.value)} className="min-h-[450px] flex-1 resize-none p-6 text-xs leading-relaxed text-slate-900 outline-none placeholder:text-slate-400 font-sans" spellCheck placeholder="Document text..." />
              <footer className="flex items-center justify-between border-t border-slate-200 px-4 py-2 text-[11px] text-slate-500">
                <span>{content.trim().split(/\s+/).filter(Boolean).length} words</span>
                <span>{active.citations.length} sources</span>
              </footer>
            </>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center text-center p-8">
              <Bot className="size-8 text-slate-300" />
              <p className="mt-2 text-xs font-semibold text-slate-600">Select a document</p>
            </div>
          )}
        </main>

        <aside className="border-t border-slate-200 bg-slate-50/50 p-4 xl:border-t-0 xl:border-l">
          <div className="flex items-center gap-1.5">
            <History className="size-3.5 text-slate-700" />
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Versions</p>
          </div>
          <div className="mt-3 space-y-1">
            {visibleVersions.length ? visibleVersions.map((version, index) => (
              <div key={version.id} className={cn("relative rounded border p-2.5", version.id === active?.id ? "bg-white border-slate-900" : "border-slate-200")}>
                {index < visibleVersions.length - 1 && <span className="absolute left-[19px] top-8 h-4 w-px bg-slate-200" />}
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-900">v{version.version}</span>
                  {version.id === active?.id ? (
                    <Badge className="bg-slate-900 text-white text-[10px]">Open</Badge>
                  ) : (
                    <button onClick={() => selectDocument(version)} className="text-[11px] font-medium text-slate-700 hover:underline">Open</button>
                  )}
                </div>
                <p className="mt-0.5 text-[10px] text-slate-500">{version.edit_operation.replaceAll("_", " ")} · {formatDate(version.created_at)}</p>
                {version.id !== active?.id && (
                  <button onClick={() => restore(version)} className="mt-1.5 flex items-center gap-1 text-[10px] font-medium text-slate-600 hover:text-slate-900">
                    <RotateCcw className="size-3" /> Restore
                  </button>
                )}
              </div>
            )) : <p className="mt-2 text-xs text-slate-400">No versions.</p>}
          </div>
        </aside>
      </div>

      <Dialog open={generationOpen} onOpenChange={setGenerationOpen}>
        <DialogContent className="max-w-md bg-white border border-slate-200">
          <DialogHeader>
            <DialogTitle className="text-sm font-bold text-slate-900">Generate Legal Document</DialogTitle>
          </DialogHeader>
          <form onSubmit={generate} className="space-y-3">
            <div>
              <Label htmlFor="document-title" className="text-xs">Title</Label>
              <Input id="document-title" required value={generation.title} onChange={(event) => setGeneration((current) => ({ ...current, title: event.target.value }))} className="mt-1 text-xs h-8 border-slate-300" placeholder="e.g. Risk Assessment" />
            </div>
            <div>
              <Label htmlFor="document-type" className="text-xs">Document Type</Label>
              <select id="document-type" value={generation.type} onChange={(event) => setGeneration((current) => ({ ...current, type: event.target.value as DocumentType }))} className="mt-1 h-8 w-full rounded border border-slate-300 bg-white px-2 text-xs text-slate-800">
                {Object.entries(typeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </div>
            <div>
              <Label htmlFor="document-instructions" className="text-xs">Instructions</Label>
              <textarea id="document-instructions" required value={generation.instructions} onChange={(event) => setGeneration((current) => ({ ...current, instructions: event.target.value }))} className="mt-1 min-h-24 w-full rounded border border-slate-300 p-2 text-xs text-slate-900 outline-none" placeholder="Scope and key details..." />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setGenerationOpen(false)} className="text-xs h-8">Cancel</Button>
              <Button type="submit" className="bg-slate-900 text-white hover:bg-slate-800 text-xs h-8">Queue Generation</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
