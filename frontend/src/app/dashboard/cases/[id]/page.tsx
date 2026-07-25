"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import api from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DocumentUploader } from "@/components/DocumentUploader"
import { DocumentCard } from "@/components/DocumentCard"
import { PDFPreviewModal } from "@/components/PDFPreviewModal"
import { ExecutionWorkspace } from "@/components/ExecutionWorkspace"

interface Document {
  id: string
  filename: string
  size_bytes: number
  created_at: string
  document_type?: string
  version?: string
  content_type: string
  storage_path: string
}

interface CaseData {
  id: string
  title: string
  description?: string
  created_at: string
}

export default function CaseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const caseId = params.id as string

  const [caseData, setCaseData] = useState<CaseData | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null)
  const [previewPage, setPreviewPage] = useState<number | null>(null)
  const [uploaderKey, setUploaderKey] = useState(0)

  const fetchCaseDetails = useCallback(async () => {
    try {
      const [caseRes, docsRes] = await Promise.all([
        api.get(`/cases/${caseId}`),
        api.get(`/cases/${caseId}/documents`)
      ])
      setCaseData(caseRes.data)
      setDocuments(docsRes.data)
    } catch {
      router.push("/dashboard")
    } finally {
      setLoading(false)
    }
  }, [caseId, router])

  useEffect(() => {
    if (caseId) fetchCaseDetails()
  }, [caseId, fetchCaseDetails])

  const handleUploadComplete = () => {
    // Reset uploader and refresh the list
    setUploaderKey(k => k + 1)
    fetchCaseDetails()
  }

  const handleDeleteDoc = async (docId: string) => {
    try {
      await api.delete(`/cases/${caseId}/documents/${docId}`)
      setDocuments(prev => prev.filter(d => d.id !== docId))
    } catch {
      console.error("Failed to delete document")
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-zinc-500">Loading case...</p>
        </div>
      </div>
    )
  }

  if (!caseData) return null

  const totalSize = documents.reduce((sum, d) => sum + d.size_bytes, 0)
  const formatBytes = (b: number) =>
    b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / (1024 * 1024)).toFixed(1)} MB`

  return (
    <>
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-1.5 text-sm text-zinc-500 hover:text-zinc-300 transition-colors mb-5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-zinc-100">{caseData.title}</h1>
              {caseData.description && (
                <p className="text-zinc-500 mt-1.5 text-sm leading-relaxed max-w-xl">{caseData.description}</p>
              )}
            </div>
            <Badge variant="outline" className="border-zinc-700 text-zinc-400 flex-shrink-0 mt-1">
              {documents.length} {documents.length === 1 ? "document" : "documents"}
            </Badge>
          </div>

          {/* Stats strip */}
          {documents.length > 0 && (
            <div className="flex items-center gap-6 mt-4 pt-4 border-t border-zinc-800/60">
              <div>
                <p className="text-xs text-zinc-600 uppercase tracking-wide">Total size</p>
                <p className="text-sm font-medium text-zinc-300 mt-0.5">{formatBytes(totalSize)}</p>
              </div>
              <div className="w-px h-8 bg-zinc-800" />
              <div>
                <p className="text-xs text-zinc-600 uppercase tracking-wide">Last upload</p>
                <p className="text-sm font-medium text-zinc-300 mt-0.5">
                  {new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                    .format(new Date(documents[documents.length - 1]?.created_at))}
                </p>
              </div>
              <div className="w-px h-8 bg-zinc-800" />
              <div>
                <p className="text-xs text-zinc-600 uppercase tracking-wide">Processing</p>
                <p className="text-sm font-medium text-emerald-400 mt-0.5">All ready</p>
              </div>
            </div>
          )}
        </div>

        <ExecutionWorkspace caseId={caseId} />

        {/* Upload Section */}
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-zinc-200">Upload Document</CardTitle>
            <CardDescription className="text-zinc-500 text-sm">
              PDFs are automatically parsed, chunked, and embedded for semantic search.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DocumentUploader
              key={uploaderKey}
              caseId={caseId}
              onUploadComplete={handleUploadComplete}
            />
          </CardContent>
        </Card>

        {/* Documents List */}
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base text-zinc-200">Documents</CardTitle>
              <CardDescription className="text-zinc-500 text-sm mt-0.5">
                {documents.length === 0 ? "No documents yet" : `${documents.length} document${documents.length > 1 ? "s" : ""} indexed and ready`}
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchCaseDetails}
              className="h-7 px-2.5 text-xs text-zinc-500 hover:text-zinc-300"
            >
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-14 h-14 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-zinc-400">No documents yet</p>
                <p className="text-xs text-zinc-600 mt-1">Upload a PDF above to get started</p>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map(doc => (
                  <DocumentCard
                    key={doc.id}
                    doc={doc}
                    onDelete={handleDeleteDoc}
                    onPreview={d => {
                      setPreviewPage(null)
                      setPreviewDoc(d as Document)
                    }}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* PDF Preview Modal */}
      <PDFPreviewModal
        doc={previewDoc}
        pageNumber={previewPage}
        onClose={() => {
          setPreviewDoc(null)
          setPreviewPage(null)
        }}
      />
    </>
  )
}
