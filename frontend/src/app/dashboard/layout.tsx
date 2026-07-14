"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { supabase } from "@/lib/supabase"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        router.push("/login")
      } else {
        setLoading(false)
      }
    }

    checkAuth()

    // Listen for auth changes (e.g. logging out)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        router.push("/login")
      }
    })

    return () => subscription.unsubscribe()
  }, [router])

  if (loading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b py-4 px-8 flex justify-between items-center">
        <h1 className="text-xl font-bold">AI SaaS Platform</h1>
        <button 
          onClick={() => supabase.auth.signOut()}
          className="text-sm text-gray-500 hover:text-gray-900"
        >
          Sign Out
        </button>
      </header>
      <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {children}
      </main>
    </div>
  )
}
