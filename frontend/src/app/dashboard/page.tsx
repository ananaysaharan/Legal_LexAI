"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import api from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Plus, Search, FolderKanban, Trash2, Calendar, FileText, ArrowUpRight, Scale, Sparkles } from "lucide-react"

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
    if (!confirm("Are you sure you want to delete this case? All uploaded documents and conversations will be removed.")) return
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
    <div className="space-y-8">
      {/* Header Banner & Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" /> Case-Scoped AI Intelligence
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Your Cases</h1>
          <p className="text-slate-400 text-xs mt-1">
            Manage your legal cases, upload discovery PDFs, and execute grounded RAG research.
          </p>
        </div>

        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white font-semibold shadow-lg shadow-indigo-500/20 text-xs h-10 px-4 gap-2 self-start md:self-auto">
              <Plus className="w-4 h-4" /> Create New Case
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-slate-900 border-slate-800 text-slate-100 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
                <FolderKanban className="w-5 h-5 text-indigo-400" /> Create New Legal Case
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateCase} className="space-y-4 mt-2">
              <div className="space-y-1.5">
                <Label htmlFor="title" className="text-xs font-medium text-slate-300">
                  Case Title <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="title"
                  placeholder="e.g. Acme Corp v. Smith Breach of Contract"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="bg-slate-950 border-slate-800 focus:border-indigo-500 text-white text-xs h-10 placeholder:text-slate-600"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="desc" className="text-xs font-medium text-slate-300">
                  Description / Notes (Optional)
                </Label>
                <Input
                  id="desc"
                  placeholder="Key litigation details or summary notes..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="bg-slate-950 border-slate-800 focus:border-indigo-500 text-white text-xs h-10 placeholder:text-slate-600"
                />
              </div>
              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={creating}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs h-10 shadow-md"
                >
                  {creating ? "Creating Case..." : "Create Case"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filter and Search Bar */}
      {cases.length > 0 && (
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <Input
              type="text"
              placeholder="Search cases by title or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border-slate-800 focus:border-indigo-500 text-white text-xs h-10 pl-9 placeholder:text-slate-500"
            />
          </div>
          <span className="text-xs text-slate-500 font-medium">
            Showing {filteredCases.length} of {cases.length} cases
          </span>
        </div>
      )}

      {/* Grid of Cases */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 rounded-xl bg-slate-900/50 border border-slate-800/60 animate-pulse p-6 space-y-4">
              <div className="h-5 bg-slate-800 rounded w-2/3" />
              <div className="h-3 bg-slate-800/60 rounded w-full" />
              <div className="h-3 bg-slate-800/60 rounded w-4/5" />
            </div>
          ))}
        </div>
      ) : cases.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 px-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 text-center space-y-4">
          <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <FolderKanban className="w-10 h-10" />
          </div>
          <div className="space-y-1 max-w-md">
            <h3 className="text-lg font-bold text-white">No Legal Cases Created</h3>
            <p className="text-slate-400 text-xs">
              Get started by creating your first case workspace to upload document discovery and ask grounded legal questions.
            </p>
          </div>
          <Button
            onClick={() => setIsOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs h-9 px-4 gap-2"
          >
            <Plus className="w-4 h-4" /> Create First Case
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCases.map((c) => (
            <Link href={`/dashboard/cases/${c.id}`} key={c.id} className="group">
              <Card className="bg-slate-900/80 border-slate-800/80 hover:border-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/5 transition-all duration-200 cursor-pointer h-full flex flex-col justify-between overflow-hidden relative">
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                <CardHeader className="p-6 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0">
                        <Scale className="w-4 h-4" />
                      </div>
                      <CardTitle className="text-base font-bold text-white truncate group-hover:text-indigo-300 transition-colors">
                        {c.title}
                      </CardTitle>
                    </div>

                    <button
                      onClick={(e) => handleDeleteCase(c.id, e)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors shrink-0"
                      title="Delete case"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <CardDescription className="text-slate-400 text-xs line-clamp-3 leading-relaxed">
                    {c.description || "No case summary or description provided."}
                  </CardDescription>
                </CardHeader>

                <CardContent className="px-6 pb-6 pt-0 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/50 mt-2">
                  <div className="flex items-center gap-1.5 pt-3">
                    <Calendar className="w-3.5 h-3.5 text-slate-600" />
                    <span>{c.created_at ? new Date(c.created_at).toLocaleDateString() : "Recent"}</span>
                  </div>
                  <div className="flex items-center gap-1 text-indigo-400 font-medium group-hover:translate-x-0.5 transition-transform pt-3">
                    <span>Open Case</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
