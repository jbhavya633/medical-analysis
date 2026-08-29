export interface User {
  id: string
  email: string
  name: string
  role: 'physician' | 'radiologist' | 'nurse' | 'admin' | 'researcher'
  avatar?: string
  preferences: UserPreferences
  createdAt: string
  lastLoginAt: string
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  timezone: string
  notifications: {
    email: boolean
    push: boolean
    criticalAlerts: boolean
  }
  dashboard: {
    defaultView: string
    widgets: string[]
  }
  imaging: {
    defaultWindowLevel: { width: number; center: number }
    cineSpeed: number
    showAnnotations: boolean
  }
}

export interface Patient {
  id: string
  mrn: string
  firstName: string
  lastName: string
  dateOfBirth: string
  sex: 'M' | 'F' | 'O'
  phone?: string
  email?: string
  address?: Address
  insurance?: Insurance
  emergencyContact?: EmergencyContact
  primaryCareProvider?: Provider
  allergies: Allergy[]
  medications: Medication[]
  conditions: Condition[]
  encounters: Encounter[]
  vitals: VitalSigns[]
  labResults: LabResult[]
  imagingStudies: ImagingStudy[]
  ecgStudies: ECGStudy[]
  clinicalNotes: ClinicalNote[]
  admission?: { admissionDate: string }
  riskScores: RiskScore[]
  aiInsights: AIInsight[]
  createdAt: string
  updatedAt: string
}

export interface Address {
  street: string
  city: string
  state: string
  zipCode: string
  country: string
}

export interface Insurance {
  provider: string
  policyNumber: string
  groupNumber?: string
  subscriberId: string
  relationship: 'self' | 'spouse' | 'child' | 'other'
  effectiveDate: string
  expirationDate?: string
}

export interface EmergencyContact {
  name: string
  relationship: string
  phone: string
  email?: string
}

export interface Provider {
  id: string
  name: string
  npi: string
  specialty: string
  organization: string
  phone: string
  email: string
}

export interface Allergy {
  id: string
  substance: string
  reaction: string[]
  severity: 'mild' | 'moderate' | 'severe' | 'life-threatening'
  status: 'active' | 'inactive' | 'resolved'
  onsetDate?: string
  notedDate: string
}

export interface Medication {
  id: string
  name: string
  genericName?: string
  dosage: string
  dose?: string
  route: string
  frequency: string
  startDate: string
  endDate?: string
  status: 'active' | 'discontinued' | 'completed' | 'held'
  prescribingProvider: string
  indication?: string
  ndc?: string
}

export interface Condition {
  id: string
  code: string
  display: string
  category: 'problem' | 'diagnosis' | 'history'
  severity?: 'mild' | 'moderate' | 'severe'
  status: 'active' | 'inactive' | 'resolved'
  onsetDate?: string
  resolvedDate?: string
  clinicalStatus: 'active' | 'recurrence' | 'relapse' | 'inactive' | 'remission' | 'resolved'
  verificationStatus: 'unconfirmed' | 'provisional' | 'differential' | 'confirmed' | 'refuted' | 'entered-in-error'
  system?: string
}

export interface Encounter {
  id: string
  type: 'inpatient' | 'outpatient' | 'emergency' | 'urgent' | 'virtual'
  status: 'planned' | 'arrived' | 'in-progress' | 'onleave' | 'finished' | 'cancelled'
  class: string
  priority?: string
  subject: string
  participant: EncounterParticipant[]
  period: { start: string; end?: string }
  location: EncounterLocation[]
  serviceProvider: string
  diagnosis: EncounterDiagnosis[]
  reasonCode: CodeableConcept[]
}

export interface EncounterParticipant {
  individual: Provider
  type: string[]
  period: { start: string; end?: string }
}

export interface EncounterLocation {
  location: { id: string; name: string; type: string }
  status: 'planned' | 'active' | 'reserved' | 'completed'
  period: { start: string; end?: string }
}

export interface EncounterDiagnosis {
  condition: Condition
  use: string
  rank: number
}

export interface CodeableConcept {
  coding: Coding[]
  text?: string
}

export interface Coding {
  system: string
  code: string
  display: string
  version?: string
  userSelected?: boolean
}

export interface VitalSigns {
  id: string
  timestamp: string
  temperature?: number
  heartRate?: number
  respiratoryRate?: number
  bloodPressureSystolic?: number
  systolicBP?: number
  bloodPressureDiastolic?: number
  oxygenSaturation?: number
  spo2?: number
  weight?: number
  height?: number
  bmi?: number
  painScore?: number
  glasgowComaScale?: number
  source: 'manual' | 'device' | 'imported'
  deviceId?: string
}

export interface LabResult {
  id: string
  testId: string
  testName: string
  category: string
  subcategory?: string
  value: number | string
  unit: string
  referenceRange: ReferenceRange
  interpretation: 'normal' | 'abnormal' | 'critical' | 'low' | 'high'
  status: 'preliminary' | 'final' | 'amended' | 'corrected' | 'cancelled'
  specimenType?: string
  specimenId?: string
  orderedBy: string
  performedBy: string
  orderedAt: string
  collectedAt?: string
  resultedAt: string
  verifiedAt?: string
  verifiedBy?: string
  notes?: string
  components?: LabComponent[]
  loincCode?: string
  snomedCode?: string
  delta?: number
}

export interface ReferenceRange {
  low?: number
  high?: number
  lowInclusive?: boolean
  highInclusive?: boolean
  text?: string
  ageLow?: number
  ageHigh?: number
  gender?: 'M' | 'F' | 'O'
  unit: string
}

export interface LabComponent {
  id: string
  name: string
  value: number | string
  unit: string
  referenceRange: ReferenceRange
  interpretation: 'normal' | 'abnormal' | 'critical' | 'low' | 'high'
}

export interface ImagingStudy {
  id: string
  accessionNumber: string
  studyInstanceUID: string
  studyDate: string
  studyTime: string
  modality: Modality
  bodyPart: string
  description: string
  status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled' | 'archived'
  referringPhysician: string
  performingPhysician: string
  institution: string
  stationName: string
  series: ImagingSeries[]
  dicomTags?: Record<string, string>
  aiFindings?: AIFinding[]
  report?: ImagingReport
}

export type Modality =
  | 'CT' | 'MR' | 'XRAY' | 'US' | 'PET' | 'PT' | 'NM' | 'MG' | 'DX' | 'CR' | 'RF' | 'ES' | 'LS' | 'HC' | 'IO' | 'OCT' | 'OP' | 'OPM' | 'OPT' | 'OPTBSV' | 'OPTENF' | 'OPTFFA' | 'OPTICP' | 'OPTONH' | 'OPTOPT' | 'OPV' | 'PX' | 'RG' | 'SM' | 'TG' | 'XA' | 'XC' | 'BDUS' | 'EPS' | 'ECG' | 'STAIN' | 'RTDOSE' | 'RTIMAGE' | 'RTPLAN' | 'RTRECORD' | 'RTSTRUCT' | 'SEG' | 'KO' | 'KOLO' | 'KOREF' | 'KOXREF' | 'RAW' | 'VL' | 'SR' | 'SRF' | 'SRT' | 'ENCAP'

export interface ImagingSeries {
  id: string
  seriesInstanceUID: string
  seriesNumber: number
  seriesDate: string
  seriesTime: string
  modality: Modality
  description: string
  bodyPart: string
  protocolName?: string
  instanceCount: number
  instances: ImagingInstance[]
  dicomTags?: Record<string, string>
}

export interface ImagingInstance {
  id: string
  sopInstanceUID: string
  instanceNumber: number
  url: string
  thumbnailUrl?: string
  rows: number
  columns: number
  bitsAllocated: number
  bitsStored: number
  highBit: number
  pixelRepresentation: number
  samplesPerPixel: number
  photometricInterpretation: string
  windowCenter?: number | number[]
  windowWidth?: number | number[]
  rescaleIntercept?: number
  rescaleSlope?: number
  pixelSpacing?: number[]
  sliceThickness?: number
  imagePositionPatient?: number[]
  imageOrientationPatient?: number[]
  frameOfReferenceUID?: string
  positionReferenceIndicator?: string
  sliceLocation?: number
  acquisitionDateTime?: string
  contentDateTime?: string
  aiAnnotations?: any[]
  metadata?: Record<string, unknown>
}

export interface ImagingReport {
  id: string
  reportStatus: 'preliminary' | 'final' | 'amended' | 'corrected'
  reportText: string
  codedDiagnosis: CodeableConcept[]
  conclusion?: string
  recommendations?: string[]
  signedBy: string
  signedAt: string
  verifiedBy?: string
  verifiedAt?: string
}

export interface AIFinding {
  id: string
  modelId: string
  modelVersion: string
  finding: string
  confidence: number
  boundingBox?: BoundingBox
  segmentationMask?: string
  category: 'lesion' | 'nodule' | 'mass' | 'fracture' | 'hemorrhage' | 'edema' | 'consolidation' | 'atelectasis' | 'effusion' | 'pneumothorax' | 'cardiomegaly' | 'other'
  severity: 'low' | 'moderate' | 'high' | 'critical'
  status: 'pending' | 'confirmed' | 'rejected' | 'modified'
  reviewedBy?: string
  reviewedAt?: string
  createdAt: string
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
  sliceIndex?: number
}

export interface ECGStudy {
  id: string
  accessionNumber: string
  studyDate: string
  studyTime: string
  deviceId: string
  deviceModel: string
  leads: ECGLead[]
  interpretation: ECGInterpretation
  aiAnalysis?: ECGAIAnalysis
  report?: string
  sampledAt: string
  duration: number
  samplingRate: number
  filterSettings: ECGFilterSettings
  // Additional fields from Supabase database schema
  rhythm: string
  heartRate: number
  prInterval: number
  qrsDuration: number
  qtInterval: number
  qtcInterval: number
  pAxis: number
  qrsAxis: number
  tAxis: number
  acquiredAt: string
}

export interface ECGLead {
  name: string
  data: number[]
  gain: number
  baseline: number
  units: 'mV' | 'uV'
}

export interface ECGInterpretation {
  rhythm: string
  rate: number
  axis?: number
  intervals: ECGIntervals
  findings: string[]
  conclusion: string
  cardiologist?: string
  verifiedAt?: string
}

export interface ECGIntervals {
  pr?: number
  qrs?: number
  qt?: number
  qtc?: number
  rr?: number
  pDuration?: number
}

export interface ECGAIAnalysis {
  modelId: string
  modelVersion: string
  abnormalities: ECGAbnormality[]
  overallConfidence: number
  processingTime: number
}

export interface ECGAbnormality {
  type: string
  description: string
  confidence: number
  leadLocations: string[]
  timeRange?: { start: number; end: number }
}

export interface ECGFilterSettings {
  lowPass?: number
  highPass?: number
  notchFilter?: number
  muscleFilter?: boolean
}

export interface ClinicalNote {
  id: string
  type: 'progress' | 'discharge' | 'admission' | 'consultation' | 'procedure' | 'nursing' | 'radiology' | 'pathology' | 'other'
  title: string
  content: string
  author: Provider
  authoredAt: string
  status: 'draft' | 'final' | 'amended' | 'signed'
  encounterId?: string
  tags: string[]
  aiSummary?: string
  aiKeyPoints?: string[]
}

export interface RiskScore {
  id: string
  name: string
  score: number
  maxScore: number
  percentile?: number
  category: 'low' | 'moderate' | 'high' | 'very-high'
  factors: RiskFactor[]
  calculatedAt: string
  validUntil?: string
  reference: string
}

export interface RiskFactor {
  name: string
  value: string | number
  weight: number
  contribution: number
}

export interface AIInsight {
  id: string
  type: 'diagnosis' | 'treatment' | 'monitoring' | 'screening' | 'risk' | 'interaction' | 'guideline' | 'anomaly'
  title: string
  description: string
  confidence: number
  evidence: AIInsightEvidence[]
  actionable: boolean
  actions?: AIInsightAction[]
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: 'new' | 'acknowledged' | 'dismissed' | 'acted-upon'
  createdAt: string
  acknowledgedAt?: string
  acknowledgedBy?: string
  modelId: string
  modelVersion: string
  summary?: string
  recommendations: string[]
}

export interface AIInsightEvidence {
  type: 'lab' | 'imaging' | 'vital' | 'medication' | 'condition' | 'guideline' | 'literature'
  reference: string
  description: string
  strength: 'weak' | 'moderate' | 'strong'
  sourceId?: string
  modality?: string
  weight?: number
}

export interface AIInsightAction {
  label: string
  type: 'order' | 'referral' | 'medication' | 'monitoring' | 'education' | 'documentation'
  payload: Record<string, unknown>
}

export interface Dataset {
  id: string
  name: string
  description: string
  modality: Modality[]
  size: number
  subjects: number
  accessType: 'public' | 'credentialed' | 'research' | 'application'
  source: string
  url: string
  license: string
  citations: string[]
  lastUpdated: string
  features: string[]
  preprocessing: string[]
  splits: DatasetSplit[]
}

export interface DatasetSplit {
  name: string
  size: number
  description: string
}

export interface Model {
  id: string
  name: string
  version: string
  type: 'classification' | 'detection' | 'segmentation' | 'regression' | 'generation' | 'multimodal'
  modality: Modality[]
  task: string
  architecture: string
  framework: string
  inputShape: number[]
  outputShape: number[]
  metrics: ModelMetrics
  trainingData: string[]
  validationData: string[]
  testData: string[]
  artifacts: ModelArtifact[]
  createdAt: string
  updatedAt: string
  status: 'training' | 'validating' | 'deployed' | 'archived' | 'deprecated'
  deployment?: ModelDeployment
}

export interface ModelMetrics {
  accuracy?: number
  precision?: number
  recall?: number
  f1?: number
  auc?: number
  dice?: number
  iou?: number
  sensitivity?: number
  specificity?: number
  ppv?: number
  npv?: number
  custom?: Record<string, number>
}

export interface ModelArtifact {
  name: string
  type: 'weights' | 'config' | 'tokenizer' | 'preprocessor' | 'postprocessor' | 'metadata'
  url: string
  size: number
  checksum: string
}

export interface ModelDeployment {
  endpoint: string
  status: 'running' | 'stopped' | 'error' | 'scaling'
  replicas: number
  resources: { cpu: string; memory: string; gpu?: string }
  latency: { p50: number; p95: number; p99: number }
  throughput: number
  errorRate: number
}

export interface WebSocketMessage {
  type: string
  payload: unknown
  timestamp: string
  requestId?: string
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  read: boolean
  actionUrl?: string
  actionLabel?: string
  metadata?: Record<string, unknown>
  createdAt: string
  readAt?: string
}

export interface AuditLog {
  id: string
  userId: string
  userName: string
  action: string
  resource: string
  resourceId: string
  details: Record<string, unknown>
  ipAddress: string
  userAgent: string
  timestamp: string
  outcome: 'success' | 'failure' | 'partial'
}

export interface SystemMetrics {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkIn: number
  networkOut: number
  activeUsers: number
  requestsPerSecond: number
  averageLatency: number
  errorRate: number
  modelInferenceQueue: number
  storageUsed: number
  storageTotal: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: ApiError
  meta?: Record<string, unknown>
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
  requestId: string
}

export interface LabTrend {
  testName: string
  values: { t: string; v: number }[]
  delta: number
}

export interface LabPanel {
  id: string
  name: string
  category: string
}

export interface LabCategory {
  id: string
  name: string
}

export interface AIAnalysisJob {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  studyId: string
  modelId: string
  createdAt: string
  startedAt?: string
  completedAt?: string
  error?: string
}

export interface AIAnalysisResult {
  id: string
  jobId: string
  findings: AIFinding[]
  summary: string
  confidence: number
  processingTime: number
  createdAt: string
}

export interface ECGMeasurements {
  heartRate: number
  prInterval: number
  qrsDuration: number
  qtInterval: number
  qtcInterval: number
  pAxis: number
  qrsAxis: number
  tAxis: number
}

export interface ECGAIAnalysisJob {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  studyId: string
  createdAt: string
  startedAt?: string
  completedAt?: string
  error?: string
}

export interface ECGAIAnalysisResult {
  id: string
  jobId: string
  abnormalities: ECGAbnormality[]
  overallConfidence: number
  processingTime: number
  createdAt: string
}

export interface ECGComparison {
  id: string
  studyIds: string[]
  differences: Record<string, unknown>
  createdAt: string
}

export interface AIInferenceResult {
  id: string
  modelId: string
  input: Record<string, unknown>
  output: Record<string, unknown>
  confidence: number
  processingTime: number
  createdAt: string
}

export interface AIInsightFeedback {
  id: string
  insightId: string
  rating: 'helpful' | 'not-helpful' | 'incorrect' | 'partially-correct'
  comment?: string
  createdAt: string
  createdBy: string
}

export interface AIExplanation {
  id: string
  insightId: string
  explanation: string
  featureImportance: Record<string, number>
  counterfactuals: Array<{ feature: string; value: unknown; effect: number }>
  generatedAt: string
}

export interface ClinicalGuideline {
  id: string
  code: string
  title: string
  description: string
  category: string
  evidenceLevel: 'A' | 'B' | 'C' | 'D'
  recommendations: Array<{
    id: string
    text: string
    strength: 'strong' | 'conditional'
    quality: 'high' | 'moderate' | 'low' | 'very-low'
  }>
  references: string[]
  updatedAt: string
  source: string
}

export interface DrugInteraction {
  id: string
  drugA: string
  drugB: string
  severity: 'minor' | 'moderate' | 'major' | 'contraindicated'
  description: string
  mechanism?: string
  management?: string
  references: string[]
}

export interface RiskScoreDefinition {
  id: string
  name: string
  description: string
  category: string
  variables: Array<{
    name: string
    type: 'numeric' | 'categorical' | 'binary'
    description: string
    required: boolean
    options?: string[]
  }>
  formula: string
  interpretation: Array<{
    range: [number, number]
    label: string
    risk: 'low' | 'moderate' | 'high' | 'very-high'
  }>
  references: string[]
  validation: {
    population: string
    sampleSize: number
    cStatistic: number
    calibration: string
  }
}

export interface AllergyCheckResult {
  id: string
  patientId: string
  substance: string
  hasAllergy: boolean
  allergies: Allergy[]
  crossReactivities: string[]
  checkedAt: string
}

export interface OrderSet {
  id: string
  name: string
  description: string
  conditionCode?: string
  category: string
  orders: Array<{
    id: string
    type: 'medication' | 'lab' | 'imaging' | 'consultation' | 'procedure' | 'diet' | 'activity'
    details: Record<string, unknown>
    priority: 'routine' | 'urgent' | 'stat'
    condition?: string
  }>
  createdBy: string
  createdAt: string
  updatedAt: string
  version: number
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  services: Record<string, { status: 'up' | 'down' | 'degraded'; latency?: number }>
  version: string
  uptime: number
  timestamp: string
}