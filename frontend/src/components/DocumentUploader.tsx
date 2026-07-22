"use client"

import { useState, useRef, useCallback } from "react"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
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
  uploading: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  parsing: "bg-violet-500/15 text-violet-400 border-violet-500/30",
  chunking: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  embedding: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  ready: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  error: "bg-red-500/15 text-red-400 border-red-500/30",
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
      // Simulate upload progress to 80%, then hand off to server
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 80) { clearInterval(progressInterval); return 80 }
          return prev + 10
        })
      }, 150)

      // Start simulating backend stages while we wait for the response
      stageTimerRef.current = setTimeout(() => {
        setUploadProgress(100)
        simulateProcessingStages()
      }, 1200)

      await api.post(`/cases/${caseId}/documents`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })

      // Clear any pending timers and mark ready
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
    <div className="space-y-4">
      {/* Metadata inputs */}
      {!isProcessing && (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs text-zinc-400">Document Type <span className="text-zinc-600">(optional)</span></Label>
            <Input
              placeholder="e.g. NDA, MSA, Brief"
              value={docType}
              onChange={e => setDocType(e.target.value)}
              className="bg-zinc-900 border-zinc-700 text-sm h-8"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs text-zinc-400">Version <span className="text-zinc-600">(optional)</span></Label>
            <Input
              placeholder="e.g. v1.0, Draft 3"
              value={version}
              onChange={e => setVersion(e.target.value)}
              className="bg-zinc-900 border-zinc-700 text-sm h-8"
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
            relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
            ${isDragging
              ? "border-violet-500 bg-violet-500/10 scale-[1.01]"
              : "border-zinc-700 hover:border-zinc-500 hover:bg-zinc-900/50"
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
          <div className="flex flex-col items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${isDragging ? "bg-violet-500/20" : "bg-zinc-800"}`}>
              <svg className={`w-6 h-6 ${isDragging ? "text-violet-400" : "text-zinc-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-300">Drop your PDF here or <span className="text-violet-400">browse</span></p>
              <p className="text-xs text-zinc-600 mt-1">Only PDF files are supported</p>
            </div>
          </div>
        </div>
      ) : (
        /* Processing State */
        <div className="border border-zinc-800 rounded-xl p-6 space-y-5 bg-zinc-900/40">
          {/* File info */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-zinc-200 truncate">{selectedFile?.name}</p>
              <p className="text-xs text-zinc-500">{selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : ""}</p>
            </div>
            <Badge variant="outline" className={`text-xs border ${STAGE_COLORS[stage]} flex-shrink-0`}>
              {stage === "ready" ? "✓ Ready" : stage === "error" ? "✗ Failed" : (
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                  {STAGE_LABELS[stage]}...
                </span>
              )}
            </Badge>
          </div>

          {/* Progress bar */}
          <Progress value={uploadProgress} className="h-1.5 bg-zinc-800" />

          {/* Stage pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {PIPELINE_STAGES.slice(0, -1).map((s, i) => {
              const done = stageIndex > i
              const active = stageIndex === i
              return (
                <div key={s} className="flex items-center gap-2 flex-shrink-0">
                  <div className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-md transition-all duration-500 ${
                    done ? "text-emerald-400" :
                    active ? "text-zinc-200 bg-zinc-800" :
                    "text-zinc-600"
                  }`}>
                    {done ? (
                      <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : active ? (
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                    ) : (
                      <span className="w-1.5 h-1.5 rounded-full border border-current opacity-40" />
                    )}
                    {STAGE_LABELS[s]}
                  </div>
                  {i < 3 && <span className="text-zinc-700">→</span>}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
