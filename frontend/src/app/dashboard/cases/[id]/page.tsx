"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import api from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Label } from "@/components/ui/label"

export default function CaseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const caseId = params.id as string

  const [caseData, setCaseData] = useState<any>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)

  const fetchCaseDetails = async () => {
    try {
      const [caseRes, docsRes] = await Promise.all([
        api.get(`/cases/${caseId}`),
        api.get(`/cases/${caseId}/documents`)
      ])
      setCaseData(caseRes.data)
      setDocuments(docsRes.data)
    } catch (error) {
      console.error("Failed to fetch case details:", error)
      router.push("/dashboard") // Redirect if case not found
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (caseId) fetchCaseDetails()
  }, [caseId])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return
    const file = e.target.files[0]
    
    const formData = new FormData()
    formData.append("file", file)

    setUploading(true)
    try {
      await api.post(`/cases/${caseId}/documents`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      })
      // Refresh documents after upload
      fetchCaseDetails()
    } catch (error) {
      console.error("Failed to upload document:", error)
      alert("Failed to upload document. Please ensure it's a PDF.")
    } finally {
      setUploading(false)
      e.target.value = "" // Reset input
    }
  }

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm("Delete this document?")) return
    try {
      await api.delete(`/cases/${caseId}/documents/${docId}`)
      fetchCaseDetails()
    } catch (error) {
      console.error("Failed to delete document:", error)
    }
  }

  if (loading) return <div>Loading case...</div>
  if (!caseData) return null

  return (
    <div className="space-y-6">
      <div>
        <Button variant="outline" onClick={() => router.push("/dashboard")} className="mb-4">
          &larr; Back to Dashboard
        </Button>
        <h2 className="text-3xl font-bold tracking-tight">{caseData.title}</h2>
        <p className="text-gray-500 mt-2">{caseData.description}</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Documents</CardTitle>
          <div>
            <input 
              type="file" 
              accept=".pdf" 
              id="file-upload" 
              className="hidden" 
              onChange={handleFileUpload}
              disabled={uploading}
            />
            <Label htmlFor="file-upload" className="cursor-pointer">
              <Button asChild disabled={uploading}>
                <span>{uploading ? "Uploading..." : "Upload PDF"}</span>
              </Button>
            </Label>
          </div>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <div className="text-center text-gray-500 py-8">No documents uploaded yet.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Size (Bytes)</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map(doc => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">{doc.filename}</TableCell>
                    <TableCell>{doc.size_bytes}</TableCell>
                    <TableCell>{new Date(doc.created_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteDoc(doc.id)}>
                        Delete
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
