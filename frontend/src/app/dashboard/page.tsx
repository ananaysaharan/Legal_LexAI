"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import api from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function DashboardPage() {
  const [cases, setCases] = useState<any[]>([])
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [loading, setLoading] = useState(true)
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
    try {
      await api.post("/cases/", { title, description })
      setIsOpen(false)
      setTitle("")
      setDescription("")
      fetchCases() // Refresh list
    } catch (error) {
      console.error("Failed to create case:", error)
    }
  }

  const handleDeleteCase = async (id: string, e: React.MouseEvent) => {
    e.preventDefault() // prevent navigation if wrapped in link
    if (!confirm("Are you sure?")) return
    try {
      await api.delete(`/cases/${id}`)
      fetchCases()
    } catch (error) {
      console.error("Failed to delete case:", error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Your Cases</h2>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger render={<Button />}>
            Create Case
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create a new Case</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateCase} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input id="title" required value={title} onChange={e => setTitle(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="desc">Description</Label>
                <Input id="desc" value={description} onChange={e => setDescription(e.target.value)} />
              </div>
              <Button type="submit" className="w-full">Create</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div>Loading cases...</div>
      ) : cases.length === 0 ? (
        <div className="text-gray-500 text-center py-12">No cases found. Create one to get started!</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cases.map((c) => (
            <Link href={`/dashboard/cases/${c.id}`} key={c.id}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer h-full flex flex-col">
                <CardHeader className="flex-1">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-xl">{c.title}</CardTitle>
                    <Button 
                      variant="destructive" 
                      size="sm" 
                      onClick={(e) => handleDeleteCase(c.id, e)}
                    >
                      Delete
                    </Button>
                  </div>
                  <CardDescription className="line-clamp-2 mt-2">{c.description || "No description provided."}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
