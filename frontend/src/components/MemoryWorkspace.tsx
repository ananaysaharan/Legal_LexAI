"use client"

import { FormEvent, useEffect, useState } from "react"
import {
  BrainCircuit, Check, Clock3, FileText, History, Lightbulb, Plus, RefreshCw, Settings2, Sparkles,
} from "lucide-react"
import api from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

type PreferenceType = "writing_style" | "risk_tolerance" | "jurisdiction_precedence" | "custom"
interface CaseItem { id: string; title: string }
interface CaseMemory { id: string; case_id: string; memory_type: string; memory_key?: string | null; content: string; created_at: string }
interface Preference { id: string; preference_type: PreferenceType; preference_key: string; preference_value: unknown; confidence: number; usage_count: number; last_used_at: string }

const typeLabels: Record<PreferenceType, string> = { writing_style: "Writing style", risk_tolerance: "Risk tolerance", jurisdiction_precedence: "Jurisdiction precedence", custom: "Custom" }

function humanize(text: string) { return text.replaceAll("_", " ") }
function relativeTime(value: string) { return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(new Date(value)) }

export function MemoryWorkspace() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [caseId, setCaseId] = useState("")
  const [memories, setMemories] = useState<CaseMemory[]>([])
  const [preferences, setPreferences] = useState<Preference[]>([])
  const [memoryEnabled, setMemoryEnabled] = useState(true)
  const [learningEnabled, setLearningEnabled] = useState(true)
  const [draft, setDraft] = useState({ type: "writing_style" as PreferenceType, key: "", value: "{\n  \n}" })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  const load = async (selectedCaseId: string) => {
    setLoading(true)
    setError("")
    try {
      const [casesRes, prefRes] = await Promise.all([
        api.get<CaseItem[]>("/cases"),
        api.get<Preference[]>("/memory/preferences"),
      ])
      setCases(casesRes.data)
      setPreferences(prefRes.data)
      const currentCase = selectedCaseId || casesRes.data[0]?.id || ""
      setCaseId(currentCase)
      if (currentCase) {
        const memoryRes = await api.get<CaseMemory[]>(`/memory/cases/${currentCase}`)
        setMemories(memoryRes.data)
      }
    } catch {
      setError("Memory records could not be loaded.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load("").catch(() => undefined) }, [])
  useEffect(() => {
    if (!caseId) return
    api.get<CaseMemory[]>(`/memory/cases/${caseId}`).then(({ data }) => setMemories(data)).catch(() => setMemories([]))
  }, [caseId])

  const planningMemory = memories.slice(0, 3)
  const planningPreferences = preferences.slice(0, 3)
  const recentlyLearned = preferences.slice().sort((a, b) => new Date(b.last_used_at).getTime() - new Date(a.last_used_at).getTime()).slice(0, 4)

  const savePreference = async (event: FormEvent) => {
    event.preventDefault()
    if (!draft.key.trim() || saving) return
    setSaving(true)
    let preferenceValue: unknown = draft.value
    try { preferenceValue = JSON.parse(draft.value) } catch { preferenceValue = draft.value }

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
    <div className="mx-auto max-w-7xl space-y-5 pb-10 font-sans text-slate-900">
      <header className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-2xs md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3"><span className="flex size-10 items-center justify-center rounded bg-slate-100 text-slate-900"><BrainCircuit className="size-5" /></span><div><p className="text-xs font-bold uppercase tracking-wider text-slate-500">Memory Control</p><h1 className="mt-0.5 text-lg font-bold tracking-tight text-slate-900">Memory & Context Settings</h1><p className="mt-0.5 text-xs text-slate-500">Review system memory retained for case plans.</p></div></div>
        <Button variant="outline" onClick={() => load(caseId)} disabled={loading} className="text-xs h-8"><RefreshCw className={cn("size-3.5 mr-1", loading && "animate-spin")} /> Refresh</Button>
      </header>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">{error}</div>}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_320px]">
        <div className="space-y-5">
          <Card className="border-slate-200 bg-white shadow-2xs"><CardHeader><CardTitle className="flex items-center gap-2 text-xs font-bold text-slate-900"><Settings2 className="size-4 text-slate-700" /> Memory Controls</CardTitle></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2">
            {[[memoryEnabled, setMemoryEnabled, "Use memory in planning", "Include case context and preferences in plans."], [learningEnabled, setLearningEnabled, "Learn from completed work", "Save findings and reports after runs."]].map(([enabled, setEnabled, title, detail]) => <label key={title as string} className="flex cursor-pointer items-start justify-between gap-3 rounded border border-slate-200 p-3.5 transition hover:border-slate-400"><span><span className="block text-xs font-bold text-slate-900">{title as string}</span><span className="mt-0.5 block text-[11px] leading-4 text-slate-500">{detail as string}</span></span><input type="checkbox" checked={enabled as boolean} onChange={(event) => (setEnabled as (value: boolean) => void)(event.target.checked)} className="mt-0.5 size-4 accent-slate-900" /></label>)}
          </CardContent></Card>

          <Card className="border-slate-200 bg-white shadow-2xs"><CardHeader><CardTitle className="flex items-center gap-2 text-xs font-bold text-slate-900"><Sparkles className="size-4 text-slate-700" /> Preference Editor</CardTitle></CardHeader><CardContent><form onSubmit={savePreference} className="grid gap-3"><div className="grid gap-3 sm:grid-cols-2"><div><Label htmlFor="preference-type" className="text-xs">Preference type</Label><select id="preference-type" value={draft.type} onChange={(event) => setDraft((current) => ({ ...current, type: event.target.value as PreferenceType }))} className="mt-1 h-8 w-full rounded border border-slate-300 bg-white px-2 text-xs text-slate-800 outline-none">{Object.entries(typeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div><Label htmlFor="preference-key" className="text-xs">Preference name</Label><Input id="preference-key" value={draft.key} onChange={(event) => setDraft((current) => ({ ...current, key: event.target.value }))} placeholder="e.g. concise_risk_summary" className="mt-1 h-8 border-slate-300 text-xs" /></div></div><div><Label htmlFor="preference-value" className="text-xs">Preference value</Label><textarea id="preference-value" value={draft.value} onChange={(event) => setDraft((current) => ({ ...current, value: event.target.value }))} rows={4} className="mt-1 w-full rounded border border-slate-300 bg-slate-50 p-2.5 font-mono text-xs text-slate-900 outline-none" /></div><div className="flex justify-end"><Button type="submit" disabled={saving || !draft.key.trim()} className="bg-slate-900 text-white hover:bg-slate-800 text-xs h-8"><Plus className="size-3 mr-1" /> {saving ? "Saving..." : "Save Preference"}</Button></div></form></CardContent></Card>

          <Card className="border-slate-200 bg-white shadow-2xs"><CardHeader><div className="flex flex-wrap items-center justify-between gap-3"><div><CardTitle className="flex items-center gap-2 text-xs font-bold text-slate-900"><FileText className="size-4 text-slate-700" /> Case Memory</CardTitle><p className="mt-0.5 text-[11px] text-slate-500">Case-specific retained findings and execution summaries.</p></div><select value={caseId} onChange={(event) => setCaseId(event.target.value)} className="h-8 max-w-56 rounded border border-slate-300 bg-white px-2 text-xs text-slate-800">{cases.length ? cases.map((item) => <option key={item.id} value={item.id}>{item.title}</option>) : <option>No cases</option>}</select></div></CardHeader><CardContent><div className="space-y-2">{loading ? <p className="py-6 text-center text-xs text-slate-400">Loading memory…</p> : memories.length ? memories.map((memory) => <article key={memory.id} className="rounded border border-slate-200 p-3"><div className="flex items-center justify-between gap-3"><span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-800">{humanize(memory.memory_type)}</span>{memory.memory_key && <span className="truncate text-xs text-slate-400">{memory.memory_key}</span>}</div><p className="mt-1.5 text-xs leading-relaxed text-slate-800">{memory.content}</p></article>) : <div className="rounded border border-dashed border-slate-200 py-8 text-center text-xs text-slate-400">No retained memory for this case.</div>}</div></CardContent></Card>
        </div>

        <aside className="space-y-5"><Card className="border-slate-200 bg-white shadow-2xs"><CardHeader><CardTitle className="flex items-center gap-2 text-xs font-bold text-slate-900"><Lightbulb className="size-4 text-slate-700" /> Planner Context Preview</CardTitle></CardHeader><CardContent className="space-y-3"><p className="text-xs text-slate-500">Context provided to planning algorithms.</p><div><p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Case memory</p><div className="mt-1.5 space-y-1.5">{memoryEnabled && planningMemory.length ? planningMemory.map((memory) => <div key={memory.id} className="rounded border border-slate-200 bg-slate-50 p-2 text-xs text-slate-800"><span className="font-bold text-slate-900">{humanize(memory.memory_type)}</span><p className="mt-0.5 line-clamp-2 text-[11px] text-slate-600">{memory.content}</p></div>) : <p className="text-xs text-slate-400">No matching memories.</p>}</div></div><div><p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">User preferences</p><div className="mt-1.5 space-y-1.5">{memoryEnabled && planningPreferences.length ? planningPreferences.map((preference) => <div key={preference.id} className="rounded border border-slate-200 bg-slate-50 p-2"><p className="text-xs font-semibold text-slate-800">{preference.preference_key}</p><p className="mt-0.5 text-[10px] text-slate-500">{typeLabels[preference.preference_type]} · {preference.confidence}% confidence</p></div>) : <p className="text-xs text-slate-400">No preferences.</p>}</div></div></CardContent></Card>

          <Card className="border-slate-200 bg-white shadow-2xs"><CardHeader><CardTitle className="flex items-center gap-2 text-xs font-bold text-slate-900"><History className="size-4 text-slate-700" /> Memory Timeline</CardTitle></CardHeader><CardContent><div className="space-y-3">{recentlyLearned.length ? recentlyLearned.map((preference, index) => <div key={preference.id} className="relative flex gap-2.5"><span className="relative z-10 flex size-5 shrink-0 items-center justify-center rounded-full border border-slate-300 bg-slate-100 text-slate-700">{index === 0 ? <Sparkles className="size-3" /> : <Clock3 className="size-3" />}</span>{index < recentlyLearned.length - 1 && <span className="absolute left-2.5 top-5 h-6 w-px bg-slate-200" /><div className="pb-1"><p className="text-xs font-semibold text-slate-900">{preference.preference_key}</p><p className="mt-0.5 text-[10px] text-slate-500">{relativeTime(preference.last_used_at)} · {preference.usage_count} uses</p></div></div>) : <p className="py-2 text-xs text-slate-400">No learned preferences.</p>}</div></CardContent></Card>

          <Card className="border-slate-200 bg-white shadow-2xs"><CardHeader><CardTitle className="flex items-center gap-2 text-xs font-bold text-slate-900"><Check className="size-4 text-slate-700" /> Recently Learned</CardTitle></CardHeader><CardContent><div className="space-y-1.5">{recentlyLearned.map((preference) => <button type="button" key={preference.id} onClick={() => editPreference(preference)} className="w-full rounded border border-slate-200 p-2 text-left hover:border-slate-400 hover:bg-slate-50"><p className="text-xs font-semibold text-slate-900">{preference.preference_key}</p><p className="mt-0.5 text-[10px] text-slate-500">{typeLabels[preference.preference_type]}</p></button>)}</div></CardContent></Card></aside>
      </div>
    </div>
  )
}
