import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'
import { Patient, PaginatedResponse, LabResult, ImagingStudy, ECGStudy, VitalSigns, ClinicalNote, Medication, Condition, AIInsight, RiskScore } from '../types'
import { MOCK_PATIENTS } from '../data/mockData'
import { supabase, fetchPatientData, fetchPatients as fetchPatientsSupabase } from '../services/supabase'
import type { PostgrestResponse } from '@supabase/supabase-js'

interface PatientContextType {
  patients: Patient[]
  currentPatient: Patient | null
  isLoading: boolean
  error: string | null
  pagination: { page: number; pageSize: number; total: number; totalPages: number }
  fetchPatients: (params?: PatientListParams) => Promise<void>
  fetchPatient: (id: string) => Promise<Patient | null>
  getPatient: (id: string) => Patient | undefined
  refreshPatient: (id: string) => Promise<Patient | null>
  createPatient: (patient: Omit<Patient, 'id' | 'createdAt' | 'updatedAt'>) => Promise<Patient>
  updatePatient: (id: string, data: Partial<Patient>) => Promise<Patient>
  deletePatient: (id: string) => Promise<void>
  searchPatients: (query: string) => Promise<Patient[]>
  fetchLabResults: (patientId: string, params?: LabQueryParams) => Promise<PaginatedResponse<LabResult>>
  fetchImagingStudies: (patientId: string) => Promise<ImagingStudy[]>
  fetchECGStudies: (patientId: string) => Promise<ECGStudy[]>
  fetchVitalSigns: (patientId: string, params?: VitalQueryParams) => Promise<VitalSigns[]>
  fetchClinicalNotes: (patientId: string) => Promise<ClinicalNote[]>
  fetchMedications: (patientId: string) => Promise<Medication[]>
  fetchConditions: (patientId: string) => Promise<Condition[]>
  fetchAIInsights: (patientId: string) => Promise<AIInsight[]>
  fetchRiskScores: (patientId: string) => Promise<RiskScore[]>
  addLabResult: (patientId: string, lab: Omit<LabResult, 'id'>) => Promise<LabResult>
  addImagingStudy: (patientId: string, study: Omit<ImagingStudy, 'id'>) => Promise<ImagingStudy>
  addClinicalNote: (patientId: string, note: Omit<ClinicalNote, 'id'>) => Promise<ClinicalNote>
  acknowledgeAIInsight: (patientId: string, insightId: string) => Promise<void>
  dismissAIInsight: (patientId: string, insightId: string) => Promise<void>
}

interface PatientListParams {
  page?: number
  pageSize?: number
  search?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: Record<string, unknown>
}

interface LabQueryParams {
  category?: string
  status?: string
  dateFrom?: string
  dateTo?: string
  abnormalOnly?: boolean
}

interface VitalQueryParams {
  type?: string[]
  dateFrom?: string
  dateTo?: string
  limit?: number
}

const PatientContext = createContext<PatientContextType | undefined>(undefined)

function mapSupabasePatient(sbPatient: any): Patient {
  return {
    id: sbPatient.id,
    mrn: sbPatient.mrn,
    firstName: sbPatient.first_name,
    lastName: sbPatient.last_name,
    dateOfBirth: sbPatient.date_of_birth,
    sex: sbPatient.sex,
    email: sbPatient.email,
    phone: sbPatient.phone,
    address: sbPatient.address,
    insurance: sbPatient.insurance,
    primaryCareProvider: sbPatient.primary_care_provider,
    allergies: sbPatient.allergies || [],
    medications: sbPatient.medications || [],
    conditions: sbPatient.conditions || [],
    encounters: sbPatient.encounters || [],
    vitals: sbPatient.vitals || [],
    labResults: sbPatient.lab_results || [],
    imagingStudies: sbPatient.imaging_studies || [],
    ecgStudies: sbPatient.ecg_studies || [],
    notes: sbPatient.notes || sbPatient.clinical_notes || [],
    riskScores: sbPatient.risk_scores || [],
    aiInsights: sbPatient.ai_insights || [],
    createdAt: sbPatient.created_at,
    updatedAt: sbPatient.updated_at,
  }
}

export function PatientProvider({ children }: { children: ReactNode }) {
  const [patients, setPatients] = useState<Patient[]>([])
  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0, totalPages: 0 })
  const [useSupabase, setUseSupabase] = useState(false)

  useEffect(() => {
    setUseSupabase(!!supabase)
  }, [])

  const fetchPatients = useCallback(async (params: PatientListParams = {}) => {
    setIsLoading(true)
    setError(null)
    try {
      if (useSupabase && supabase) {
        const { data, error: supabaseError, count } = await fetchPatientsSupabase(
          params.page,
          params.pageSize,
          params.search
        ) as PostgrestResponse<any> & { count: number | null }
        if (supabaseError) throw supabaseError
        const mappedPatients = (data || []).map(mapSupabasePatient)
        const total = count || 0
        const page = params.page || 1
        const pageSize = params.pageSize || 20
        setPatients(mappedPatients)
        setPagination({
          page,
          pageSize,
          total,
          totalPages: Math.ceil(total / pageSize),
        })
      } else {
        let rows = [...MOCK_PATIENTS]
        if (params.search) {
          const q = params.search.toLowerCase()
          rows = rows.filter(p =>
            p.lastName.toLowerCase().includes(q) ||
            p.firstName.toLowerCase().includes(q) ||
            p.mrn.toLowerCase().includes(q) ||
            p.id.includes(q) ||
            p.conditions.some(c => c.display.toLowerCase().includes(q))
          )
        }
        const total = rows.length
        const page = params.page || 1
        const pageSize = params.pageSize || 20
        rows = rows.slice((page - 1) * pageSize, page * pageSize)
        setPatients(rows)
        setPagination({ page, pageSize, total, totalPages: Math.ceil(total / pageSize) })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patients')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [useSupabase])

  const fetchPatient = useCallback(async (id: string) => {
    setIsLoading(true)
    setError(null)
    try {
      if (useSupabase && supabase) {
        const { data, error: supabaseError } = await fetchPatientData(id)
        if (supabaseError) throw supabaseError
        if (data) {
          const mapped = mapSupabasePatient(data)
          setCurrentPatient(mapped)
          return mapped
        }
      }
      const mockPatient = MOCK_PATIENTS.find(p => p.id === id)
      if (mockPatient) {
        setCurrentPatient(mockPatient)
        return mockPatient
      }
      throw new Error('Patient not found')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patient')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [useSupabase])

  const getPatient = useCallback((id: string): Patient | undefined => {
    return patients.find(p => p.id === id) || (currentPatient?.id === id ? currentPatient : undefined)
  }, [patients, currentPatient])

  const refreshPatient = useCallback(async (id: string): Promise<Patient | null> => {
    try {
      if (useSupabase && supabase) {
        const { data, error: supabaseError } = await fetchPatientData(id)
        if (supabaseError) throw supabaseError
        if (data) {
          const mapped = mapSupabasePatient(data)
          setCurrentPatient(mapped)
          setPatients(prev => prev.map(p => p.id === id ? mapped : p))
          return mapped
        }
      }
      const mockPatient = MOCK_PATIENTS.find(p => p.id === id)
      if (mockPatient) {
        setCurrentPatient(mockPatient)
        setPatients(prev => prev.map(p => p.id === id ? mockPatient : p))
        return mockPatient
      }
      return null
    } catch {
      return null
    }
  }, [useSupabase])

  const createPatient = useCallback(async (patientData: Omit<Patient, 'id' | 'createdAt' | 'updatedAt'>) => {
    setIsLoading(true)
    setError(null)
    try {
      if (useSupabase && supabase) {
        const { data, error: supabaseError } = await supabase
          .from('patients')
          .insert({
            mrn: patientData.mrn,
            first_name: patientData.firstName,
            last_name: patientData.lastName,
            date_of_birth: patientData.dateOfBirth,
            sex: patientData.sex,
            email: patientData.email,
            phone: patientData.phone,
            address: patientData.address as any,
            insurance: patientData.insurance as any,
            attending_physician: patientData.primaryCareProvider?.name || null,
          })
          .select()
          .single()
        if (supabaseError) throw supabaseError
        const mapped = mapSupabasePatient(data as any)
        setPatients(prev => [mapped, ...prev])
        return mapped
      }
      // Fallback - add to mock
      const newPatient: Patient = {
        ...patientData,
        id: `patient-${Date.now()}`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        labResults: [],
        imagingStudies: [],
        ecgStudies: [],
        notes: [],
        medications: [],
        conditions: [],
        aiInsights: [],
        riskScores: [],
        vitals: [],
      }
      setPatients(prev => [newPatient, ...prev])
      return newPatient
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create patient')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [useSupabase])

  const updatePatient = useCallback(async (id: string, data: Partial<Patient>) => {
    setIsLoading(true)
    setError(null)
    try {
      if (useSupabase && supabase) {
        const updateData: Record<string, any> = {}
        if (data.mrn) updateData.mrn = data.mrn
        if (data.firstName) updateData.first_name = data.firstName
        if (data.lastName) updateData.last_name = data.lastName
        if (data.dateOfBirth) updateData.date_of_birth = data.dateOfBirth
        if (data.sex) updateData.sex = data.sex
        if (data.email) updateData.email = data.email
        if (data.phone) updateData.phone = data.phone
        if (data.address) updateData.address = data.address
        if (data.insurance) updateData.insurance = data.insurance
        if (data.primaryCareProvider) updateData.attending_physician = data.primaryCareProvider?.name || null
        updateData.updated_at = new Date().toISOString()

        const { data: updatedData, error: supabaseError } = await supabase
          .from('patients')
          .update(updateData as any)
          .eq('id', id)
          .select()
          .single()
        if (supabaseError) throw supabaseError
        const mapped = mapSupabasePatient(updatedData)
        setPatients(prev => prev.map(p => p.id === id ? mapped : p))
        if (currentPatient?.id === id) {
          setCurrentPatient(mapped)
        }
        return mapped
      }
      // Fallback
      const updated: Patient = { ...currentPatient!, ...data, id, updatedAt: new Date().toISOString() } as Patient
      setPatients(prev => prev.map(p => p.id === id ? updated : p))
      if (currentPatient?.id === id) {
        setCurrentPatient(updated)
      }
      return updated
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update patient')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [useSupabase, currentPatient])

  const deletePatient = useCallback(async (id: string) => {
    setIsLoading(true)
    setError(null)
    try {
      if (useSupabase && supabase) {
        const { error: supabaseError } = await supabase
          .from('patients')
          .delete()
          .eq('id', id)
        if (supabaseError) throw supabaseError
      }
      setPatients(prev => prev.filter(p => p.id !== id))
      if (currentPatient?.id === id) {
        setCurrentPatient(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete patient')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [useSupabase, currentPatient])

  const searchPatients = useCallback(async (query: string) => {
    if (!query.trim()) return []
    try {
      if (useSupabase && supabase) {
        const { data, error } = await supabase
          .from('patients')
          .select('*')
          .or(`last_name.ilike.%${query}%,first_name.ilike.%${query}%,mrn.ilike.%${query}%`)
          .limit(20)
        if (error) throw error
        return (data || []).map(mapSupabasePatient)
      }
      return MOCK_PATIENTS.filter(p =>
        p.lastName.toLowerCase().includes(query.toLowerCase()) ||
        p.firstName.toLowerCase().includes(query.toLowerCase()) ||
        p.mrn.toLowerCase().includes(query.toLowerCase()) ||
        p.id.includes(query)
      )
    } catch {
      return []
    }
  }, [useSupabase])

  const fetchLabResults = useCallback(async (patientId: string, _params: LabQueryParams = {}): Promise<PaginatedResponse<LabResult>> => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('lab_results')
        .select('*')
        .eq('patient_id', patientId)
        .order('collected_at', { ascending: false })
      if (error) throw error
      const total = data?.length || 0
      return { data: data || [], page: 1, pageSize: 50, total, totalPages: 1, hasNext: false, hasPrevious: false }
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    const total = patient?.labResults.length || 0
    return { data: patient?.labResults || [], page: 1, pageSize: 50, total, totalPages: 1, hasNext: false, hasPrevious: false }
  }, [useSupabase])

  const fetchImagingStudies = useCallback(async (patientId: string) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('imaging_studies')
        .select('*, series(*, instances(*))')
        .eq('patient_id', patientId)
        .order('study_date', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.imagingStudies || []
  }, [useSupabase])

  const fetchECGStudies = useCallback(async (patientId: string) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('ecg_studies')
        .select('*')
        .eq('patient_id', patientId)
        .order('acquired_at', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.ecgStudies || []
  }, [useSupabase])

  const fetchVitalSigns = useCallback(async (patientId: string, _params: VitalQueryParams = {}) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('vitals')
        .select('*')
        .eq('patient_id', patientId)
        .order('recorded_at', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.vitals || []
  }, [useSupabase])

  const fetchClinicalNotes = useCallback(async (patientId: string) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('clinical_notes')
        .select('*')
        .eq('patient_id', patientId)
        .order('created_at', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.notes || []
  }, [useSupabase])

  const fetchMedications = useCallback(async (patientId: string) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('medications')
        .select('*')
        .eq('patient_id', patientId)
        .order('created_at', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.medications || []
  }, [useSupabase])

  const fetchConditions = useCallback(async (patientId: string) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('conditions')
        .select('*')
        .eq('patient_id', patientId)
        .order('onset_date', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.conditions || []
  }, [useSupabase])

  const fetchAIInsights = useCallback(async (patientId: string) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('ai_insights')
        .select('*')
        .eq('patient_id', patientId)
        .order('created_at', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.aiInsights || []
  }, [useSupabase])

  const fetchRiskScores = useCallback(async (patientId: string) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('risk_scores')
        .select('*')
        .eq('patient_id', patientId)
        .order('calculated_at', { ascending: false })
      if (error) throw error
      return data || []
    }
    const patient = MOCK_PATIENTS.find(p => p.id === patientId)
    return patient?.riskScores || []
  }, [useSupabase])

  const addLabResult = useCallback(async (patientId: string, lab: Omit<LabResult, 'id'>) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('lab_results')
        .insert({
          patient_id: patientId,
          test_name: lab.testName,
          value: typeof lab.value === 'number' ? lab.value : 0,
          unit: lab.unit,
          reference_range_low: lab.referenceRange.low || 0,
          reference_range_high: lab.referenceRange.high || 0,
          reference_range_unit: lab.referenceRange.unit,
          interpretation: lab.interpretation,
          collected_at: lab.collectedAt,
          resulted_at: lab.resultedAt,
          specimen_type: lab.specimenType || '',
          panel: lab.category,
          id: `lab-${Date.now()}`
        } as any)
        .select()
        .single()
      if (error) throw error
      return data
    }
    return { ...lab, id: `lab-${Date.now()}` } as LabResult
  }, [useSupabase])

  const addImagingStudy = useCallback(async (patientId: string, study: Omit<ImagingStudy, 'id'>) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('imaging_studies')
        .insert({
          patient_id: patientId,
          modality: study.modality,
          body_part: study.bodyPart,
          description: study.description,
          status: study.status,
          study_date: study.studyDate,
          accession_number: study.accessionNumber,
          referring_physician: study.referringPhysician,
          ai_findings: study.aiFindings || null,
          id: `img-${Date.now()}`
        } as any)
        .select()
        .single()
      if (error) throw error
      return data
    }
    return { ...study, id: `img-${Date.now()}` } as ImagingStudy
  }, [useSupabase])

  const addClinicalNote = useCallback(async (patientId: string, note: Omit<ClinicalNote, 'id'>) => {
    if (useSupabase && supabase) {
      const { data, error } = await supabase
        .from('clinical_notes')
        .insert({
          patient_id: patientId,
          type: note.type,
          title: note.title,
          content: note.content,
          author: note.author.name,
          author_role: note.author.specialty,
          tags: note.tags || [],
          id: `note-${Date.now()}`
        } as any)
        .select()
        .single()
      if (error) throw error
      return data
    }
    return { ...note, id: `note-${Date.now()}` } as ClinicalNote
  }, [useSupabase])

  const acknowledgeAIInsight = useCallback(async (patientId: string, insightId: string) => {
    if (useSupabase && supabase) {
      await supabase
        .from('ai_insights')
        .update({ status: 'reviewed', reviewed_at: new Date().toISOString() } as any)
        .eq('id', insightId)
    }
    if (currentPatient) {
      const insights = await fetchAIInsights(patientId)
      setCurrentPatient({ ...currentPatient, aiInsights: insights })
    }
  }, [currentPatient, fetchAIInsights, useSupabase])

  const dismissAIInsight = useCallback(async (patientId: string, insightId: string) => {
    if (useSupabase && supabase) {
      await supabase
        .from('ai_insights')
        .update({ status: 'dismissed', reviewed_at: new Date().toISOString() } as any)
        .eq('id', insightId)
    }
    if (currentPatient) {
      const insights = await fetchAIInsights(patientId)
      setCurrentPatient({ ...currentPatient, aiInsights: insights })
    }
  }, [currentPatient, fetchAIInsights, useSupabase])

  useEffect(() => {
    fetchPatients()
  }, [fetchPatients])

  return (
    <PatientContext.Provider
      value={{
        patients,
        currentPatient,
        isLoading,
        error,
        pagination,
        fetchPatients,
        fetchPatient,
        getPatient,
        refreshPatient,
        createPatient,
        updatePatient,
        deletePatient,
        searchPatients,
        fetchLabResults,
        fetchImagingStudies,
        fetchECGStudies,
        fetchVitalSigns,
        fetchClinicalNotes,
        fetchMedications,
        fetchConditions,
        fetchAIInsights,
        fetchRiskScores,
        addLabResult,
        addImagingStudy,
        addClinicalNote,
        acknowledgeAIInsight,
        dismissAIInsight,
      }}
    >
      {children}
    </PatientContext.Provider>
  )
}

export function usePatient() {
  const context = useContext(PatientContext)
  if (!context) {
    throw new Error('usePatient must be used within a PatientProvider')
  }
  return context
}