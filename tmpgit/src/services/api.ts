import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
import { ApiResponse, ApiError } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

class ApiClient {
  private client: AxiosInstance
  private refreshTokenPromise: Promise<string> | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    })

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('auth_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const newToken = await this.refreshAccessToken()
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
            }
            return this.client.request(originalRequest)
          } catch {
            localStorage.removeItem('auth_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user')
            window.location.href = '/login'
            return Promise.reject(error)
          }
        }

        return Promise.reject(this.normalizeError(error))
      }
    )
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise
    }

    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    this.refreshTokenPromise = (async () => {
      try {
        const response = await axios.post<{ access_token: string }>(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        )
        const newToken = response.data.access_token
        localStorage.setItem('auth_token', newToken)
        return newToken
      } finally {
        this.refreshTokenPromise = null
      }
    })()

    return this.refreshTokenPromise
  }

  private normalizeError(error: AxiosError<ApiError>): Error {
    if (error.response?.data) {
      const apiError = error.response.data
      const err = new Error(apiError.message || 'An error occurred') as Error & { code?: string; details?: Record<string, unknown>; status?: number }
      err.code = apiError.code
      err.details = apiError.details
      err.status = error.response.status
      return err
    }

    if (error.code === 'ECONNABORTED') {
      const err = new Error('Request timeout') as Error & { code: string }
      err.code = 'TIMEOUT'
      return err
    }

    if (!error.response) {
      const err = new Error('Network error. Please check your connection.') as Error & { code: string }
      err.code = 'NETWORK_ERROR'
      return err
    }

    const err = new Error(`HTTP ${error.response.status}: ${error.response.statusText}`) as Error & { status: number }
    err.status = error.response.status
    return err
  }

  async get<T>(url: string, config?: AxiosRequestConfig) {
    const response = await this.client.get<ApiResponse<T>>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    const response = await this.client.post<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    const response = await this.client.put<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig) {
    const response = await this.client.delete<ApiResponse<T>>(url, config)
    return response.data
  }

  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post<ApiResponse<T>>(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          onProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total))
        }
      },
    })
    return response.data
  }

  async download(url: string, filename?: string) {
    const response = await this.client.get(url, { responseType: 'blob' })
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || url.split('/').pop() || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  setAuthToken(token: string | null) {
    if (token) {
      localStorage.setItem('auth_token', token)
    } else {
      localStorage.removeItem('auth_token')
    }
  }

  getAuthToken(): string | null {
    return localStorage.getItem('auth_token')
  }
}

export const api = new ApiClient()

export const authApi = {
  login: (email: string, password: string, rememberMe?: boolean) =>
    api.post<{ user: User; access_token: string; refresh_token: string }>('/auth/login', { email, password, remember_me: rememberMe }),

  logout: () => api.post('/auth/logout'),

  refresh: () => api.post<{ access_token: string }>('/auth/refresh'),

  me: () => api.get<User>('/auth/me'),

  updateProfile: (data: Partial<User>) => api.patch<User>('/auth/me', data),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),

  requestPasswordReset: (email: string) => api.post('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    api.post('/auth/reset-password', { token, new_password: newPassword }),
}

export const patientsApi = {
  list: (params?: Record<string, unknown>) => api.get<PaginatedResponse<Patient>>('/patients', { params }),

  get: (id: string) => api.get<Patient>(`/patients/${id}`),

  create: (data: Omit<Patient, 'id' | 'createdAt' | 'updatedAt'>) => api.post<Patient>('/patients', data),

  update: (id: string, data: Partial<Patient>) => api.patch<Patient>(`/patients/${id}`, data),

  delete: (id: string) => api.delete(`/patients/${id}`),

  search: (query: string) => api.get<Patient[]>('/patients/search', { params: { q: query } }),

  getLabs: (patientId: string, params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<LabResult>>(`/patients/${patientId}/labs`, { params }),

  getImaging: (patientId: string) => api.get<ImagingStudy[]>(`/patients/${patientId}/imaging`),

  getECG: (patientId: string) => api.get<ECGStudy[]>(`/patients/${patientId}/ecg`),

  getVitals: (patientId: string, params?: Record<string, unknown>) =>
    api.get<VitalSigns[]>(`/patients/${patientId}/vitals`, { params }),

  getNotes: (patientId: string) => api.get<ClinicalNote[]>(`/patients/${patientId}/notes`),

  getMedications: (patientId: string) => api.get<Medication[]>(`/patients/${patientId}/medications`),

  getConditions: (patientId: string) => api.get<Condition[]>(`/patients/${patientId}/conditions`),

  getAIInsights: (patientId: string) => api.get<AIInsight[]>(`/patients/${patientId}/ai-insights`),

  getRiskScores: (patientId: string) => api.get<RiskScore[]>(`/patients/${patientId}/risk-scores`),

  addLab: (patientId: string, data: Omit<LabResult, 'id'>) => api.post<LabResult>(`/patients/${patientId}/labs`, data),

  addImaging: (patientId: string, data: Omit<ImagingStudy, 'id'>) => api.post<ImagingStudy>(`/patients/${patientId}/imaging`, data),

  addNote: (patientId: string, data: Omit<ClinicalNote, 'id'>) => api.post<ClinicalNote>(`/patients/${patientId}/notes`, data),

  acknowledgeInsight: (patientId: string, insightId: string) =>
    api.post(`/patients/${patientId}/ai-insights/${insightId}/acknowledge`),

  dismissInsight: (patientId: string, insightId: string) =>
    api.post(`/patients/${patientId}/ai-insights/${insightId}/dismiss`),
}

export const imagingApi = {
  getStudy: (studyId: string) => api.get<ImagingStudy>(`/imaging/studies/${studyId}`),

  getSeries: (seriesId: string) => api.get<ImagingSeries>(`/imaging/series/${seriesId}`),

  getInstances: (seriesId: string) => api.get<ImagingInstance[]>(`/imaging/series/${seriesId}/instances`),

  getInstance: (instanceId: string) => api.get<ImagingInstance>(`/imaging/instances/${instanceId}`),

  getDICOM: (instanceId: string) => api.get<ArrayBuffer>(`/imaging/instances/${instanceId}/dicom`, { responseType: 'arraybuffer' }),

  getFrame: (instanceId: string, frame: number) => api.get<ArrayBuffer>(`/imaging/instances/${instanceId}/frames/${frame}`, { responseType: 'arraybuffer' }),

  getThumbnail: (instanceId: string, size = 256) => api.get<Blob>(`/imaging/instances/${instanceId}/thumbnail?size=${size}`, { responseType: 'blob' }),

  runAIAnalysis: (studyId: string, modelId: string) => api.post<AIAnalysisJob>(`/imaging/studies/${studyId}/analyze`, { model_id: modelId }),

  getAIAnalysis: (jobId: string) => api.get<AIAnalysisResult>(`/imaging/ai-jobs/${jobId}`),

  getModels: () => api.get<Model[]>(`/imaging/models`),

  uploadDICOM: (file: File, onProgress?: (progress: number) => void) => api.upload<ImagingStudy>('/imaging/upload', file, onProgress),
}

export const labApi = {
  getReferenceRanges: (testId: string) => api.get<ReferenceRange>(`/labs/reference-ranges/${testId}`),

  getTrends: (patientId: string, testIds: string[], days = 90) =>
    api.get<LabTrend[]>(`/patients/${patientId}/labs/trends`, { params: { test_ids: testIds.join(','), days } }),

  getPanels: () => api.get<LabPanel[]>('/labs/panels'),

  getCategories: () => api.get<LabCategory[]>('/labs/categories'),

  flagAbnormal: (patientId: string, labId: string) => api.post(`/patients/${patientId}/labs/${labId}/flag`),

  addComment: (patientId: string, labId: string, comment: string) =>
    api.post(`/patients/${patientId}/labs/${labId}/comments`, { comment }),
}

export const ecgApi = {
  getStudy: (studyId: string) => api.get<ECGStudy>(`/ecg/studies/${studyId}`),

  getWaveform: (studyId: string, lead: string) => api.get<number[]>(`/ecg/studies/${studyId}/waveform/${lead}`),

  getMeasurements: (studyId: string) => api.get<ECGMeasurements>(`/ecg/studies/${studyId}/measurements`),

  runAIAnalysis: (studyId: string) => api.post<ECGAIAnalysisJob>(`/ecg/studies/${studyId}/analyze`),

  getAIAnalysis: (jobId: string) => api.get<ECGAIAnalysisResult>(`/ecg/ai-jobs/${jobId}`),

  compareStudies: (studyIds: string[]) => api.post<ECGComparison>(`/ecg/compare`, { study_ids: studyIds }),

  uploadECG: (file: File, onProgress?: (progress: number) => void) => api.upload<ECGStudy>('/ecg/upload', file, onProgress),
}

export const aiApi = {
  generateInsights: (patientId: string, context?: Record<string, unknown>) =>
    api.post<AIInsight[]>(`/ai/insights/${patientId}`, { context }),

  getModels: () => api.get<Model[]>(`/ai/models`),

  getModel: (modelId: string) => api.get<Model>(`/ai/models/${modelId}`),

  runInference: (modelId: string, input: Record<string, unknown>) =>
    api.post<AIInferenceResult>(`/ai/models/${modelId}/infer`, { input }),

  submitFeedback: (insightId: string, feedback: AIInsightFeedback) =>
    api.post(`/ai/insights/${insightId}/feedback`, feedback),

  getExplanations: (insightId: string) => api.get<AIExplanation>(`/ai/insights/${insightId}/explain`),
}

export const clinicalApi = {
  getGuidelines: (conditionCode: string) => api.get<ClinicalGuideline[]>(`/clinical/guidelines/${conditionCode}`),

  getDrugInteractions: (medications: string[]) => api.post<DrugInteraction[]>(`/clinical/drug-interactions`, { medications }),

  calculateRiskScore: (scoreId: string, patientData: Record<string, unknown>) =>
    api.post<RiskScore>(`/clinical/risk-scores/${scoreId}/calculate`, { patient_data: patientData }),

  getRiskScores: () => api.get<RiskScoreDefinition[]>(`/clinical/risk-scores`),

  checkAllergies: (patientId: string, substance: string) =>
    api.get<AllergyCheckResult>(`/patients/${patientId}/allergies/check`, { params: { substance } }),

  getOrderSets: (conditionCode?: string) => api.get<OrderSet[]>(`/clinical/order-sets`, { params: { condition: conditionCode } }),
}

export const systemApi = {
  getMetrics: () => api.get<SystemMetrics>('/system/metrics'),

  getHealth: () => api.get<SystemHealth>('/system/health'),

  getAuditLogs: (params?: Record<string, unknown>) => api.get<PaginatedResponse<AuditLog>>('/system/audit-logs', { params }),

  getNotifications: (unreadOnly = false) => api.get<Notification[]>('/system/notifications', { params: { unread_only: unreadOnly } }),

  markNotificationRead: (id: string) => api.post(`/system/notifications/${id}/read`),

  markAllNotificationsRead: () => api.post('/system/notifications/read-all'),
}

import { User, Patient, PaginatedResponse, LabResult, ImagingStudy, ImagingSeries, ImagingInstance, ECGStudy, VitalSigns, ClinicalNote, Medication, Condition, AIInsight, RiskScore, ReferenceRange, LabTrend, LabPanel, LabCategory, AIAnalysisJob, AIAnalysisResult, Model, ECGMeasurements, ECGAIAnalysisJob, ECGAIAnalysisResult, ECGComparison, AIInferenceResult, AIInsightFeedback, AIExplanation, ClinicalGuideline, DrugInteraction, RiskScoreDefinition, AllergyCheckResult, OrderSet, SystemMetrics, SystemHealth, AuditLog, Notification } from '../types'