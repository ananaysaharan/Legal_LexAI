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
    } font-sans finally {
      setLoading(false)
    }
  }, [caseId, router])

  useEffect(() => {
    if (caseId) fetchCaseDetails()
  }, [caseId, fetchCaseDetails])

  const handleUploadComplete = () => {
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
          <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-500 font-medium">Loading case...</p>
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
      <div className="max-w-6xl mx-auto space-y-6 text-slate-900 font-sans">
        {/* Header */}
        <div>
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-900 transition-colors mb-4"
          >
            &larr; Back to Cases
          </button>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">{caseData.title}</h1>
              {caseData.description && (
                <p className="text-slate-600 mt-1 text-xs leading-relaxed max-w-xl">{caseData.description}</p>
              )}
            </div>
            <Badge variant="outline" className="border-slate-300 text-slate-700 flex-shrink-0 mt-1">
              {documents.length} {documents.length === 1 ? "document" : "documents"}
            </Badge>
          </div>

          {/* Stats strip */}
          {documents.length > 0 && (
            <div className="flex items-center gap-6 mt-4 pt-3 border-t border-slate-200 text-xs">
              <div>
                <p className="text-[11px] text-slate-500 uppercase tracking-wide">Total size</p>
                <p className="font-semibold text-slate-800 mt-0.5">{formatBytes(totalSize)}</p>
              </div>
              <div className="w-px h-6 bg-slate-200" />
              <div>
                <p className="text-[11px] text-slate-500 uppercase tracking-wide">Last upload</p>
                <p className="font-semibold text-slate-800 mt-0.5">
                  {new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                    .format(new Date(documents[documents.length - 1]?.created_at))}
                </p>
              </div>
            </div>
          )}
        </div>

        <ExecutionWorkspace caseId={caseId} />

        {/* Upload Section */}
        <Card className="bg-white border-slate-200 shadow-2xs">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold text-slate-900">Upload Document</CardTitle>
            <CardDescription className="text-slate-500 text-xs">
              Upload PDF legal documents to index for search and research.
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
        <Card className="bg-white border-slate-200 shadow-2xs">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-sm font-bold text-slate-900">Documents</CardTitle>
              <CardDescription className="text-slate-500 text-xs mt-0.5">
                {documents.length === 0 ? "No documents uploaded" : `${documents.length} document${documents.length > 1 ? "s" : ""} available`}
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchCaseDetails}
              className="h-7 px-2 text-xs text-slate-600 hover:text-slate-900"
            >
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <p className="text-xs font-medium text-slate-600">No documents yet</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Upload a PDF above to get started</p>
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
