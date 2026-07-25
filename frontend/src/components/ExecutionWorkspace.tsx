"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import {
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
  }
  error?: { node: string; message: string }
}

interface ExecutionResult {
  execution_id: string
  case_id: string
  user_id: string
  request: string
  workflow: WorkflowResult
}

interface TimelineNode {
  id: string
  label: string
  description: string
  icon: typeof Workflow
}

const timeline: TimelineNode[] = [
  { id: "planner", label: "Intent & plan", description: "Classifies legal goal and outlines execution steps.", icon: GitBranch },
  { id: "researcher", label: "Legal retrieval", description: "Queries pgvector for case documents and precedents.", icon: FileSearch },
  { id: "analyzer", label: "Clause & risk analysis", description: "Evaluates key clauses and risk exposure.", icon: Layers3 },
  { id: "writer", label: "Draft generation", description: "Drafts grounded legal analysis.", icon: FilePenLine },
  { id: "reviewer", label: "Review & verification", description: "Verifies claims against source documents.", icon: ShieldCheck },
]

function formatDuration(ms: number | null): string {
  if (ms === null) return "0.0s"
  return `${(ms / 1000).toFixed(1)}s`
}

function humanize(text: string): string {
  return text.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}

function reasoningSummary(nodeId: string, workflow?: WorkflowResult): string {
  if (!workflow) return "Pending execution."

  switch (nodeId) {
    case "planner":
      return workflow.intent
        ? `Intent: ${humanize(workflow.intent.task_type)} (${Math.round(workflow.intent.confidence * 100)}% confidence)`
        : "Plan generated."
    case "researcher":
      return workflow.research?.findings
        ? `Retrieved ${workflow.research.findings.length} relevant document passages.`
        : "Passages retrieved from pgvector."
    case "analyzer":
      return workflow.analysis
        ? "Clause structure and risk factors evaluated."
        : "Risk factors evaluated."
    case "writer":
      return workflow.writer?.draft
        ? "Draft answer generated with citations."
        : "Draft answer generated."
    case "reviewer":
      if (!workflow.reviewer?.checks) return "Quality and citation checks completed."
      const total = workflow.reviewer.checks.length
      const passed = workflow.reviewer.checks.filter((check) => check.passed).length
      return `${passed}/${total} verification checks passed.`
    default:
      return "Step complete."
  }
}

export function ExecutionWorkspace({ caseId }: { caseId: string }) {
  const [request, setRequest] = useState("")
  const [execution, setExecution] = useState<ExecutionResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
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
        setError("The execution service could not be reached. Please try again.")
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
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-2xs text-slate-900 font-sans">
      <header className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-slate-100 text-slate-900">
            <Workflow className="size-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Task Execution Engine</h2>
            <p className="mt-0.5 text-xs text-slate-500">Plan, retrieval evidence, and reviewed legal analysis.</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600 self-start md:self-auto">
          <Clock3 className="size-3.5 text-slate-500" /> {formatDuration(duration)}
        </div>
      </header>

      <div className="grid xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-slate-50/50 p-4 xl:border-r xl:border-b-0">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Execution Timeline</p>
            {isRunning && <span className="flex items-center gap-1 text-[11px] text-slate-900 font-medium"><CircleDashed className="size-3 animate-spin" /> Running</span>}
          </div>
          <div className="space-y-0.5">
            {timeline.map((node, index) => {
              const status = nodeStatus(node, index)
              const Icon = node.icon
              return (
                <div key={node.id} className="relative flex gap-3 py-2">
                  {index < timeline.length - 1 && <span className="absolute top-8 bottom-[-8px] left-[11px] w-px bg-slate-200" />}
                  <span className={cn("relative z-10 flex size-6 shrink-0 items-center justify-center rounded border text-xs", status === "complete" ? "border-slate-900 bg-slate-900 text-white" : status === "active" ? "border-slate-900 bg-slate-100 text-slate-900" : status === "failed" ? "border-red-300 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-400")}>
                    {status === "complete" ? <CheckCircle2 className="size-3" /> : status === "active" ? <CircleDashed className="size-3 animate-spin" /> : <Icon className="size-3" />}
                  </span>
                  <div className="min-w-0 pt-0.5"><p className={cn("text-xs font-semibold", status === "pending" ? "text-slate-400" : "text-slate-900")}>{node.label}</p><p className="mt-0.5 text-[11px] leading-3.5 text-slate-500">{node.description}</p></div>
                </div>
              )
            })}
          </div>
        </aside>

        <div className="min-w-0 p-5">
          <form onSubmit={execute} className="rounded-lg border border-slate-300 bg-white p-2 focus-within:border-slate-900">
            <textarea value={request} onChange={(event) => setRequest(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} placeholder="Review this contract, compare agreements, find risk factors..." rows={2} disabled={isRunning} className="w-full resize-none bg-transparent px-2 py-1 text-xs text-slate-900 placeholder:text-slate-400 outline-none disabled:cursor-not-allowed" />
            <div className="flex items-center justify-between px-1 pt-1 border-t border-slate-100"><span className="text-[11px] text-slate-400">Creates an auditable execution record</span><Button type="submit" disabled={!request.trim() || isRunning} className="bg-slate-900 text-white hover:bg-slate-800 text-xs h-8 px-3 rounded font-medium"><Play className="size-3 mr-1" /> {isRunning ? "Executing..." : "Execute Task"}</Button></div>
          </form>

          {error && <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700"><TriangleAlert className="size-4 shrink-0" />{error}</div>}

          <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_200px]">
            <div className="rounded-lg border border-slate-200 bg-white">
              <button type="button" onClick={() => setIsPlanExpanded((current) => !current)} className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-slate-50">
                <span><span className="block text-xs font-bold text-slate-900">Execution Plan</span><span className="mt-0.5 block text-[11px] text-slate-500">{planner ? `${humanize(planner.intent.task_type)} · ${planner.steps.length} steps` : "Plan will appear here after execution"}</span></span>
                {isPlanExpanded ? <ChevronUp className="size-4 text-slate-400" /> : <ChevronDown className="size-4 text-slate-400" />}
              </button>
              {isPlanExpanded && <div className="border-t border-slate-200 px-4 py-3">
                {planner ? <div className="space-y-2">{planner.steps.map((step, index) => <div key={step.step_id} className="flex gap-2.5"><span className="flex size-4 shrink-0 items-center justify-center rounded border border-slate-300 bg-slate-100 text-[10px] font-bold text-slate-700">{index + 1}</span><div><p className="text-xs font-semibold text-slate-800">{step.description}</p><p className="mt-0.5 text-[11px] text-slate-500">Output: {step.expected_output}</p></div></div>)}</div> : <p className="py-2 text-xs text-slate-400">Run a task to view the execution plan.</p>}
              </div>}
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-3.5"><p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Current Agent</p><div className="mt-2 flex items-center gap-2"><span className={cn("flex size-7 items-center justify-center rounded border", isRunning ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600")}><CircleDashed className={cn("size-3.5", isRunning && "animate-spin")} /></span><p className="text-xs font-semibold text-slate-900">{currentAgent}</p></div></div>
          </div>

          <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Agent Summaries</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">{timeline.slice(0, -1).map((node) => <div key={node.id} className="rounded border border-slate-200 bg-slate-50/50 p-2.5"><p className="text-xs font-semibold text-slate-800">{node.label}</p><p className="mt-0.5 text-[11px] text-slate-500">{reasoningSummary(node.id, workflow)}</p></div>)}</div>
          </div>

          <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3"><div><p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Generated Analysis</p></div>{workflow?.final_response && <span className="rounded bg-slate-900 text-white px-2 py-0.5 text-[10px] font-semibold">{workflow.final_response.review_passed ? "Verified" : "Review Needed"}</span>}</div>
            {workflow?.final_response ? <div className="mt-3 whitespace-pre-wrap text-xs leading-relaxed text-slate-800">{workflow.final_response.content}</div> : <div className="mt-3 rounded border border-dashed border-slate-200 p-6 text-center text-xs text-slate-400">Analysis output will appear here upon execution.</div>}
            {sourceIds.length > 0 && <div className="mt-3 border-t border-slate-200 pt-2.5"><p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Sources</p><div className="mt-1.5 flex flex-wrap gap-1.5">{sourceIds.map((sourceId, index) => <span key={sourceId} className="rounded border border-slate-200 bg-slate-100 px-2 py-0.5 text-[11px] text-slate-700 font-medium">Source {index + 1} · {sourceId.slice(0, 8)}</span>)}</div></div>}
          </div>
        </div>
      </div>
    </section>
  )
}
