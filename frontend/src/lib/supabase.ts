import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder'

// Initialize the Supabase client for the browser.
// This handles local storage and session management automatically.
export const supabase = createClient(supabaseUrl, supabaseAnonKey)
