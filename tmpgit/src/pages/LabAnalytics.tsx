import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  TrendingUp, TrendingDown, AlertCircle, Search,
  Download, Calendar, BarChart2, FlaskConical
} from 'lucide-react'
import { MOCK_PATIENTS } from '../data/mockData'
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { InterpretationBadge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Table, Column, Pagination } from '../components/ui/Table'
import { cn, formatDate, formatRelativeTime } from '../utils/helpers'
import { LabResult } from '../types'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell,
} from 'recharts'

export function LabAnalytics() {
  const { patientId } = useParams<{ patientId: string }>()
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d')
  const [searchQ, setSearchQ] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 15

  const patient = patientId ? MOCK_PATIENTS.find(p => p.id === patientId) : null
  interface LabWithPatient extends LabResult {
    patient?: { id: string; lastName: string; firstName: string; mrn: string }
  }

  const allLabs: LabWithPatient[] = (patient?.labResults as LabWithPatient[]) || MOCK_PATIENTS.flatMap(p => p.labResults.map(l => ({ ...l, patient: { id: p.id, lastName: p.lastName, firstName: p.firstName, mrn: p.mrn } })))

  const filtered = useMemo(() => {
    let rows = allLabs
    const now = new Date()
    const cutoff = new Date(now)
    if (timeRange === '24h') cutoff.setHours(cutoff.getHours() - 24)
    else if (timeRange === '7d') cutoff.setDate(cutoff.getDate() - 7)
    else if (timeRange === '30d') cutoff.setDate(cutoff.getDate() - 30)

    rows = rows.filter(l => l.collectedAt && new Date(l.collectedAt) >= cutoff)
    if (searchQ) rows = rows.filter(l =>
      l.testName.toLowerCase().includes(searchQ.toLowerCase()) ||
      l.value.toString().includes(searchQ) ||
      (l.patient && (l.patient.lastName.toLowerCase().includes(searchQ.toLowerCase()) || l.patient.mrn.includes(searchQ)))
    )
    return rows
  }, [allLabs, timeRange, searchQ])

  const paged = filtered.slice((page - 1) * pageSize, page * pageSize)

  const criticalCount = filtered.filter(l => l.interpretation === 'critical').length
  const highCount = filtered.filter(l => l.interpretation === 'high').length
  const lowCount = filtered.filter(l => l.interpretation === 'low').length
  const deltaCount = filtered.filter(l => l.delta !== undefined).length

  const trendData = useMemo(() => {
    const groups = new Map<string, { testName: string; values: { t: string; v: number }[] }>()
    filtered.forEach(l => {
      const key = l.testName
      if (!groups.has(key)) groups.set(key, { testName: l.testName, values: [] })
      groups.get(key)!.values.push({ t: formatDate(l.collectedAt || new Date().toISOString()), v: typeof l.value === 'number' ? l.value : parseFloat(l.value as string) })
    })
    return Array.from(groups.values()).map(g => ({
      ...g,
      values: g.values.sort((a, b) => new Date(a.t).getTime() - new Date(b.t).getTime())
    }))
  }, [filtered])

  const topTrending = trendData
    .filter(t => t.values.length >= 2)
    .map(t => ({ ...t, delta: t.values[t.values.length - 1].v - t.values[0].v }))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 6)

  const columns: Column<any>[] = [
    { key: 'testName', header: 'Test', accessor: l => l.testName },
    { key: 'value', header: 'Result', accessor: l => l.value, render: (_, l) => (
      <div className="font-mono font-medium">{l.value} {l.unit}</div>
    )},
    { key: 'ref', header: 'Reference', accessor: l => `${l.referenceRange.low}–${l.referenceRange.high} ${l.referenceRange.unit}` },
    { key: 'interpretation', header: 'Flag', accessor: l => l.interpretation, render: (_, l) => <InterpretationBadge interpretation={l.interpretation} /> },
    { key: 'delta', header: 'Δ', accessor: l => l.delta, render: (v: number | undefined, l) => l.delta !== undefined ? (
      <span className={cn('font-mono font-medium', v > 0 ? 'text-critical-600' : v < 0 ? 'text-medical-600' : 'text-neutral-500')}>
        {v > 0 ? '+' : ''}{v.toFixed(1)}
      </span>
    ) : <span className="text-neutral-400">—</span> },
    { key: 'collectedAt', header: 'Collected', accessor: l => l.collectedAt, sortable: true, render: v => formatRelativeTime(String(v)) },
    { key: 'patient', header: 'Patient', accessor: l => l.patient, render: (_, l) => l.patient ? (
      <span className="text-sm">{l.patient.lastName}, {l.patient.firstName} · {l.patient.mrn}</span>
    ) : <span>—</span> },
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Lab analytics</h2>
          <p className="text-neutral-500 text-sm">
            MIMIC-IV labevents · Trend analysis · Delta detection · Reference-range flagging
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>Export CSV</Button>
          <Button variant="outline" leftIcon={<Calendar className="h-4 w-4" />} onClick={() => setTimeRange('30d')}>30 days</Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: 'Total results', value: filtered.length, icon: FlaskConical, color: 'text-medical-600' },
          { label: 'Critical', value: criticalCount, icon: AlertCircle, color: 'text-critical-600' },
          { label: 'High', value: highCount, icon: TrendingUp, color: 'text-warning-600' },
          { label: 'Low', value: lowCount, icon: TrendingDown, color: 'text-info-600' },
          { label: 'With trend', value: deltaCount, icon: BarChart2, color: 'text-clinical-600' },
        ].map(s => (
          <Card key={s.label} variant="hover" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-neutral-500">{s.label}</div>
                <div className="stat-value">{s.value}</div>
              </div>
              <div className={cn('p-2 rounded-xl bg-neutral-100 dark:bg-neutral-800', s.color)}>
                <s.icon className="h-5 w-5" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex gap-2 border-b border-neutral-200 dark:border-neutral-800 mb-4">
        {['24h', '7d', '30d', 'all'].map(r => (
          <button
            key={r}
            onClick={() => setTimeRange(r as any)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              timeRange === r ? 'text-medical-600 border-medical-500' : 'text-neutral-500 hover:text-neutral-700 border-transparent'
            )}
          >
            {r}
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 p-5">
          <CardHeader className="mb-2">
            <CardTitle>Trending tests</CardTitle>
            <CardDescription>Top 6 tests by absolute change over selected range</CardDescription>
          </CardHeader>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={topTrending.flatMap(t => t.values.map(v => ({ time: v.t, [t.testName]: v.v }))).reduce((acc, curr) => {
                const existing = acc.find(a => a.time === curr.time)
                if (existing) { Object.assign(existing, curr); return acc }
                return [...acc, curr]
              }, [] as any[])} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <defs>
                  {topTrending.map((t, i) => (
                    <linearGradient key={t.testName} id={`trend${i}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={['#ef4444', '#14b8a6', '#3b82f6', '#a855f7', '#f59e0b', '#ec4899'][i]} stopOpacity={0.25} />
                      <stop offset="100%" stopColor={['#ef4444', '#14b8a6', '#3b82f6', '#a855f7', '#f59e0b', '#ec4899'][i]} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <XAxis dataKey="time" stroke="#737373" fontSize={11} />
                <YAxis stroke="#737373" fontSize={11} />
                <Tooltip />
                {topTrending.map((t, i) => (
                  <Area key={t.testName} type="monotone" dataKey={t.testName} stroke={['#ef4444', '#14b8a6', '#3b82f6', '#a855f7', '#f59e0b', '#ec4899'][i]} fill={`url(#trend${i})`} strokeWidth={2} />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <CardHeader className="mb-2">
            <CardTitle>Flagged tests</CardTitle>
            <CardDescription>Critical / High / Low breakdown</CardDescription>
          </CardHeader>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: 'Normal', value: filtered.length - criticalCount - highCount - lowCount, color: '#22c55e' },
                { name: 'Low', value: lowCount, color: '#3b82f6' },
                { name: 'High', value: highCount, color: '#f59e0b' },
                { name: 'Critical', value: criticalCount, color: '#ef4444' },
              ]} layout="vertical">
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" width={56} stroke="#737373" fontSize={11} />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {[
                    { name: 'Normal', color: '#22c55e' },
                    { name: 'Low', color: '#3b82f6' },
                    { name: 'High', color: '#f59e0b' },
                    { name: 'Critical', color: '#ef4444' },
                  ].map(d => <Cell key={d.name} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-5">
          <CardHeader className="mb-2">
            <CardTitle>Panels by category</CardTitle>
          </CardHeader>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { panel: 'CBC', count: 142, color: '#ef4444' },
                { panel: 'BMP', count: 98, color: '#f59e0b' },
                { panel: 'LFT', count: 67, color: '#3b82f6' },
                { panel: 'Coag', count: 34, color: '#a855f7' },
                { panel: 'Cardiac', count: 28, color: '#ec4899' },
                { panel: 'ABG', count: 19, color: '#14b8a6' },
              ]} layout="vertical">
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="panel" width={48} stroke="#737373" fontSize={11} />
                <Tooltip />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {[{name:'CBC',color:'#ef4444'},{name:'BMP',color:'#f59e0b'},{name:'LFT',color:'#3b82f6'},{name:'Coag',color:'#a855f7'},{name:'Cardiac',color:'#ec4899'},{name:'ABG',color:'#14b8a6'}].map(d => <Cell key={d.name} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <CardHeader className="mb-2">
            <CardTitle>Delta alerts</CardTitle>
            <CardDescription>Significant changes from baseline</CardDescription>
          </CardHeader>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {topTrending.slice(0, 8).map(t => (
              <div key={t.testName} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                <div>
                  <div className="font-medium text-sm">{t.testName}</div>
                  <div className="text-xs text-neutral-500">{t.values[0]?.t} → {t.values[t.values.length-1]?.t}</div>
                </div>
                <div className="text-right">
                  <div className={cn('font-mono font-medium', t.delta > 0 ? 'text-critical-600' : 'text-medical-600')}>
                    {t.delta > 0 ? '+' : ''}{t.delta.toFixed(1)} {t.values[0] ? '' : ''}
                  </div>
                  <div className="text-xs text-neutral-400">{t.values[0]?.v?.toFixed(1)} → {t.values[t.values.length-1]?.v?.toFixed(1)}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <CardTitle>All lab results</CardTitle>
          <div className="flex items-center gap-2">
            <div className="relative max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
              <input
                type="search"
                placeholder="Search test name, value, patient..."
                value={searchQ}
                onChange={e => { setSearchQ(e.target.value); setPage(1) }}
                className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800"
              />
            </div>
          </div>
        </div>
        <Table
          data={paged}
          columns={columns}
          keyExtractor={l => l.id}
          onRowClick={l => l.patient && window.history.pushState(null, '', `/labs/${l.patient.id}`)}
          sortBy="collectedAt"
          sortOrder="desc"
        />
        <Pagination
          currentPage={page}
          totalPages={Math.max(1, Math.ceil(filtered.length / pageSize))}
          totalItems={filtered.length}
          pageSize={pageSize}
          onPageChange={setPage}
        />
      </Card>
    </div>
  )
}

