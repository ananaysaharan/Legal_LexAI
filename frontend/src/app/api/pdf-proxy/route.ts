import { NextRequest, NextResponse } from "next/server"
import { createClient } from "@supabase/supabase-js"

// Server-side Supabase client using service role key for private bucket access
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const path = searchParams.get("path")
  const page = searchParams.get("page")

  if (!path) {
    return NextResponse.json({ error: "Missing path" }, { status: 400 })
  }

  try {
    // Get a signed URL from Supabase for the private bucket
    const { data, error } = await supabase.storage
      .from("documents")
      .createSignedUrl(path, 3600) // 1 hour expiry

    if (error || !data?.signedUrl) {
      console.error("Supabase signed URL error:", error)
      return NextResponse.json({ error: "Failed to generate signed URL" }, { status: 500 })
    }

    // Redirect to the signed URL so the browser can render the PDF
    const pageSuffix = page && /^\d+$/.test(page) ? `#page=${page}` : ""
    return NextResponse.redirect(`${data.signedUrl}${pageSuffix}`)
  } catch (err) {
    console.error("PDF proxy error:", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
