"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import api from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

export default function DashboardPage() {
  const [cases, setCases] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  const fetchCases = async () => {
    try {
      const res = await api.get("/cases/")
      setCases(res.data)
    } catch (error) {
      console.error("Failed to fetch cases:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCases()
  }, [])

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    setCreating(true)
    try {
      await api.post("/cases/", { title, description })
      setIsOpen(false)
      setTitle("")
      setDescription("")
      fetchCases()
    } catch (error) {
      console.error("Failed to create case:", error)
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteCase = async (id: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm("Are you sure you want to delete this case?")) return
    try {
      await api.delete(`/cases/${id}`)
      fetchCases()
    } catch (error) {
      console.error("Failed to delete case:", error)
    }
  }

  const filteredCases = cases.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.description && c.description.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Cases</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage your legal cases and associated discovery documents.
          </p>
        </div>

        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger render={<Button className="bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs h-9 px-4 rounded" />}>
            New Case
          </DialogTrigger>
          <DialogContent className="bg-white border border-slate-200 text-slate-900 max-w-md p-6">
            <DialogHeader>
              <DialogTitle className="text-base font-bold text-slate-900">
                New Legal Case
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateCase} className="space-y-4 mt-2">
              <div className="space-y-1">
                <Label htmlFor="title" className="text-xs font-medium text-slate-700">
                  Title <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="title"
                  placeholder="Case title or matter number"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="bg-white border-slate-300 text-slate-900 text-xs h-9"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="desc" className="text-xs font-medium text-slate-700">
                  Description
                </Label>
                <Input
                  id="desc"
                  placeholder="Optional notes or summary..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="bg-white border-slate-300 text-slate-900 text-xs h-9"
                />
              </div>
              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={creating}
                  className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs h-9 rounded"
                >
                  {creating ? "Creating..." : "Save Case"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filter and Search */}
      {cases.length > 0 && (
        <div className="flex items-center gap-3">
          <Input
            type="text"
            placeholder="Search cases..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-white border-slate-300 text-slate-900 text-xs h-9 max-w-sm"
          />
          <span className="text-xs text-slate-400">
            {filteredCases.length} case{filteredCases.length === 1 ? "" : "s"}
          </span>
        </div>
      )}

      {/* Cases List */}
      {loading ? (
        <div className="text-xs text-slate-500 py-8">Loading cases...</div>
      ) : cases.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg p-12 text-center space-y-3">
          <p className="text-sm font-medium text-slate-700">No cases created yet.</p>
          <p className="text-xs text-slate-500">Create a case to begin uploading documents.</p>
          <div>
            <Button
              onClick={() => setIsOpen(true)}
              className="bg-slate-900 hover:bg-slate-800 text-white text-xs h-8 px-3 rounded font-medium"
            >
              New Case
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCases.map((c) => (
            <Link
              href={`/dashboard/cases/${c.id}`}
              key={c.id}
              className="block bg-white border border-slate-200 hover:border-slate-400 rounded-lg p-5 transition-colors group shadow-2xs"
            >
              <div className="flex justify-between items-start gap-2 mb-2">
                <h2 className="text-sm font-bold text-slate-900 truncate group-hover:text-slate-700">
                  {c.title}
                </h2>
                <button
                  onClick={(e) => handleDeleteCase(c.id, e)}
                  className="text-xs text-slate-400 hover:text-red-600 px-1 py-0.5 rounded hover:bg-slate-100"
                  title="Delete case"
                >
                  Delete
                </button>
              </div>

              <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-4">
                {c.description || "No description."}
              </p>

              <div className="flex justify-between items-center text-[11px] text-slate-400 pt-3 border-t border-slate-100">
                <span>Created {c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}</span>
                <span className="font-medium text-slate-700 group-hover:underline">Open &rarr;</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
