import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { HeartPulse, Download, Brain, ChevronLeft, ChevronRight } from 'lucide-react'
import { MOCK_PATIENTS, generateECGWaveform, ECG_LEADS } from '../data/mockData'
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ProgressBar } from '../components/ui/ProgressBar'
import { cn, formatRelativeTime, calculateAge } from '../utils/helpers'
import { ECGStudy } from '../types'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export function ECGAnalyzer() {
  const { patientId } = useParams<{ patientId: string }>()
  const [lead, setLead] = useState('II')
  const [seconds, setSeconds] = useState(10)
  const [speed, setSpeed] = useState(25) // mm/s
  const [gain, setGain] = useState(10) // mm/mV
  const [selectedStudy, setSelectedStudy] = useState<ECGStudy | null>(null)
  const [aiAnalysis, setAiAnalysis] = useState<{
    rhythm: string
    rhythmConfidence: number
    intervals: Record<string, { value: number; normal: boolean }>
    axes: Record<string, number>
    hypertrophy: { lvh: boolean; rvh: boolean }
    ischemia: { stElevation: string[]; stDepression: string[]; tInversion: string[] }
    ptbxlClasses: Record<string, number>
    processingTimeMs: number
    modelVersion: string
  } | null>(null)
  const [runningAI, setRunningAI] = useState(false)

  const patient = patientId ? MOCK_PATIENTS.find(p => p.id === patientId) : null
  const studies: (ECGStudy & { patient?: typeof patient })[] = patient?.ecgStudies.map(s => ({ ...s, patient })) || MOCK_PATIENTS.flatMap(p => p.ecgStudies.map(s => ({ ...s, patient: p })))

  useEffect(() => {
    if (studies.length > 0) setSelectedStudy(studies[0])
  }, [studies])

  const waveform = useMemo(() => {
    if (!selectedStudy) return []
    return generateECGWaveform(lead, seconds, selectedStudy.heartRate, selectedStudy.rhythm === 'afib')
  }, [selectedStudy, lead, seconds])

  const runAIAnalysis = async () => {
    if (!selectedStudy) return
    setRunningAI(true)
    await new Promise(r => setTimeout(r, 2000))
    // Simulate PTB-XL model output
    setAiAnalysis({
      rhythm: selectedStudy.rhythm,
      rhythmConfidence: 0.94,
      intervals: {
        pr: { value: selectedStudy.prInterval, normal: selectedStudy.prInterval >= 120 && selectedStudy.prInterval <= 200 },
        qrs: { value: selectedStudy.qrsDuration, normal: selectedStudy.qrsDuration < 120 },
        qt: { value: selectedStudy.qtInterval, normal: selectedStudy.qtInterval < 440 },
        qtc: { value: selectedStudy.qtcInterval, normal: selectedStudy.qtcInterval < 450 },
      },
      axes: { p: 55, qrs: 42, t: 38 },
      hypertrophy: { lvh: false, rvh: false },
      ischemia: { stElevation: [], stDepression: [], tInversion: [] },
      ptbxlClasses: {
        norm: 0.72,
        afib: selectedStudy.rhythm === 'afib' ? 0.91 : 0.08,
        sb: 0.05,
        gsvt: 0.03,
        stach: 0.02,
      },
      processingTimeMs: 187,
      modelVersion: 'ptbxl-transformer-v1.3',
    })
    setRunningAI(false)
  }

  const measurementsData = useMemo(() => {
    if (!selectedStudy) return []
    return [
      { label: 'Heart rate', value: selectedStudy.heartRate, unit: 'bpm', ref: '60–100', status: selectedStudy.heartRate < 60 ? 'low' : selectedStudy.heartRate > 100 ? 'high' : 'normal' },
      { label: 'PR interval', value: selectedStudy.prInterval, unit: 'ms', ref: '120–200', status: selectedStudy.prInterval < 120 ? 'low' : selectedStudy.prInterval > 200 ? 'high' : 'normal' },
      { label: 'QRS duration', value: selectedStudy.qrsDuration, unit: 'ms', ref: '<120', status: selectedStudy.qrsDuration > 120 ? 'high' : 'normal' },
      { label: 'QT interval', value: selectedStudy.qtInterval, unit: 'ms', ref: '<440', status: selectedStudy.qtInterval > 440 ? 'high' : 'normal' },
      { label: 'QTc (Bazett)', value: selectedStudy.qtcInterval, unit: 'ms', ref: '<450', status: selectedStudy.qtcInterval > 450 ? 'high' : 'normal' },
      { label: 'P axis', value: selectedStudy.pAxis, unit: '°', ref: '0–75', status: 'normal' },
      { label: 'QRS axis', value: selectedStudy.qrsAxis, unit: '°', ref: '-30–90', status: selectedStudy.qrsAxis < -30 || selectedStudy.qrsAxis > 90 ? 'abnormal' : 'normal' },
      { label: 'T axis', value: selectedStudy.tAxis, unit: '°', ref: '15–75', status: 'normal' },
    ]
  }, [selectedStudy])

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">ECG analyzer</h2>
          <p className="text-neutral-500 text-sm">
            12-lead viewer · PTB-XL transformer · Interval measurement · Rhythm classification
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>Export PDF</Button>
          <Button variant="outline" leftIcon={<Brain className="h-4 w-4" />} onClick={runAIAnalysis} loading={runningAI}>
            Run AI analysis
          </Button>
        </div>
      </div>

      {patient && (
        <div className="flex items-center gap-4 p-4 bg-neutral-50 dark:bg-neutral-900/50 rounded-xl border border-neutral-200 dark:border-neutral-800">
          <div className="w-12 h-12 rounded-xl bg-gradient-critical flex items-center justify-center">
            <HeartPulse className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold">{patient.lastName}, {patient.firstName}</div>
            <div className="text-sm text-neutral-500">{calculateAge(patient.dateOfBirth)}{patient.sex} · {patient.mrn} · {studies.length} ECG study{studies.length !== 1 ? 's' : ''}</div>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 p-4 bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800">
        <div className="flex items-center gap-2">
          <span className="text-sm text-neutral-500">Lead:</span>
          <div className="flex gap-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg p-1">
            {ECG_LEADS.map(l => (
              <button
                key={l}
                onClick={() => setLead(l)}
                className={cn('px-2.5 py-1 rounded text-sm font-mono transition-colors min-w-[2.5rem]', lead === l ? 'bg-medical-500 text-white' : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700')}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
        <div className="h-6 w-px bg-neutral-200 dark:bg-neutral-700 mx-2" />
        <div className="flex items-center gap-2">
          <span className="text-sm text-neutral-500">Duration:</span>
          <select value={seconds} onChange={e => setSeconds(Number(e.target.value))} className="px-2 py-1 text-sm border rounded bg-white dark:bg-neutral-800">
            <option value={5}>5s</option>
            <option value={10}>10s</option>
            <option value={20}>20s</option>
            <option value={30}>30s</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-neutral-500">Speed:</span>
          <select value={speed} onChange={e => setSpeed(Number(e.target.value))} className="px-2 py-1 text-sm border rounded bg-white dark:bg-neutral-800">
            <option value={10}>10 mm/s</option>
            <option value={25}>25 mm/s</option>
            <option value={50}>50 mm/s</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-neutral-500">Gain:</span>
          <select value={gain} onChange={e => setGain(Number(e.target.value))} className="px-2 py-1 text-sm border rounded bg-white dark:bg-neutral-800">
            <option value={5}>5 mm/mV</option>
            <option value={10}>10 mm/mV</option>
            <option value={20}>20 mm/mV</option>
          </select>
        </div>
        <div className="flex-1" />
        {selectedStudy && (
          <div className="flex items-center gap-4 text-sm text-neutral-500">
            <Badge variant={selectedStudy.rhythm === 'sinus' ? 'success' : 'critical'}>{selectedStudy.rhythm.toUpperCase()}</Badge>
            <span>HR {selectedStudy.heartRate} bpm</span>
            <span>QRS {selectedStudy.qrsDuration}ms</span>
            <span>PR {selectedStudy.prInterval}ms</span>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 p-5">
          <CardHeader className="mb-2">
            <CardTitle>Waveform</CardTitle>
            <CardDescription>Lead {lead} · {seconds}s · {speed} mm/s · {gain} mm/mV</CardDescription>
          </CardHeader>
          <div className="h-80 bg-neutral-900 rounded-xl p-4 relative overflow-hidden">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={waveform} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                <defs>
                  <pattern id="grid" patternUnits="userSpaceOnUse" width={50} height={50}>
                    <rect width="50" height="50" fill="none" />
                    <line x1="0" y1="0" x2="50" y2="0" stroke="#333" strokeWidth="0.5" />
                    <line x1="0" y1="0" x2="0" y2="50" stroke="#333" strokeWidth="0.5" />
                    <line x1="0" y1="25" x2="50" y2="25" stroke="#333" strokeWidth="0.25" strokeDasharray="2,2" />
                    <line x1="25" y1="0" x2="25" y2="50" stroke="#333" strokeWidth="0.25" strokeDasharray="2,2" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
                <XAxis type="number" domain={[0, seconds]} hide />
                <YAxis type="number" hide />
                <Tooltip />
                <Area type="monotone" dataKey="v" stroke="#22c55e" strokeWidth={1.5} fill="none" />
              </AreaChart>
            </ResponsiveContainer>
            <div className="absolute bottom-2 right-2 text-[10px] text-neutral-400 font-mono">
              {lead} · {seconds}s · {speed}mm/s · {gain}mm/mV · {selectedStudy?.heartRate || '—'} bpm
            </div>
            <div className="absolute top-2 left-2 flex gap-1">
              <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => setSeconds(s => Math.min(s + 5, 30))} title="Increase duration">
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => setSeconds(s => Math.max(s - 5, 5))} title="Decrease duration">
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <CardHeader className="mb-2">
            <CardTitle>Measurements</CardTitle>
            <CardDescription>Auto-detected intervals & axes</CardDescription>
          </CardHeader>
          <div className="space-y-2">
            {measurementsData.map(m => (
              <div key={m.label} className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">{m.label}</span>
                  <span className="font-mono font-medium">{m.value} {m.unit}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-neutral-500">Ref: {m.ref}</span>
                  <Badge size="sm" variant={m.status === 'normal' ? 'success' : m.status === 'abnormal' ? 'warning' : m.status === 'high' ? 'warning' : 'info'}>{m.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {aiAnalysis && (
        <Card className="p-5 border-clinical-200 dark:border-clinical-800">
          <CardHeader className="mb-2 flex items-center justify-between">
            <CardTitle>AI analysis (PTB-XL transformer)</CardTitle>
            <Badge variant="clinical" size="sm">{aiAnalysis.modelVersion}</Badge>
          </CardHeader>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 rounded-xl bg-clinical-50 dark:bg-clinical-900/20">
              <div className="text-xs text-clinical-600 dark:text-clinical-400">Rhythm classification</div>
              <div className="font-mono font-medium text-lg mt-1">{aiAnalysis.rhythm.toUpperCase()}</div>
              <ProgressBar value={aiAnalysis.rhythmConfidence * 100} max={100} className="mt-1" size="sm" variant="clinical" showLabel={false} />
            </div>
            <div className="p-3 rounded-xl bg-clinical-50 dark:bg-clinical-900/20">
              <div className="text-xs text-clinical-600 dark:text-clinical-400">Intervals</div>
              <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                {Object.entries(aiAnalysis.intervals).map(([k, v]: [string, any]) => (
                  <div key={k} className={cn('p-1.5 rounded text-center', v.normal ? 'bg-success-100 text-success-700' : 'bg-critical-100 text-critical-700')}>
                    <div className="text-[10px] text-neutral-500">{k.toUpperCase()}</div>
                    <div className="font-mono">{v.value}ms</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-clinical-50 dark:bg-clinical-900/20">
              <div className="text-xs text-clinical-600 dark:text-clinical-400">Electrical axes</div>
              <div className="grid grid-cols-3 gap-2 mt-2 text-sm">
                {Object.entries(aiAnalysis.axes).map(([k, v]) => (
                  <div key={k} className="text-center p-1.5 rounded bg-neutral-100 dark:bg-neutral-800">
                    <div className="text-[10px] text-neutral-500">{k.toUpperCase()}</div>
                    <div className="font-mono">{v}°</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-clinical-50 dark:bg-clinical-900/20">
              <div className="text-xs text-clinical-600 dark:text-clinical-400">Processing</div>
              <div className="text-sm font-mono mt-1">{aiAnalysis.processingTimeMs}ms</div>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-xs text-neutral-500 mb-2">PTB-XL class probabilities</div>
              <div className="space-y-2">
                {Object.entries(aiAnalysis.ptbxlClasses).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between text-sm">
                    <span className="capitalize">{k}</span>
                    <ProgressBar value={v * 100} max={100} className="w-24" size="sm" variant={k === 'afib' ? 'critical' : 'clinical'} showLabel={false} />
                    <span className="font-mono text-xs ml-2">{Math.round(v * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 lg:col-span-3">
              <div className="text-xs text-neutral-500 mb-2">Interpretation</div>
              <div className="text-sm text-neutral-700 dark:text-neutral-300">
                Rhythm: <strong>{aiAnalysis.rhythm}</strong> (confidence {Math.round(aiAnalysis.rhythmConfidence * 100)}%).
                {Object.entries(aiAnalysis.intervals).some(([, v]: [string, any]) => !v.normal) &&
                  ` Abnormal intervals: ${Object.entries(aiAnalysis.intervals).filter(([, v]: [string, any]) => !v.normal).map(([k]) => k.toUpperCase()).join(', ')}.`
                }
                {aiAnalysis.hypertrophy.lvh && ' LVH criteria met.'}
                {aiAnalysis.hypertrophy.rvh && ' RVH criteria met.'}
                {aiAnalysis.ischemia.stElevation.length > 0 && ` ST elevation in ${aiAnalysis.ischemia.stElevation.join(', ')}.`}
                {aiAnalysis.ischemia.stDepression.length > 0 && ` ST depression in ${aiAnalysis.ischemia.stDepression.join(', ')}.`}
              </div>
            </div>
          </div>
        </Card>
      )}

      <Card className="p-5">
        <CardHeader className="mb-2">
          <CardTitle>Available ECG studies</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800">
                <th className="px-4 py-3 text-left font-medium text-neutral-500">Study ID</th>
                <th className="px-4 py-3 text-left font-medium text-neutral-500">Patient</th>
                <th className="px-4 py-3 text-left font-medium text-neutral-500">Acquired</th>
                <th className="px-4 py-3 text-left font-medium text-neutral-500">Rhythm</th>
                <th className="px-4 py-3 text-left font-medium text-neutral-500">HR</th>
                <th className="px-4 py-3 text-left font-medium text-neutral-500">QRS</th>
                <th className="px-4 py-3 text-left font-medium text-neutral-500">QTc</th>
                <th className="px-4 py-3 text-left font-medium text-neutral-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {studies.map(s => (
                <tr
                  key={s.id}
                  onClick={() => setSelectedStudy(s)}
                  className="cursor-pointer hover:bg-neutral-50 dark:hover:bg-neutral-800/50 border-b border-neutral-100 dark:border-neutral-800"
                >
                  <td className="px-4 py-3 font-mono text-neutral-900 dark:text-neutral-100">{s.id}</td>
                  <td className="px-4 py-3">{s.patient ? `${s.patient.lastName}, ${s.patient.firstName}` : '—'}</td>
                  <td className="px-4 py-3 text-neutral-500">{formatRelativeTime(s.acquiredAt)}</td>
                  <td className="px-4 py-3"><Badge variant={s.rhythm === 'sinus' ? 'success' : 'critical'}>{s.rhythm.toUpperCase()}</Badge></td>
                  <td className="px-4 py-3 font-mono">{s.heartRate} bpm</td>
                  <td className="px-4 py-3 font-mono">{s.qrsDuration} ms</td>
                  <td className="px-4 py-3 font-mono">{s.qtcInterval} ms</td>
                  <td className="px-4 py-3"><Badge variant={s.rhythm === 'sinus' ? 'success' : 'warning'}>
                    {s.rhythm === 'sinus' ? 'Normal' : 'Abnormal'}
                  </Badge></td>
                </tr>
              ))}
              {studies.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-neutral-400">No ECG studies</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}