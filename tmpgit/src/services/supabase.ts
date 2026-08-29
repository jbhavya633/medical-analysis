import { createBrowserClient } from '@supabase/ssr'
import type { Database } from './database.types'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('[Supabase] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set. Supabase features disabled.')
}

export const supabase = supabaseUrl && supabaseAnonKey
  ? createBrowserClient<Database>(supabaseUrl, supabaseAnonKey)
  : null

export function getSupabase() {
  return supabase
}

export async function getSession() {
  if (!supabase) return { data: { session: null }, error: new Error('Supabase not configured') }
  return supabase.auth.getSession()
}

export async function getUser() {
  if (!supabase) return { data: { user: null }, error: new Error('Supabase not configured') }
  return supabase.auth.getUser()
}

export async function signIn(email: string, password: string) {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  return supabase.auth.signInWithPassword({ email, password })
}

export async function signUp(email: string, password: string, metadata?: Record<string, any>) {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  return supabase.auth.signUp({ email, password, options: { data: metadata } })
}

export async function signOut() {
  if (!supabase) return { error: new Error('Supabase not configured') }
  return supabase.auth.signOut()
}

export async function resetPassword(email: string) {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  return supabase.auth.resetPasswordForEmail(email)
}

export function onAuthStateChange(callback: (event: string, session: any) => void) {
  if (!supabase) return { data: { subscription: { unsubscribe: () => {} } } }
  return supabase.auth.onAuthStateChange(callback)
}

export async function fetchPatientData(patientId: string) {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  return supabase
    .from('patients')
    .select(`
      *,
      lab_results(*),
      imaging_studies(*, series(*, instances(*))),
      ecg_studies(*),
      clinical_notes(*),
      medications(*),
      conditions(*),
      ai_insights(*),
      risk_scores(*),
      vitals(*)
    `)
    .eq('id', patientId)
    .single()
}

export async function fetchPatients(page = 1, pageSize = 20, search = '') {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  let query = supabase
    .from('patients')
    .select('*', { count: 'exact' })
    .range((page - 1) * pageSize, page * pageSize - 1)
    .order('updated_at', { ascending: false })

  if (search) {
    query = query.or(`last_name.ilike.%${search}%,first_name.ilike.%${search}%,mrn.ilike.%${search}%`)
  }

  return query
}

export function subscribeToPatientUpdates(patientId: string, callback: (payload: any) => void) {
  if (!supabase) return { unsubscribe: () => {} }
  return supabase
    .channel(`patient-${patientId}`)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'patients', filter: `id=eq.${patientId}` }, callback)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'lab_results', filter: `patient_id=eq.${patientId}` }, callback)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'imaging_studies', filter: `patient_id=eq.${patientId}` }, callback)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'ecg_studies', filter: `patient_id=eq.${patientId}` }, callback)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'ai_insights', filter: `patient_id=eq.${patientId}` }, callback)
    .subscribe()
}

export async function uploadDICOM(file: File, patientId: string, studyId: string) {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  const fileName = `${patientId}/${studyId}/${Date.now()}-${file.name}`
  return supabase.storage.from('dicom').upload(fileName, file)
}

export async function uploadECG(file: File, patientId: string) {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  const fileName = `${patientId}/ecg/${Date.now()}-${file.name}`
  return supabase.storage.from('ecg').upload(fileName, file)
}

export async function fetchModels() {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  return supabase.from('models').select('*').order('created_at', { ascending: false })
}

export async function fetchDatasets() {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  return supabase.from('datasets').select('*').order('created_at', { ascending: false })
}

export async function createAIJob(input: { patientId: string; modalities: string[]; task: string }) {
  if (!supabase) return { data: null, error: new Error('Supabase not configured') }
  return supabase.from('ai_jobs').insert({
    patient_id: input.patientId,
    modalities: input.modalities,
    task: input.task
  }).select().single()
}

export function subscribeToAIJobs(callback: (payload: any) => void) {
  if (!supabase) return { unsubscribe: () => {} }
  return supabase
    .channel('ai-jobs')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'ai_jobs' }, callback)
    .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'ai_jobs' }, callback)
    .subscribe()
}