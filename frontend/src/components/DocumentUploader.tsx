"use client"

import { useState, useRef, useCallback } from "react"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import api from "@/lib/api"

type ProcessingStage = "idle" | "uploading" | "parsing" | "chunking" | "embedding" | "ready" | "error"

const STAGE_LABELS: Record<ProcessingStage, string> = {
  idle: "",
  uploading: "Uploading",
  parsing: "Parsing",
  chunking: "Chunking",
  embedding: "Embedding",
  ready: "Ready",
  error: "Failed",
}

const STAGE_COLORS: Record<ProcessingStage, string> = {
  idle: "",
  uploading: "bg-slate-100 text-slate-800 border-slate-300",
  parsing: "bg-slate-100 text-slate-800 border-slate-300",
  chunking: "bg-slate-100 text-slate-800 border-slate-300",
  embedding: "bg-slate-100 text-slate-800 border-slate-300",
  ready: "bg-slate-900 text-white border-slate-900",
  error: "bg-red-50 text-red-700 border-red-200",
}

const PIPELINE_STAGES: ProcessingStage[] = ["uploading", "parsing", "chunking", "embedding", "ready"]

interface DocumentUploaderProps {
  caseId: string
  onUploadComplete: () => void
}

export function DocumentUploader({ caseId, onUploadComplete }: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [stage, setStage] = useState<ProcessingStage>("idle")
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [docType, setDocType] = useState("")
  const [version, setVersion] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const stageTimerRef = useRef<NodeJS.Timeout | null>(null)

  const simulateProcessingStages = (startIndex: number = 1) => {
    const stages: ProcessingStage[] = ["parsing", "chunking", "embedding"]
    let i = startIndex - 1
    const tick = () => {
      if (i < stages.length) {
        setStage(stages[i])
        i++
        stageTimerRef.current = setTimeout(tick, 2500)
      }
    }
    tick()
  }

  const handleUpload = async (file: File) => {
    if (!file || file.type !== "application/pdf") {
      alert("Only PDF files are allowed.")
      return
    }

    setSelectedFile(file)
    setStage("uploading")
    setUploadProgress(0)

    const formData = new FormData()
    formData.append("file", file)
    if (docType) formData.append("document_type", docType)
    if (version) formData.append("version", version)

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 80) { clearInterval(progressInterval); return 80 }
          return prev + 10
        })
      }, 150)

      stageTimerRef.current = setTimeout(() => {
        setUploadProgress(100)
        simulateProcessingStages()
      }, 1200)

      await api.post(`/cases/${caseId}/documents`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })

      if (stageTimerRef.current) clearTimeout(stageTimerRef.current)
      setStage("ready")
      setUploadProgress(100)

      setTimeout(() => {
        setStage("idle")
        setSelectedFile(null)
        setDocType("")
        setVersion("")
        setUploadProgress(0)
        onUploadComplete()
      }, 1500)
    } catch {
      if (stageTimerRef.current) clearTimeout(stageTimerRef.current)
      setStage("error")
      setTimeout(() => {
        setStage("idle")
        setSelectedFile(null)
        setUploadProgress(0)
      }, 3000)
    }
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleUpload(file)
  }, [caseId, docType, version])

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const onDragLeave = useCallback(() => setIsDragging(false), [])

  const isProcessing = stage !== "idle"
  const stageIndex = PIPELINE_STAGES.indexOf(stage)

  return (
    <div className="space-y-4 font-sans text-slate-900">
      {/* Metadata inputs */}
      {!isProcessing && (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="text-xs text-slate-600">Document Type <span className="text-slate-400">(optional)</span></Label>
            <Input
              placeholder="e.g. NDA, Contract, Brief"
              value={docType}
              onChange={e => setDocType(e.target.value)}
              className="bg-white border-slate-300 text-xs h-8"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-slate-600">Version <span className="text-slate-400">(optional)</span></Label>
            <Input
              placeholder="e.g. v1.0, Draft 2"
              value={version}
              onChange={e => setVersion(e.target.value)}
              className="bg-white border-slate-300 text-xs h-8"
            />
          </div>
        </div>
      )}

      {/* Drop Zone */}
      {!isProcessing ? (
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`
            relative border border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-150
            ${isDragging
              ? "border-slate-900 bg-slate-100"
              : "border-slate-300 hover:border-slate-500 bg-slate-50/50 hover:bg-slate-50"
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f) }}
          />
          <div className="flex flex-col items-center gap-2">
            <p className="text-xs font-medium text-slate-800">
              Drag & drop your PDF file here, or <span className="underline font-semibold">browse</span>
            </p>
            <p className="text-[11px] text-slate-500">Only PDF files are supported</p>
          </div>
        </div>
      ) : (
        /* Processing State */
        <div className="border border-slate-200 rounded-lg p-4 space-y-4 bg-white">
          <div className="flex items-center gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-900 truncate">{selectedFile?.name}</p>
              <p className="text-[11px] text-slate-500">{selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : ""}</p>
            </div>
            <Badge variant="outline" className={`text-xs border ${STAGE_COLORS[stage]} flex-shrink-0`}>
              {stage === "ready" ? "Complete" : stage === "error" ? "Failed" : STAGE_LABELS[stage]}
            </Badge>
          </div>

          <Progress value={uploadProgress} className="h-1 bg-slate-100" />

          <div className="flex items-center gap-2 overflow-x-auto text-xs text-slate-600">
            {PIPELINE_STAGES.slice(0, -1).map((s, i) => {
              const done = stageIndex > i
              const active = stageIndex === i
              return (
                <div key={s} className="flex items-center gap-2 flex-shrink-0">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                    done ? "bg-slate-200 text-slate-900" :
                    active ? "bg-slate-900 text-white" :
                    "text-slate-400"
                  }`}>
                    {STAGE_LABELS[s]}
                  </span>
                  {i < 3 && <span className="text-slate-300">&rarr;</span>}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
