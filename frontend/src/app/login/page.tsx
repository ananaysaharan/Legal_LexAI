"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function LoginPage() {
  const router = useRouter()
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)

    if (isSignUp) {
      if (password !== confirmPassword) {
        setError("Passwords do not match.")
        setLoading(false)
        return
      }
      if (password.length < 6) {
        setError("Password must be at least 6 characters.")
        setLoading(false)
        return
      }

      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      })

      if (error) {
        setError(error.message)
        setLoading(false)
      } else {
        if (data.session) {
          router.push("/dashboard")
        } else {
          setMessage("Account created successfully. You may now sign in.")
          setIsSignUp(false)
          setLoading(false)
        }
      }
    } else {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        setError(error.message)
        setLoading(false)
      } else {
        router.push("/dashboard")
      }
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Simple Brand Header */}
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Legal LexAI</h1>
          <p className="text-xs text-slate-500 font-normal">Case-Scoped Legal Management Platform</p>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-300">
          <button
            type="button"
            onClick={() => { setIsSignUp(false); setError(null); setMessage(null); }}
            className={`flex-1 pb-2 text-xs font-semibold border-b-2 transition-colors ${
              !isSignUp ? "border-slate-900 text-slate-900" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsSignUp(true); setError(null); setMessage(null); }}
            className={`flex-1 pb-2 text-xs font-semibold border-b-2 transition-colors ${
              isSignUp ? "border-slate-900 text-slate-900" : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Sign Up
          </button>
        </div>

        <Card className="bg-white border-slate-200 shadow-sm rounded-lg">
          <CardHeader className="space-y-1 pb-3">
            <CardTitle className="text-lg font-semibold text-slate-900">
              {isSignUp ? "Create an account" : "Sign in to your account"}
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              {isSignUp ? "Enter your details to create a new workspace." : "Enter your email and password to continue."}
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <div className="p-2.5 rounded bg-red-50 border border-red-200 text-red-700 text-xs font-medium">
                  {error}
                </div>
              )}

              {message && (
                <div className="p-2.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium">
                  {message}
                </div>
              )}

              <div className="space-y-1">
                <Label htmlFor="email" className="text-xs font-medium text-slate-700">
                  Email address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@firm.com"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-white border-slate-300 text-slate-900 text-xs h-9 focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="password" className="text-xs font-medium text-slate-700">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-white border-slate-300 text-slate-900 text-xs h-9 focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
                />
              </div>

              {isSignUp && (
                <div className="space-y-1">
                  <Label htmlFor="confirmPassword" className="text-xs font-medium text-slate-700">
                    Confirm Password
                  </Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="bg-white border-slate-300 text-slate-900 text-xs h-9 focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
                  />
                </div>
              )}
            </CardContent>

            <div className="p-6 pt-2">
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs h-9 rounded"
              >
                {loading ? "Please wait..." : isSignUp ? "Create Account" : "Sign In"}
              </Button>
            </div>
          </form>
        </Card>

        <p className="text-center text-xs text-slate-400">
          Legal LexAI Platform
        </p>
      </div>
    </div>
  )
}
