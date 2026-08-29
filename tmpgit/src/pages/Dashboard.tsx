import { Link } from 'react-router-dom'
import {
  Users, AlertTriangle, Scan, FlaskConical, Brain,
  ArrowUpRight, HeartPulse, Database, Cpu
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { Badge, PriorityBadge } from '../components/ui/Badge'
import { MOCK_PATIENTS, DATASETS, MODELS } from '../data/mockData'
import { formatRelativeTime, calculateAge, cn } from '../utils/helpers'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts'

const census = [
  { t: '00', ed: 18, icu: 22, ward: 64 },
  { t: '04', ed: 12, icu: 23, ward: 61 },
  { t: '08', ed: 28, icu: 24, ward: 70 },
  { t: '12', ed: 34, icu: 25, ward: 72 },
  { t: '16', ed: 31, icu: 24, ward: 71 },
  { t: '20', ed: 22, icu: 24, ward: 68 },
]

const modalityLoad = [
  { name: 'ECG', v: 142, color: '#ef4444' },
  { name: 'CXR', v: 86, color: '#f59e0b' },
  { name: 'CT', v: 24, color: '#3b82f6' },
  { name: 'PET', v: 6, color: '#ec4899' },
  { name: 'MRI', v: 11, color: '#a855f7' },
  { name: 'Echo', v: 19, color: '#14b8a6' },
]

export function Dashboard() {
  const criticalInsights = MOCK_PATIENTS.flatMap(p =>
    p.aiInsights.filter(i => i.priority === 'critical' || i.priority === 'high').map(i => ({ ...i, patient: p }))
  )
  const criticalLabs = MOCK_PATIENTS.flatMap(p =>
    p.labResults.filter(l => l.interpretation === 'critical').map(l => ({ ...l, patient: p }))
  )

  return (
    <div className="p-6 space-y-6 page-transition">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Clinical command center</h2>
          <p className="text-neutral-500 mt-1">Live census, multimodal AI queue, and MIMIC-linked patients.</p>
        </div>
        <Badge variant="medical" dot>Demo cohort · MIMIC-IV schema</Badge>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 stagger-in">
        {[
          { label: 'Active patients', value: MOCK_PATIENTS.length, icon: Users, trend: '+2 today', color: 'text-medical-600' },
          { label: 'Critical alerts', value: criticalLabs.length + criticalInsights.filter(i => i.priority === 'critical').length, icon: AlertTriangle, trend: 'Needs review', color: 'text-critical-600' },
          { label: 'AI jobs today', value: 48, icon: Brain, trend: 'p95 410ms', color: 'text-clinical-600' },
          { label: 'Studies ingested', value: 288, icon: Scan, trend: 'CXR · ECG · PET', color: 'text-vital-600' },
        ].map(s => (
          <Card key={s.label} variant="hover" className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-neutral-500">{s.label}</div>
                <div className="stat-value mt-1">{s.value}</div>
                <div className="text-xs text-neutral-400 mt-1">{s.trend}</div>
              </div>
              <div className={cn('p-2.5 rounded-xl bg-neutral-100 dark:bg-neutral-800', s.color)}>
                <s.icon className="h-5 w-5" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 p-5">
          <CardHeader className="mb-2">
            <CardTitle>Hospital census (demo)</CardTitle>
            <CardDescription>ED · ICU · Ward occupancy over 24h</CardDescription>
          </CardHeader>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={census}>
                <defs>
                  <linearGradient id="ed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="icu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a855f7" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="ward" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#14b8a6" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#14b8a6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="t" stroke="#737373" fontSize={12} />
                <YAxis stroke="#737373" fontSize={12} />
                <Tooltip contentStyle={{ borderRadius: 12, border: 'none' }} />
                <Area type="monotone" dataKey="ward" stroke="#14b8a6" fill="url(#ward)" strokeWidth={2} />
                <Area type="monotone" dataKey="icu" stroke="#a855f7" fill="url(#icu)" strokeWidth={2} />
                <Area type="monotone" dataKey="ed" stroke="#ef4444" fill="url(#ed)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <CardHeader className="mb-2">
            <CardTitle>Modality volume</CardTitle>
            <CardDescription>Studies processed today</CardDescription>
          </CardHeader>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modalityLoad} layout="vertical">
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" width={48} stroke="#737373" fontSize={12} />
                <Tooltip />
                <Bar dataKey="v" radius={[0, 6, 6, 0]}>
                  {modalityLoad.map(d => <Cell key={d.name} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <CardTitle>Priority AI insights</CardTitle>
              <CardDescription>Fusion layer — not a diagnosis</CardDescription>
            </div>
            <Link to="/cds" className="text-sm text-medical-600 hover:underline flex items-center gap-1">
              Open CDS <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="space-y-3">
            {criticalInsights.slice(0, 5).map(i => (
              <Link
                key={i.id}
                to={`/patients/${i.patient.id}`}
                className={cn('block p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-medical-300 transition-colors', i.priority === 'critical' && 'border-l-4 border-l-critical-500')}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{i.title}</div>
                    <div className="text-xs text-neutral-500 mt-0.5">
                      {i.patient.lastName}, {i.patient.firstName} · {calculateAge(i.patient.dateOfBirth)}{i.patient.sex} · {formatRelativeTime(i.createdAt)}
                    </div>
                  </div>
                  <PriorityBadge priority={i.priority} size="sm" />
                </div>
              </Link>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <CardTitle>Critical labs</CardTitle>
              <CardDescription>MIMIC-IV labevents flagged</CardDescription>
            </div>
            <Link to="/labs" className="text-sm text-medical-600 hover:underline flex items-center gap-1">
              Lab analytics <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="space-y-3">
            {criticalLabs.map(l => (
              <Link key={l.id} to={`/labs/${l.patient.id}`} className="flex items-center justify-between p-3 rounded-xl bg-critical-50 dark:bg-critical-900/20">
                <div>
                  <div className="text-sm font-medium">{l.testName} · {l.value} {l.unit}</div>
                  <div className="text-xs text-neutral-500">{l.patient.lastName}, {l.patient.firstName} · ref {l.referenceRange.low}–{l.referenceRange.high}</div>
                </div>
                <FlaskConical className="h-4 w-4 text-critical-500" />
              </Link>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Database className="h-5 w-5 text-medical-500" />
            <CardTitle>Dataset registry</CardTitle>
          </div>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {DATASETS.map(d => (
              <div key={d.id} className="flex items-center justify-between gap-3 py-2 border-b border-neutral-100 dark:border-neutral-800 last:border-0">
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{d.name}</div>
                  <div className="text-xs text-neutral-500 truncate">{d.role}</div>
                </div>
                <Badge variant={d.status === 'ready' ? 'success' : d.status === 'download' ? 'medical' : 'warning'} size="sm">
                  {d.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="h-5 w-5 text-clinical-500" />
            <CardTitle>Specialized models</CardTitle>
          </div>
          <div className="space-y-3">
            {MODELS.map(m => (
              <div key={m.id} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                <div>
                  <div className="text-sm font-medium">{m.name}</div>
                  <div className="text-xs text-neutral-500">{m.task} · {m.trainingData[0] || 'N/A'}</div>
                </div>
                <div className="text-right">
                  <Badge variant={m.status === 'deployed' ? 'success' : 'clinical'} size="sm">{m.status}</Badge>
                  <div className="text-[11px] font-mono text-neutral-400 mt-1">
                    {m.metrics.auc ? `AUC ${m.metrics.auc}` : m.metrics.dice ? `Dice ${m.metrics.dice}` : m.metrics.mae ? `MAE ${m.metrics.mae}` : `P ${m.metrics.precision}`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <CardTitle>Watchlist</CardTitle>
          <Link to="/patients" className="text-sm text-medical-600 hover:underline">All patients</Link>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {MOCK_PATIENTS.map(p => (
            <Link key={p.id} to={`/patients/${p.id}`} className="card-hover p-4 block">
              <div className="flex items-center gap-2 mb-2">
                <HeartPulse className="h-4 w-4 text-critical-500" />
                <span className="font-medium text-sm truncate">{p.lastName}, {p.firstName}</span>
              </div>
              <div className="text-xs text-neutral-500">{calculateAge(p.dateOfBirth)}{p.sex} · {p.mrn}</div>
              <div className="text-xs text-neutral-400 mt-1 truncate">{p.conditions[0]?.display}</div>
              <div className="flex gap-1 mt-2 flex-wrap">
                {p.imagingStudies.slice(0, 2).map(s => (
                  <Badge key={s.id} size="sm" variant="info">{s.modality}</Badge>
                ))}
                {p.ecgStudies.length > 0 && <Badge size="sm" variant="critical">ECG</Badge>}
              </div>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  )
}
