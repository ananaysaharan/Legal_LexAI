import axios from 'axios'
import { supabase } from './supabase'

// Create a central Axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
})

// Request Interceptor: Runs before EVERY request sent by this client
api.interceptors.request.use(async (config) => {
  // Grab the current session from Supabase
  const { data: { session } } = await supabase.auth.getSession()
  
  // If we are logged in, inject the JWT into the Authorization header
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  
  return config
})

export default api
