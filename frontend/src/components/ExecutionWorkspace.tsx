"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import {
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleDashed,
  Clock3,
  FilePenLine,
  FileSearch,
  GitBranch,
  Layers3,
  Play,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Workflow,
} from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

type StepType = "retrieve" | "analyze" | "research" | "generate" | "review"

interface PlanStep {
  step_id: string
  step_type: StepType
  description: string
  inputs: string[]
  expected_output: string
  depends_on: string[]
}

interface ExecutionPlan {
  plan_id: string
  status: "planned"
  intent: { task_type: string; confidence: number; normalized_request: string }
  steps: PlanStep[]
}

interface WorkerSummary {
  findings?: unknown[]
  draft?: { content: string; source_ids: string[] }
  checks?: { name: string; passed: boolean; detail: string }[]
}

interface WorkflowResult {
  status: "completed" | "failed"
  trace: string[]
  intent?: { task_type: string; confidence: number }
  plan?: ExecutionPlan
  research?: WorkerSummary
  analysis?: WorkerSummary
  writer?: WorkerSummary
  reviewer?: WorkerSummary
  final_response?: {
    content: string
    source_ids: string[]
    review_passed: boolean
    requires_human_review: boolean
  }
  error?: { node: string; message: string }
}

interface ExecutionResult {
  execution_id: string
  status: "completed" | "failed"
  workflow: WorkflowResult
}

interface TimelineNode {
  id: string
  label: string
  description: string
  icon: typeof BrainCircuit
}

const timeline: TimelineNode[] = [
  { id: "intent", label: "Intent detection", description: "Classifying the requested legal task", icon: BrainCircuit },
  { id: "planner", label: "Planning", description: "Building a structured execution plan", icon: GitBranch },
  { id: "research", label: "Research agent", description: "Retrieving grounded document evidence", icon: FileSearch },
  { id: "analysis", label: "Analysis agent", description: "Organizing evidence into findings", icon: Layers3 },
  { id: "writer", label: "Writer agent", description: "Composing the draft response", icon: FilePenLine },
  { id: "reviewer", label: "Reviewer agent", description: "Checking source coverage and output", icon: ShieldCheck },
  { id: "finalize", label: "Final response", description: "Packaging the reviewed result", icon: Sparkles },
]

function formatDuration(milliseconds: number | null) {
  if (milliseconds === null) return "—"
  if (milliseconds < 1_000) return `${milliseconds} ms`
  return `${(milliseconds / 1_000).toFixed(1)} s`
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function reasoningSummary(id: string, workflow?: WorkflowResult) {
  if (!workflow) return "Awaiting execution."
  if (id === "research") return `${workflow.research?.findings?.length ?? 0} evidence items prepared for analysis.`
  if (id === "analysis") return `${workflow.analysis?.findings?.length ?? 0} reviewable findings produced.`
  if (id === "writer") return workflow.writer?.draft?.content ? "Draft assembled from the structured findings." : "Draft is pending."
  if (id === "reviewer") {
    const checks = workflow.reviewer?.checks ?? []
    return checks.length ? `${checks.filter((check) => check.passed).length}/${checks.length} review checks passed.` : "Review checks are pending."
  }
  if (id === "planner") return workflow.plan ? `${workflow.plan.steps.length} planned execution steps.` : "Execution plan is pending."
  if (id === "intent") return workflow.intent ? `Detected ${humanize(workflow.intent.task_type)}.` : "Intent classification is pending."
  return workflow.final_response ? "Reviewed result is ready for delivery." : "Final response is pending."
}

export function ExecutionWorkspace({ caseId }: { caseId: string }) {
  const [request, setRequest] = useState("")
  const [execution, setExecution] = useState<ExecutionResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  const [startedAt, setStartedAt] = useState<number | null>(null)
  const [duration, setDuration] = useState<number | null>(null)
  const [isPlanExpanded, setIsPlanExpanded] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!isRunning) return
    const timer = window.setInterval(() => {
      setActiveIndex((current) => Math.min(current + 1, timeline.length - 1))
    }, 900)
    return () => window.clearInterval(timer)
  }, [isRunning])

  const workflow = execution?.workflow
  const completedTrace = workflow?.trace ?? []
  const planner = workflow?.plan
  const sourceIds = workflow?.final_response?.source_ids ?? workflow?.writer?.draft?.source_ids ?? []

  const currentAgent = useMemo(() => {
    if (!isRunning) return workflow?.status === "completed" ? "Execution complete" : "Ready to execute"
    return timeline[activeIndex]?.label ?? "Preparing execution"
  }, [activeIndex, isRunning, workflow?.status])

  const execute = async (event: FormEvent) => {
    event.preventDefault()
    const prompt = request.trim()
    if (!prompt || isRunning) return

    setError("")
    setExecution(null)
    setIsRunning(true)
    setActiveIndex(0)
    const started = performance.now()
    setStartedAt(started)
    setDuration(null)

    try {
      const response = await api.post<ExecutionResult>("/ai/execute", {
        case_id: caseId,
        request: prompt,
        top_k: 5,
      })
      setExecution(response.data)
    } catch (caught) {
      const failed = caught as { response?: { data?: ExecutionResult } }
      if (failed.response?.data?.workflow) {
        setExecution(failed.response.data)
        setError(failed.response.data.workflow.error?.message ?? "The execution did not complete.")
      } else {
        setError("The AI execution service could not be reached. Please try again.")
      }
    } finally {
      setDuration(Math.round(performance.now() - started))
      setIsRunning(false)
    }
  }

  const nodeStatus = (node: TimelineNode, index: number) => {
    if (workflow?.status === "failed" && workflow.error?.node === node.id) return "failed"
    if (completedTrace.includes(node.id)) return "complete"
    if (isRunning && index === activeIndex) return "active"
    return "pending"
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/20">
      <header className="flex flex-col gap-4 border-b border-zinc-800 px-5 py-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-300"><Workflow className="size-5" /></span>
          <div>
            <h2 className="text-base font-semibold text-zinc-100">AI execution workspace</h2>
            <p className="mt-0.5 text-xs text-zinc-500">Plan, agent activity, evidence, and reviewed output in one run.</p>
          </div>
        </div>
        <div className="flex items-center gap-2 self-start rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-400 md:self-auto">
          <Clock3 className="size-3.5 text-violet-400" /> {formatDuration(duration)}
        </div>
      </header>

      <div className="grid xl:grid-cols-[310px_minmax(0,1fr)]">
        <aside className="border-b border-zinc-800 bg-zinc-950/70 p-5 xl:border-r xl:border-b-0">
          <div className="mb-5 flex items-center justify-between">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">Execution timeline</p>
            {isRunning && <span className="flex items-center gap-1.5 text-[11px] text-violet-300"><CircleDashed className="size-3 animate-spin" /> Running</span>}
          </div>
          <div className="space-y-0.5">
            {timeline.map((node, index) => {
              const status = nodeStatus(node, index)
              const Icon = node.icon
              return (
                <div key={node.id} className="relative flex gap-3 py-2.5">
                  {index < timeline.length - 1 && <span className="absolute top-9 bottom-[-9px] left-[13px] w-px bg-zinc-800" />}
                  <span className={cn("relative z-10 flex size-7 shrink-0 items-center justify-center rounded-full border", status === "complete" ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : status === "active" ? "border-violet-500/40 bg-violet-500/15 text-violet-300" : status === "failed" ? "border-red-500/30 bg-red-500/10 text-red-400" : "border-zinc-800 bg-zinc-900 text-zinc-600")}>
                    {status === "complete" ? <CheckCircle2 className="size-3.5" /> : status === "active" ? <CircleDashed className="size-3.5 animate-spin" /> : <Icon className="size-3.5" />}
                  </span>
                  <div className="min-w-0 pt-0.5"><p className={cn("text-xs font-medium", status === "pending" ? "text-zinc-600" : "text-zinc-200")}>{node.label}</p><p className="mt-0.5 text-[11px] leading-4 text-zinc-600">{node.description}</p></div>
                </div>
              )
            })}
          </div>
        </aside>

        <div className="min-w-0 p-5 sm:p-6">
          <form onSubmit={execute} className="rounded-xl border border-zinc-700 bg-zinc-900/70 p-2 shadow-inner shadow-black/10 focus-within:border-violet-500/60">
            <textarea value={request} onChange={(event) => setRequest(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} placeholder="Review this contract, compare agreements, find risky clauses…" rows={2} disabled={isRunning} className="w-full resize-none bg-transparent px-2 py-1.5 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none disabled:cursor-not-allowed" />
            <div className="flex items-center justify-between px-1"><span className="text-[11px] text-zinc-600">Creates an auditable AI execution record</span><Button type="submit" disabled={!request.trim() || isRunning} className="bg-violet-600 text-white hover:bg-violet-500"><Play className="size-3.5" /> {isRunning ? "Executing" : "Execute"}</Button></div>
          </form>

          {error && <div className="mt-4 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3.5 py-3 text-sm text-red-200"><TriangleAlert className="size-4 shrink-0" />{error}</div>}

          <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px]">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
              <button type="button" onClick={() => setIsPlanExpanded((current) => !current)} className="flex w-full items-center justify-between px-4 py-3.5 text-left hover:bg-zinc-900/70">
                <span><span className="block text-sm font-medium text-zinc-200">Planner output</span><span className="mt-0.5 block text-xs text-zinc-500">{planner ? `${humanize(planner.intent.task_type)} · ${planner.steps.length} steps` : "Execution plan will appear here"}</span></span>
                {isPlanExpanded ? <ChevronUp className="size-4 text-zinc-500" /> : <ChevronDown className="size-4 text-zinc-500" />}
              </button>
              {isPlanExpanded && <div className="border-t border-zinc-800 px-4 py-3">
                {planner ? <div className="space-y-2.5">{planner.steps.map((step, index) => <div key={step.step_id} className="flex gap-3"><span className="flex size-5 shrink-0 items-center justify-center rounded-full border border-zinc-700 bg-zinc-950 text-[10px] text-zinc-400">{index + 1}</span><div><p className="text-xs font-medium text-zinc-300">{step.description}</p><p className="mt-1 text-[11px] text-zinc-600">Output: {step.expected_output}</p></div></div>)}</div> : <p className="py-3 text-sm text-zinc-600">Run an AI task to inspect the generated plan.</p>}
              </div>}
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4"><p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">Current agent</p><div className="mt-3 flex items-center gap-2"><span className={cn("flex size-8 items-center justify-center rounded-lg", isRunning ? "bg-violet-500/15 text-violet-300" : "bg-zinc-800 text-zinc-400")}><CircleDashed className={cn("size-4", isRunning && "animate-spin")} /></span><p className="text-sm font-medium text-zinc-200">{currentAgent}</p></div><p className="mt-3 text-xs leading-5 text-zinc-600">{isRunning ? "The execution graph is moving through its planned stages." : "Start an execution to see live agent activity."}</p></div>
          </div>

          <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">Agent summaries</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">{timeline.slice(0, -1).map((node) => <div key={node.id} className="rounded-lg border border-zinc-800/80 bg-zinc-950/50 px-3 py-2.5"><p className="text-xs font-medium text-zinc-300">{node.label}</p><p className="mt-1 text-[11px] leading-4 text-zinc-600">{reasoningSummary(node.id, workflow)}</p></div>)}</div>
          </div>

          <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="flex items-start justify-between gap-3"><div><p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">Generated final answer</p><p className="mt-1 text-xs text-zinc-600">Reviewed output from the execution engine.</p></div>{workflow?.final_response && <span className={cn("rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide", workflow.final_response.review_passed ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-300")}>{workflow.final_response.review_passed ? "Review passed" : "Review needed"}</span>}</div>
            {workflow?.final_response ? <div className="mt-4 whitespace-pre-wrap text-sm leading-6 text-zinc-300">{workflow.final_response.content}</div> : <div className="mt-4 rounded-lg border border-dashed border-zinc-800 px-3 py-6 text-center text-sm text-zinc-600">Your reviewed final answer will appear here.</div>}
            {sourceIds.length > 0 && <div className="mt-4 border-t border-zinc-800 pt-3"><p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">Grounding citations</p><div className="mt-2 flex flex-wrap gap-2">{sourceIds.map((sourceId, index) => <span key={sourceId} className="rounded-md border border-violet-500/20 bg-violet-500/10 px-2 py-1 text-[11px] text-violet-200">Source {index + 1} · {sourceId.slice(0, 8)}</span>)}</div></div>}
          </div>
        </div>
      </div>
    </section>
  )
}
