import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  AlertTriangle, Heart, Pill, Scan, FileText, AlertCircle,
  Calendar, Droplets, Brain,
  Zap, Stethoscope, Download, Search, Share2, ChevronLeft
} from 'lucide-react'
import { MOCK_PATIENTS } from '../data/mockData'
import { usePatient } from '../contexts/PatientContext'
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { Badge, PriorityBadge, InterpretationBadge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import { Tabs, TabList, TabTrigger, TabContent } from '../components/ui/Tabs'
import { Table, Column } from '../components/ui/Table'
import { formatRelativeTime, calculateAge, formatDate, cn } from '../utils/helpers'
import { Patient, LabResult, ImagingStudy, ClinicalNote, AIInsight } from '../types'
import { generateECGWaveform, ECG_LEADS } from '../data/mockData'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export function PatientDetail() {
  const params = useParams<{ id: string }>()
  const patientId = params.id
  const navigate = useNavigate()
  const { refreshPatient, getPatient, patients } = usePatient()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (patientId) {
      const p = getPatient(patientId)
      if (p) setPatient(p)
      else refreshPatient(patientId).then(setPatient)
    }
  }, [patientId, getPatient, refreshPatient])

  if (!patient) return <div className="p-6 text-center">Loading patient…</div>

  const timeline = [
    ...patient.labResults.map(l => ({ ...l, type: 'lab' as const, time: l.collectedAt })),
    ...patient.imagingStudies.map(s => ({ ...s, type: 'imaging' as const, time: s.studyDate })),
    ...patient.ecgStudies.map(e => ({ ...e, type: 'ecg' as const, time: e.acquiredAt })),
    ...patient.clinicalNotes.map(n => ({ ...n, type: 'note' as const, time: n.createdAt })),
    ...patient.medications.map(m => ({ ...m, type: 'med' as const, time: m.startDate })),
    ...patient.conditions.map(c => ({ ...c, type: 'condition' as const, time: c.onsetDate })),
  ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())

  return (
    <div className="p-6 space-y-6 page-transition">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/patients')}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold">{patient.lastName}, {patient.firstName}</h2>
              <Badge variant="medical">{patient.mrn}</Badge>
              {patient.aiInsights.some(i => i.status === 'new') && (
                <Badge variant="critical" dot>{patient.aiInsights.filter(i => i.status === 'new').length} new insights</Badge>
              )}
            </div>
            <p className="text-neutral-500 text-sm mt-1">
              {calculateAge(patient.dateOfBirth)}{patient.sex} · {patient.conditions[0]?.display || 'No active conditions'}
              {patient.admission && ` · Admitted ${formatDate(patient.admission.admissionDate)}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button leftIcon={<Download className="h-4 w-4" />} variant="outline">Export CCDA</Button>
          <Button leftIcon={<Share2 className="h-4 w-4" />} variant="outline">Share</Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: 'AI insights', value: patient.aiInsights.length, icon: Brain, color: 'clinical', filter: 'new' },
          { label: 'Critical labs', value: patient.labResults.filter(l => l.interpretation === 'critical').length, icon: AlertCircle, color: 'critical', filter: 'critical' },
          { label: 'Active meds', value: patient.medications.filter(m => m.status === 'active').length, icon: Pill, color: 'medical' },
          { label: 'Imaging studies', value: patient.imagingStudies.length, icon: Scan, color: 'vital' },
          { label: 'Clinical notes', value: patient.clinicalNotes.length, icon: FileText, color: 'info' },
        ].map(s => (
          <Card key={s.label} variant="hover" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-neutral-500">{s.label}</div>
                <div className="stat-value">{s.value}</div>
              </div>
              <div className={cn('p-2 rounded-xl bg-neutral-100 dark:bg-neutral-800', `text-${s.color}-600`)}>
                <s.icon className="h-5 w-5" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex gap-2 border-b border-neutral-200 dark:border-neutral-800">
        {[
          { id: 'overview', label: 'Overview', icon: Heart },
          { id: 'timeline', label: 'Timeline', icon: Calendar },
          { id: 'labs', label: 'Labs', icon: Droplets },
          { id: 'imaging', label: 'Imaging', icon: Scan },
          { id: 'ecg', label: 'ECG', icon: Zap },
          { id: 'notes', label: 'Notes', icon: FileText },
          { id: 'ai', label: 'AI Insights', icon: Brain },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-1.5',
              activeTab === t.id
                ? 'text-medical-600 border-medical-500'
                : 'text-neutral-500 hover:text-neutral-700 border-transparent'
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid lg:grid-cols-3 gap-6">
            <Card className="p-5">
              <CardHeader className="mb-2">
                <CardTitle>Problem list</CardTitle>
              </CardHeader>
              <div className="space-y-2">
                {patient.conditions.map(c => (
                  <div key={c.id} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                    <div>
                      <div className="font-medium">{c.display}</div>
                      <div className="text-xs text-neutral-500">{c.category} · {c.status} · {c.system}</div>
                    </div>
                    <Badge variant={c.severity === 'severe' ? 'critical' : c.severity === 'moderate' ? 'warning' : 'info'} size="sm">
                      {c.severity}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-5 lg:col-span-2">
              <CardHeader className="mb-2">
                <CardTitle>Current medications</CardTitle>
              </CardHeader>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {patient.medications.filter(m => m.status === 'active').map(m => (
                  <div key={m.id} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                    <div className="min-w-0">
                      <div className="font-medium truncate">{m.name} {m.dosage} {m.route}</div>
                      <div className="text-xs text-neutral-500">{m.frequency} · {m.indication}</div>
                    </div>
                    <Badge size="sm" variant={m.status === 'active' ? 'success' : 'warning'}>{m.status}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card className="p-5">
            <CardHeader className="mb-2">
              <CardTitle>Latest AI insights</CardTitle>
              <CardDescription>Fusion layer outputs — clinician review required</CardDescription>
            </CardHeader>
            <div className="space-y-3">
              {patient.aiInsights.slice(0, 3).map(i => (
                <Link key={i.id} to={`/cds/${patient.id}?insight=${i.id}`} className="card-hover p-4 flex items-start gap-3">
                  <div className={cn('p-2 rounded-xl flex-shrink-0', i.priority === 'critical' ? 'bg-critical-100 text-critical-600' : 'bg-clinical-100 text-clinical-600')}>
                    <Brain className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="font-medium truncate">{i.title}</div>
                      <PriorityBadge priority={i.priority} size="sm" />
                    </div>
                    <div className="text-sm text-neutral-500 mt-1 truncate">{i.description}</div>
                    <div className="flex items-center gap-3 mt-2 text-xs text-neutral-400">
                      <span>Type: {i.type}</span>
                      <span>Confidence: {Math.round(i.confidence * 100)}%</span>
                      <span>{formatRelativeTime(i.createdAt)}</span>
                    </div>
                  </div>
                </Link>
              ))}
              {patient.aiInsights.length === 0 && (
                <div className="text-center py-8 text-neutral-400">
                  <Brain className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No AI insights generated yet. Run analysis from CDS tab.</p>
                </div>
              )}
            </div>
          </Card>

          <Card className="p-5">
            <CardHeader className="mb-2">
              <CardTitle>Vital signs trend (24h)</CardTitle>
            </CardHeader>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={patient.vitals.slice(-24).map(v => ({ t: formatDate(v.timestamp), hr: v.heartRate, spo2: v.spo2, sbp: v.systolicBP }))}>
                  <defs>
                    <linearGradient id="hr" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} /><stop offset="100%" stopColor="#ef4444" stopOpacity={0} /></linearGradient>
                    <linearGradient id="spo2" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#14b8a6" stopOpacity={0.3} /><stop offset="100%" stopColor="#14b8a6" stopOpacity={0} /></linearGradient>
                    <linearGradient id="sbp" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                  </defs>
                  <XAxis dataKey="t" stroke="#737373" fontSize={11} />
                  <YAxis stroke="#737373" fontSize={11} />
                  <Tooltip />
                  <Area type="monotone" dataKey="hr" stroke="#ef4444" fill="url(#hr)" strokeWidth={2} />
                  <Area type="monotone" dataKey="spo2" stroke="#14b8a6" fill="url(#spo2)" strokeWidth={2} />
                  <Area type="monotone" dataKey="sbp" stroke="#3b82f6" fill="url(#sbp)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'timeline' && (
        <Card className="p-5">
          <div className="space-y-4">
            {timeline.map((ev, i) => (
              <div key={`${ev.type}-${ev.id}-${i}`} className="flex gap-4 relative">
                <div className="relative flex-shrink-0 w-8">
                  <div className={cn('absolute left-1/2 top-0 -translate-x-1/2 w-3 h-3 rounded-full border-2', getEventColor(ev.type))} />
                  <div className={cn('absolute left-1/2 top-3 -translate-x-1/2 w-0.5 h-full', i < timeline.length - 1 ? 'bg-neutral-200 dark:bg-neutral-700' : 'hidden')} />
                </div>
                <div className="flex-1 p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                  {renderEvent(ev)}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'labs' && (
        <LabTable patient={patient} />
      )}

      {activeTab === 'imaging' && (
        <ImagingTable patient={patient} />
      )}

      {activeTab === 'ecg' && (
        <ECGViewer patient={patient} />
      )}

      {activeTab === 'notes' && (
        <NotesTable patient={patient} />
      )}

      {activeTab === 'ai' && (
        <AIInsightsTable patient={patient} />
      )}
    </div>
  )
}

function getEventColor(type: string) {
  switch (type) {
    case 'lab': return 'bg-vital-500 border-white dark:border-neutral-900'
    case 'imaging': return 'bg-medical-500 border-white dark:border-neutral-900'
    case 'ecg': return 'bg-critical-500 border-white dark:border-neutral-900'
    case 'note': return 'bg-clinical-500 border-white dark:border-neutral-900'
    case 'med': return 'bg-medical-500 border-white dark:border-neutral-900'
    case 'condition': return 'bg-warning-500 border-white dark:border-neutral-900'
    default: return 'bg-neutral-400 border-white'
  }
}

function renderEvent(ev: any) {
  const icon = { lab: Droplets, imaging: Scan, ecg: Zap, note: FileText, med: Pill, condition: AlertTriangle }[ev.type] || FileText
  const Icon = icon

  switch (ev.type) {
    case 'lab':
      return (
        <div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-vital-500" />
              <div className="font-medium">{ev.testName}</div>
            </div>
            <InterpretationBadge interpretation={ev.interpretation} size="sm" />
          </div>
          <div className="text-sm text-neutral-600 dark:text-neutral-400 mt-1 flex flex-wrap gap-4">
            <span>{ev.value} {ev.unit} (ref {ev.referenceRange.low}–{ev.referenceRange.high})</span>
            <span>{formatRelativeTime(ev.time)}</span>
          </div>
        </div>
      )
    case 'imaging':
      return (
        <div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-medical-500" />
              <div className="font-medium">{ev.modality} {ev.bodyPart}</div>
            </div>
            <Badge size="sm" variant="info">{ev.status}</Badge>
          </div>
          <div className="text-sm text-neutral-500 mt-1">{ev.description || 'No description'} · {formatRelativeTime(ev.time)}</div>
        </div>
      )
    case 'ecg':
      return (
        <div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-critical-500" />
              <div className="font-medium">12-lead ECG</div>
            </div>
            <Badge size="sm" variant="critical">{ev.rhythm}</Badge>
          </div>
          <div className="text-sm text-neutral-500 mt-1">HR {ev.heartRate} bpm · QRS {ev.qrsDuration}ms · {formatRelativeTime(ev.time)}</div>
        </div>
      )
    case 'note':
      return (
        <div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-clinical-500" />
              <div className="font-medium">{ev.type}</div>
            </div>
            <span className="text-xs text-neutral-500">{formatRelativeTime(ev.time)}</span>
          </div>
          <div className="text-sm text-neutral-600 dark:text-neutral-400 mt-1 line-clamp-2">{ev.content}</div>
        </div>
      )
    case 'med':
      return (
        <div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-medical-500" />
              <div className="font-medium">{ev.name} {ev.dosage} {ev.route}</div>
            </div>
            <Badge size="sm" variant={ev.status === 'active' ? 'success' : 'warning'}>{ev.status}</Badge>
          </div>
          <div className="text-sm text-neutral-500 mt-1">{ev.frequency} · {ev.indication}</div>
        </div>
      )
    case 'condition':
      return (
        <div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-warning-500" />
              <div className="font-medium">{ev.display}</div>
            </div>
            <Badge size="sm" variant={ev.severity === 'severe' ? 'critical' : ev.severity === 'moderate' ? 'warning' : 'info'}>{ev.severity}</Badge>
          </div>
          <div className="text-sm text-neutral-500 mt-1">{ev.category} · onset {formatDate(ev.onsetDate)}</div>
        </div>
      )
    default:
      return <div>{ev.type}</div>
  }
}

function LabTable({ patient }: { patient: Patient }) {
  const columns: Column<LabResult>[] = [
    { key: 'testName', header: 'Test', accessor: l => l.testName },
    { key: 'value', header: 'Result', accessor: l => `${l.value} ${l.unit}`, render: (_, l) => (
      <div>
        <div className="font-mono font-medium">{l.value} {l.unit}</div>
        <div className="text-xs text-neutral-500">Ref {l.referenceRange.low}–{l.referenceRange.high} {l.referenceRange.unit}</div>
      </div>
    )},
    { key: 'interpretation', header: 'Flag', accessor: l => l.interpretation, render: (_, l) => <InterpretationBadge interpretation={l.interpretation} /> },
    { key: 'collectedAt', header: 'Collected', accessor: l => l.collectedAt, sortable: true, render: v => formatRelativeTime(String(v)) },
  ]
  return <Table data={patient.labResults} columns={columns} keyExtractor={l => l.id} emptyMessage="No lab results" />
}

function ImagingTable({ patient }: { patient: Patient }) {
  const columns: Column<ImagingStudy>[] = [
    { key: 'modality', header: 'Modality', accessor: s => s.modality, render: (_, s) => <Badge variant="info">{s.modality}</Badge> },
    { key: 'bodyPart', header: 'Body part', accessor: s => s.bodyPart },
    { key: 'description', header: 'Description', accessor: s => s.description },
    { key: 'status', header: 'Status', accessor: s => s.status, render: v => <Badge size="sm" variant={v === 'final' ? 'success' : 'warning'}>{String(v)}</Badge> },
    { key: 'studyDate', header: 'Date', accessor: s => s.studyDate, sortable: true, render: v => formatDate(String(v)) },
    { key: 'aiFindings', header: 'AI findings', accessor: s => s.aiFindings?.length || 0, render: v => Number(v) > 0 ? <Badge variant="clinical" size="sm">{String(v)} findings</Badge> : <span className="text-neutral-400">—</span> },
  ]
  return <Table data={patient.imagingStudies} columns={columns} keyExtractor={s => s.id} emptyMessage="No imaging studies" />
}

function NotesTable({ patient }: { patient: Patient }) {
  return (
    <div className="space-y-4">
      {patient.clinicalNotes.map(note => (
        <Card key={note.id} className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="info" size="sm">{note.type}</Badge>
                <span className="text-xs text-neutral-500">{note.author} · {formatRelativeTime(note.createdAt)}</span>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">{note.content}</div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}

function AIInsightsTable({ patient }: { patient: Patient }) {
  return (
    <div className="space-y-4">
      {patient.aiInsights.map(insight => (
        <Card key={insight.id} className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <div className={cn('p-2 rounded-xl', insight.priority === 'critical' ? 'bg-critical-100 text-critical-600' : 'bg-clinical-100 text-clinical-600')}>
                  <Brain className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-medium">{insight.title}</div>
                  <div className="flex items-center gap-2 text-xs text-neutral-500 mt-0.5">
                    <span>Type: {insight.type}</span>
                    <PriorityBadge priority={insight.priority} size="sm" />
                    <span>Confidence: {Math.round(insight.confidence * 100)}%</span>
                  </div>
                </div>
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">{insight.description}</div>
              {insight.recommendations.length > 0 && (
                <div className="mt-3 space-y-1">
                  {insight.recommendations.map((r, i) => (
                    <div key={i} className="text-sm flex items-start gap-2 text-medical-700 dark:text-medical-300">
                      <span className="mt-0.5">→</span> {r}
                    </div>
                  ))}
                </div>
              )}
              {insight.evidence.length > 0 && (
                <details className="mt-3">
                  <summary className="text-sm text-medical-600 cursor-pointer">Evidence sources ({insight.evidence.length})</summary>
                  <ul className="mt-2 space-y-1 text-xs text-neutral-500">
                    {insight.evidence.map((e, i) => <li key={i}>{e.type} · {e.reference} (strength {e.strength})</li>)}
                  </ul>
                </details>
              )}
            </div>
          </div>
        </Card>
      ))}
      {patient.aiInsights.length === 0 && (
        <Card className="p-12 text-center">
          <Brain className="h-16 w-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" />
          <p className="text-neutral-500">No AI insights. Trigger multimodal fusion from Clinical DS tab.</p>
        </Card>
      )}
    </div>
  )
}

function ECGViewer({ patient }: { patient: Patient }) {
  const [lead, setLead] = useState('II')
  const [seconds, setSeconds] = useState(10)

  if (patient.ecgStudies.length === 0) {
    return (
      <Card className="p-12 text-center">
        <Zap className="h-16 w-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" />
        <p className="text-neutral-500">No ECG studies for this patient.</p>
      </Card>
    )
  }

  const study = patient.ecgStudies[0]
  const waveform = generateECGWaveform(lead, seconds, study.heartRate, study.rhythm === 'afib')

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="font-semibold">ECG Study {study.id}</h3>
          <p className="text-sm text-neutral-500">HR {study.heartRate} bpm · {study.rhythm} · QRS {study.qrsDuration}ms · PR {study.prInterval}ms</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex gap-1">
            {ECG_LEADS.map(l => (
              <button
                key={l}
                onClick={() => setLead(l)}
                className={cn('px-2 py-1 rounded text-sm font-mono transition-colors', lead === l ? 'bg-medical-500 text-white' : 'text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800')}
              >
                {l}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-neutral-500">Duration</span>
            <select value={seconds} onChange={e => setSeconds(Number(e.target.value))} className="px-2 py-1 text-sm border rounded bg-white dark:bg-neutral-800">
              <option value={5}>5s</option>
              <option value={10}>10s</option>
              <option value={20}>20s</option>
            </select>
          </div>
        </div>
      </div>
      <div className="h-64 bg-neutral-900 rounded-xl p-4 relative overflow-hidden">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={waveform} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
            <XAxis type="number" domain={[0, seconds]} hide />
            <YAxis type="number" hide />
            <Area type="monotone" dataKey="v" stroke="#22c55e" strokeWidth={1.5} fill="none" />
          </AreaChart>
        </ResponsiveContainer>
        <div className="absolute bottom-2 right-2 text-[10px] text-neutral-400 font-mono">
          {lead} · {seconds}s · {study.heartRate} bpm
        </div>
      </div>
    </Card>
  )
}