"use client"

import { useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"

interface Document {
  id: string
  filename: string
  storage_path: string
}

interface PDFPreviewModalProps {
  doc: Document | null
  onClose: () => void
  pageNumber?: number | null
}

export function PDFPreviewModal({ doc, onClose, pageNumber }: PDFPreviewModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onClose])

  if (!doc) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={e => { if (e.target === overlayRef.current) onClose() }}
    >
      <div className="relative flex flex-col w-full max-w-4xl h-[85vh] bg-white border border-slate-300 rounded-lg shadow-xl overflow-hidden font-sans text-slate-900">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-200 flex-shrink-0 bg-slate-50">
          <div className="flex items-center gap-2">
            <p className="text-xs font-bold text-slate-900 truncate max-w-sm">{doc.filename}</p>
            {pageNumber && <span className="rounded bg-slate-900 text-white px-2 py-0.5 text-[10px] font-semibold">Page {pageNumber}</span>}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-6 w-6 p-0 text-slate-500 hover:text-slate-900"
          >
            ✕
          </Button>
        </div>

        {/* Viewer */}
        <div className="flex-1 bg-slate-100">
          <iframe
            src={`/api/pdf-proxy?path=${encodeURIComponent(doc.storage_path)}${pageNumber ? `&page=${pageNumber}` : ""}`}
            className="w-full h-full border-0"
            title={doc.filename}
          />
        </div>
      </div>
    </div>
  )
}
