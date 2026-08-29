import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Search, Plus } from 'lucide-react'
import { MOCK_PATIENTS } from '../data/mockData'
import { Table, Column, Pagination } from '../components/ui/Table'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Patient } from '../types'
import { calculateAge, formatRelativeTime } from '../utils/helpers'

export function PatientList() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [q, setQ] = useState(params.get('q') || '')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('updatedAt')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const pageSize = 10

  const filtered = useMemo(() => {
    const query = q.toLowerCase()
    let rows = MOCK_PATIENTS.filter(p =>
      !query ||
      p.lastName.toLowerCase().includes(query) ||
      p.firstName.toLowerCase().includes(query) ||
      p.mrn.toLowerCase().includes(query) ||
      p.id.includes(query) ||
      p.conditions.some(c => c.display.toLowerCase().includes(query))
    )
    rows = [...rows].sort((a, b) => {
      const av = (a as unknown as Record<string, string>)[sortBy] ?? ''
      const bv = (b as unknown as Record<string, string>)[sortBy] ?? ''
      return sortOrder === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av))
    })
    return rows
  }, [q, sortBy, sortOrder])

  const pageRows = filtered.slice((page - 1) * pageSize, page * pageSize)

  const columns: Column<Patient>[] = [
    { key: 'name', header: 'Patient', accessor: p => `${p.lastName}, ${p.firstName}`, render: (_, p) => (
      <div>
        <div className="font-medium">{p.lastName}, {p.firstName}</div>
        <div className="text-xs text-neutral-500">{p.mrn}</div>
      </div>
    )},
    { key: 'age', header: 'Age / Sex', accessor: p => `${calculateAge(p.dateOfBirth)}${p.sex}` },
    { key: 'dx', header: 'Primary problem', accessor: p => p.conditions[0]?.display || '—', render: (v) => <span className="text-sm">{String(v)}</span> },
    { key: 'mods', header: 'Modalities', accessor: p => p.id, render: (_, p) => (
      <div className="flex flex-wrap gap-1">
        {p.labResults.length > 0 && <Badge size="sm" variant="medical">Labs</Badge>}
        {p.imagingStudies.map(s => <Badge key={s.id} size="sm" variant="info">{s.modality}</Badge>)}
        {p.ecgStudies.length > 0 && <Badge size="sm" variant="critical">ECG</Badge>}
      </div>
    )},
    { key: 'alerts', header: 'Alerts', accessor: p => p.aiInsights.filter(i => i.status === 'new').length, render: (v) => Number(v) > 0 ? <Badge variant="critical">{String(v)} new</Badge> : <span className="text-neutral-400">—</span> },
    { key: 'updatedAt', header: 'Updated', accessor: p => p.updatedAt, sortable: true, render: v => <span className="text-xs text-neutral-500">{formatRelativeTime(String(v))}</span> },
  ]

  return (
    <div className="p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">Patients</h2>
          <p className="text-neutral-500 text-sm">MIMIC-IV demo subject_ids · linked ED / ECG / imaging when present</p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => navigate('/patients/10012853')}>Open index case</Button>
      </div>
      <div className="max-w-md">
        <Input
          placeholder="Search name, MRN, subject_id, diagnosis..."
          value={q}
          onChange={e => { setQ(e.target.value); setPage(1) }}
          leftIcon={<Search className="h-4 w-4" />}
        />
      </div>
      <Table
        data={pageRows}
        columns={columns}
        keyExtractor={p => p.id}
        onRowClick={p => navigate(`/patients/${p.id}`)}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={(k, o) => { setSortBy(k); setSortOrder(o) }}
      />
      <Pagination
        currentPage={page}
        totalPages={Math.max(1, Math.ceil(filtered.length / pageSize))}
        totalItems={filtered.length}
        pageSize={pageSize}
        onPageChange={setPage}
        showPageSizeSelector={false}
      />
    </div>
  )
}
