"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface Document {
  id: string
  filename: string
  size_bytes: number
  created_at: string
  document_type?: string
  version?: string
  content_type: string
}

interface DocumentCardProps {
  doc: Document
  onDelete: (id: string) => void
  onPreview: (doc: Document) => void
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d)
}

export function DocumentCard({ doc, onDelete, onPreview }: DocumentCardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false)

  const handleDelete = () => {
    if (confirmDelete) {
      onDelete(doc.id)
    } else {
      setConfirmDelete(true)
      setTimeout(() => setConfirmDelete(false), 3000)
    }
  }

  return (
    <div className="group flex items-center gap-4 p-4 rounded-xl border border-zinc-800 bg-zinc-900/30 hover:bg-zinc-900/60 hover:border-zinc-700 transition-all duration-200">
      {/* PDF icon */}
      <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0">
        <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
      </div>

      {/* Doc info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium text-zinc-200 truncate max-w-xs">{doc.filename}</p>
          {doc.document_type && (
            <Badge variant="outline" className="text-[10px] h-4 px-1.5 border-zinc-700 text-zinc-400">
              {doc.document_type}
            </Badge>
          )}
          {doc.version && (
            <Badge variant="outline" className="text-[10px] h-4 px-1.5 border-zinc-700 text-zinc-500">
              {doc.version}
            </Badge>
          )}
          {/* "Ready" badge — all documents in the list are processed */}
          <Badge variant="outline" className="text-[10px] h-4 px-1.5 border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
            ✓ Ready
          </Badge>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-zinc-500">{formatBytes(doc.size_bytes)}</span>
          <span className="text-zinc-700">·</span>
          <span className="text-xs text-zinc-500">{formatDate(doc.created_at)}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2.5 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
          onClick={() => onPreview(doc)}
        >
          <svg className="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          Preview
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDelete}
          className={`h-7 px-2.5 text-xs transition-colors ${
            confirmDelete
              ? "text-red-400 bg-red-500/10 hover:bg-red-500/20"
              : "text-zinc-500 hover:text-red-400 hover:bg-red-500/10"
          }`}
        >
          {confirmDelete ? "Confirm?" : "Delete"}
        </Button>
      </div>
    </div>
  )
}
