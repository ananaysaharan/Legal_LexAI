"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import {
  BrainCircuit,
  Check,
  Clock3,
  FileText,
  History,
  Lightbulb,
  Plus,
  RefreshCw,
  Settings2,
  Sparkles,
} from "lucide-react"
import api from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

type PreferenceType =
  | "preferred_report_format"
  | "writing_style"
  | "citation_preferences"
  | "workflow_behavior"
  | "frequently_used_task"
  | "custom"

interface CaseItem { id: string; title: string }
interface Preference {
  id: string
  preference_type: PreferenceType
  preference_key: string
  preference_value: Record<string, unknown>
  scope: string
  confidence: number
  usage_count: number
  last_used_at?: string | null
  is_active: boolean
}
interface CaseMemory {
  id: string
  memory_type: string
  memory_key?: string | null
  content: string
  metadata: Record<string, unknown>
}

const typeLabels: Record<PreferenceType, string> = {
  preferred_report_format: "Report format",
  writing_style: "Writing style",
  citation_preferences: "Citation preferences",
  workflow_behavior: "Workflow behaviour",
  frequently_used_task: "Frequently used task",
  custom: "Custom preference",
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function relativeTime(value?: string | null) {
  if (!value) return "Recently learned"
  const days = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 86_400_000))
  if (!days) return "Today"
  return days === 1 ? "Yesterday" : `${days} days ago`
}

export function MemoryWorkspace() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [caseId, setCaseId] = useState("")
  const [preferences, setPreferences] = useState<Preference[]>([])
  const [memories, setMemories] = useState<CaseMemory[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [memoryEnabled, setMemoryEnabled] = useState(true)
  const [learningEnabled, setLearningEnabled] = useState(true)
  const [draft, setDraft] = useState({ type: "writing_style" as PreferenceType, key: "", value: "{\n  \n}" })

  const load = async (selectedCaseId = caseId) => {
    setLoading(true)
    setError("")
    try {
      const [caseResponse, preferenceResponse, memoryResponse] = await Promise.all([
        api.get<CaseItem[]>("/cases"),
        api.get<Preference[]>("/memory/preferences"),
        selectedCaseId ? api.get<CaseMemory[]>(`/memory/cases/${selectedCaseId}`) : Promise.resolve({ data: [] as CaseMemory[] }),
      ])
      setCases(caseResponse.data)
      setPreferences(preferenceResponse.data)
      setMemories(memoryResponse.data)
      if (!selectedCaseId && caseResponse.data[0]) setCaseId(caseResponse.data[0].id)
    } catch {
      setError("Memory data could not be loaded. Please refresh and try again.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load("") }, []) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (caseId) load(caseId) }, [caseId]) // eslint-disable-line react-hooks/exhaustive-deps

  const recentlyLearned = useMemo(
    () => [...preferences].sort((a, b) => (b.last_used_at ?? "").localeCompare(a.last_used_at ?? "")).slice(0, 4),
    [preferences],
  )
  const planningMemory = useMemo(() => memories.slice(0, 3), [memories])
  const planningPreferences = useMemo(() => preferences.filter((preference) => preference.is_active).slice(0, 3), [preferences])

  const savePreference = async (event: FormEvent) => {
    event.preventDefault()
    if (!draft.key.trim()) return
    let preferenceValue: Record<string, unknown>
    try { preferenceValue = JSON.parse(draft.value) } catch { setError("Preference value must be valid JSON."); return }
    setSaving(true)
    setError("")
    try {
      await api.put("/memory/preferences", {
        preference_type: draft.type,
        preference_key: draft.key.trim(),
        preference_value: preferenceValue,
        scope: "global",
        confidence: 100,
        update_strategy: "replace",
      })
      setDraft({ type: "writing_style", key: "", value: "{\n  \n}" })
      await load(caseId)
    } catch {
      setError("The preference could not be saved.")
    } finally { setSaving(false) }
  }

  const editPreference = (preference: Preference) => {
    setDraft({ type: preference.preference_type, key: preference.preference_key, value: JSON.stringify(preference.preference_value, null, 2) })
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-10">
      <header className="flex flex-col gap-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3"><span className="flex size-11 items-center justify-center rounded-xl bg-violet-100 text-violet-700"><BrainCircuit className="size-5" /></span><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-violet-600">Memory control centre</p><h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-950">Memory settings</h1><p className="mt-1 text-sm text-zinc-500">Review what the system retains and what it will pass into future plans.</p></div></div>
        <Button variant="outline" onClick={() => load(caseId)} disabled={loading}><RefreshCw className={cn("size-4", loading && "animate-spin")} /> Refresh</Button>
      </header>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_340px]">
        <div className="space-y-6">
          <Card className="border-zinc-200 bg-white shadow-sm"><CardHeader><CardTitle className="flex items-center gap-2 text-zinc-900"><Settings2 className="size-4 text-violet-600" /> Memory controls</CardTitle></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2">
            {[[memoryEnabled, setMemoryEnabled, "Use memory in planning", "Include relevant case context and preferences in new plans."], [learningEnabled, setLearningEnabled, "Learn from completed work", "Save curated findings and reports after successful runs."]].map(([enabled, setEnabled, title, detail]) => <label key={title as string} className="flex cursor-pointer items-start justify-between gap-3 rounded-xl border border-zinc-200 p-4 transition hover:border-violet-300"><span><span className="block text-sm font-medium text-zinc-800">{title as string}</span><span className="mt-1 block text-xs leading-5 text-zinc-500">{detail as string}</span></span><input type="checkbox" checked={enabled as boolean} onChange={(event) => (setEnabled as (value: boolean) => void)(event.target.checked)} className="mt-0.5 size-4 accent-violet-600" /></label>)}
          </CardContent></Card>

          <Card className="border-zinc-200 bg-white shadow-sm"><CardHeader><CardTitle className="flex items-center gap-2 text-zinc-900"><Sparkles className="size-4 text-violet-600" /> User preference editor</CardTitle></CardHeader><CardContent><form onSubmit={savePreference} className="grid gap-4"><div className="grid gap-4 sm:grid-cols-2"><div><Label htmlFor="preference-type">Preference type</Label><select id="preference-type" value={draft.type} onChange={(event) => setDraft((current) => ({ ...current, type: event.target.value as PreferenceType }))} className="mt-1.5 h-9 w-full rounded-lg border border-zinc-200 bg-white px-3 text-sm text-zinc-800 outline-none focus:border-violet-500">{Object.entries(typeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div><Label htmlFor="preference-key">Preference name</Label><Input id="preference-key" value={draft.key} onChange={(event) => setDraft((current) => ({ ...current, key: event.target.value }))} placeholder="e.g. concise_risk_summary" className="mt-1.5 border-zinc-200" /></div></div><div><Label htmlFor="preference-value">Preference value</Label><textarea id="preference-value" value={draft.value} onChange={(event) => setDraft((current) => ({ ...current, value: event.target.value }))} rows={5} className="mt-1.5 w-full rounded-lg border border-zinc-200 bg-zinc-50 p-3 font-mono text-xs text-zinc-800 outline-none focus:border-violet-500" /></div><div className="flex justify-end"><Button type="submit" disabled={saving || !draft.key.trim()} className="bg-violet-600 text-white hover:bg-violet-700"><Plus className="size-4" /> {saving ? "Saving" : "Save preference"}</Button></div></form></CardContent></Card>

          <Card className="border-zinc-200 bg-white shadow-sm"><CardHeader><div className="flex flex-wrap items-center justify-between gap-3"><div><CardTitle className="flex items-center gap-2 text-zinc-900"><FileText className="size-4 text-violet-600" /> Case memory viewer</CardTitle><p className="mt-1 text-xs text-zinc-500">Case-specific retained findings, reports, and execution summaries.</p></div><select value={caseId} onChange={(event) => setCaseId(event.target.value)} className="h-8 max-w-56 rounded-lg border border-zinc-200 bg-white px-2 text-xs text-zinc-700">{cases.length ? cases.map((item) => <option key={item.id} value={item.id}>{item.title}</option>) : <option>No cases available</option>}</select></div></CardHeader><CardContent><div className="space-y-2">{loading ? <p className="py-8 text-center text-sm text-zinc-400">Loading memory…</p> : memories.length ? memories.map((memory) => <article key={memory.id} className="rounded-xl border border-zinc-200 p-3.5"><div className="flex items-center justify-between gap-3"><span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-violet-700">{humanize(memory.memory_type)}</span>{memory.memory_key && <span className="truncate text-xs text-zinc-400">{memory.memory_key}</span>}</div><p className="mt-2 text-sm leading-6 text-zinc-700">{memory.content}</p></article>) : <div className="rounded-xl border border-dashed border-zinc-200 py-10 text-center text-sm text-zinc-400">No retained memory for this case yet.</div>}</div></CardContent></Card>
        </div>

        <aside className="space-y-6"><Card className="border-violet-200 bg-violet-50/50 shadow-sm"><CardHeader><CardTitle className="flex items-center gap-2 text-zinc-900"><Lightbulb className="size-4 text-violet-600" /> Planner context preview</CardTitle></CardHeader><CardContent className="space-y-4"><p className="text-xs leading-5 text-zinc-600">The next plan receives only this compact, relevant context.</p><div><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-zinc-500">Case memory</p><div className="mt-2 space-y-2">{memoryEnabled && planningMemory.length ? planningMemory.map((memory) => <div key={memory.id} className="rounded-lg border border-violet-100 bg-white p-2.5 text-xs text-zinc-700"><span className="font-medium text-violet-700">{humanize(memory.memory_type)}</span><p className="mt-1 line-clamp-2 text-zinc-600">{memory.content}</p></div>) : <p className="text-xs text-zinc-400">No matching case memories.</p>}</div></div><div><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-zinc-500">User preferences</p><div className="mt-2 space-y-2">{memoryEnabled && planningPreferences.length ? planningPreferences.map((preference) => <div key={preference.id} className="rounded-lg border border-violet-100 bg-white p-2.5"><p className="text-xs font-medium text-zinc-700">{preference.preference_key}</p><p className="mt-1 text-[11px] text-zinc-500">{typeLabels[preference.preference_type]} · {preference.confidence}% confidence</p></div>) : <p className="text-xs text-zinc-400">No active preferences.</p>}</div></div></CardContent></Card>

          <Card className="border-zinc-200 bg-white shadow-sm"><CardHeader><CardTitle className="flex items-center gap-2 text-zinc-900"><History className="size-4 text-violet-600" /> Memory timeline</CardTitle></CardHeader><CardContent><div className="space-y-4">{recentlyLearned.length ? recentlyLearned.map((preference, index) => <div key={preference.id} className="relative flex gap-3"><span className="relative z-10 flex size-6 shrink-0 items-center justify-center rounded-full border border-violet-200 bg-violet-50 text-violet-600">{index === 0 ? <Sparkles className="size-3" /> : <Clock3 className="size-3" />}</span>{index < recentlyLearned.length - 1 && <span className="absolute left-3 top-6 h-7 w-px bg-zinc-200" />}<div className="pb-2"><p className="text-xs font-medium text-zinc-800">{preference.preference_key}</p><p className="mt-0.5 text-[11px] text-zinc-500">{relativeTime(preference.last_used_at)} · used {preference.usage_count} times</p></div></div>) : <p className="py-4 text-sm text-zinc-400">No preferences have been learned yet.</p>}</div></CardContent></Card>

          <Card className="border-zinc-200 bg-white shadow-sm"><CardHeader><CardTitle className="flex items-center gap-2 text-zinc-900"><Check className="size-4 text-emerald-600" /> Recently learned</CardTitle></CardHeader><CardContent><div className="space-y-2">{recentlyLearned.map((preference) => <button type="button" key={preference.id} onClick={() => editPreference(preference)} className="w-full rounded-lg border border-zinc-200 px-3 py-2.5 text-left hover:border-violet-300 hover:bg-violet-50"><p className="text-xs font-medium text-zinc-800">{preference.preference_key}</p><p className="mt-1 text-[11px] text-zinc-500">{typeLabels[preference.preference_type]}</p></button>)}</div></CardContent></Card></aside>
      </div>
    </div>
  )
}
