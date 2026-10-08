import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart,
} from 'recharts'
import { AlertTriangle, Atom, Loader2, Play } from 'lucide-react'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { qmlApi, QmlBenchmark, QmlJob, QmlModelInfo, QmlPrediction } from '../services/api'

const MODEL_LABELS: Record<string, string> = {
  logreg: 'Logistic regression',
  svm_rbf: 'SVM (RBF)',
  random_forest: 'Random forest',
  mlp: 'MLP',
  qsvm: 'Quantum-kernel SVM',
  vqc: 'VQC',
  hybrid_qnn: 'Hybrid QNN',
}
const MODEL_IDS = Object.keys(MODEL_LABELS)
const QUANTUM = ['qsvm', 'vqc', 'hybrid_qnn']
const CLASSICAL = ['logreg', 'svm_rbf', 'random_forest', 'mlp']
const METRICS = ['accuracy', 'sensitivity', 'specificity', 'auc', 'f1'] as const

// Fixed categorical slot per model (dataviz reference palette); light/dark steps via CSS variables.
const PALETTE_CSS = `
.qlab { --qlab-grid:#ecebe7; --qlab-axis:#52514e; --logreg:#2a78d6; --svm_rbf:#eb6834; --random_forest:#1baf7a;
  --mlp:#eda100; --qsvm:#e87ba4; --vqc:#008300; --hybrid_qnn:#4a3aa7; }
.dark .qlab { --qlab-grid:#2e2e2c; --qlab-axis:#c3c2b7; --logreg:#3987e5; --svm_rbf:#d95926; --random_forest:#199e70;
  --mlp:#c98500; --qsvm:#d55181; --vqc:#008300; --hybrid_qnn:#9085e9; }
`
const color = (model: string) => `var(--${model})`
const fmt = (v: number | undefined, d = 3) => (v === undefined || Number.isNaN(v) ? '-' : v.toFixed(d))

export function QuantumLab() {
  const benchmark = useQuery({ queryKey: ['qml-benchmark'], queryFn: qmlApi.getBenchmark, retry: false })
  const datasets = Object.keys(benchmark.data?.datasets ?? {})
  const [dataset, setDataset] = useState('breast_cancer')
  const [model, setModel] = useState('qsvm')
  const [nQubits, setNQubits] = useState(6)
  const [job, setJob] = useState<QmlJob | null>(null)
  const [jobError, setJobError] = useState<string | null>(null)

  useEffect(() => {
    if (datasets.length && !datasets.includes(dataset)) setDataset(datasets[0])
  }, [datasets, dataset])

  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'failed') return
    const t = setTimeout(async () => {
      try {
        setJob(await qmlApi.getJob(job.job_id))
      } catch {
        setJobError('Lost contact with the training job.')
      }
    }, 1500)
    return () => clearTimeout(t)
  }, [job])

  const startTraining = async () => {
    setJobError(null)
    try {
      setJob(await qmlApi.train(dataset, model, nQubits))
    } catch {
      setJobError('Could not start training. Is the API running on port 8000?')
    }
  }

  const ds = benchmark.data?.datasets[dataset]

  return (
    <div className="qlab space-y-6 p-6">
      <style>{PALETTE_CSS}</style>
      <div
        role="alert"
        className="flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100"
      >
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
        <p>
          <strong>Research prototype - not a diagnostic tool.</strong> Models are trained on public benchmark
          datasets (UCI Breast Cancer Wisconsin, UCI Heart Disease) and run on a quantum simulator. Do not use the
          outputs for clinical decisions.
        </p>
      </div>

      <header className="flex items-center gap-3">
        <Atom className="h-7 w-7 text-medical-600" aria-hidden />
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900 dark:text-white">Quantum Lab</h1>
          <p className="text-sm text-neutral-500">
            Hybrid quantum-classical models vs classical baselines (SIH26139)
          </p>
        </div>
      </header>

      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <Picker label="Dataset" value={dataset} onChange={setDataset}
            options={(datasets.length ? datasets : ['breast_cancer', 'heart']).map(d => [d, benchmark.data?.datasets[d]?.info.title ?? d])} />
          <Picker label="Model" value={model} onChange={setModel} options={MODEL_IDS.map(m => [m, MODEL_LABELS[m]])} />
          <Picker label="Qubits" value={String(nQubits)} onChange={v => setNQubits(Number(v))}
            options={[4, 5, 6, 7, 8].map(n => [String(n), `${n} qubits`])} />
          <Button onClick={startTraining} disabled={job?.status === 'queued' || job?.status === 'running'}
            leftIcon={<Play className="h-4 w-4" />}>
            Train on held-out split
          </Button>
          <Button variant="outline" onClick={() => benchmark.refetch()}>Reload benchmark</Button>
        </div>
        <JobStatus job={job} error={jobError} />
      </Card>

      {benchmark.isLoading && <p className="text-sm text-neutral-500">Loading benchmark results...</p>}
      {benchmark.isError && (
        <Card>
          <p className="text-sm text-neutral-600 dark:text-neutral-300">
            No benchmark results available from the API. Start it with{' '}
            <code>python -m uvicorn backend.main:app --port 8000</code> and run{' '}
            <code>python -m backend.ml.quantum.benchmark --dataset all</code>.
          </p>
        </Card>
      )}

      {ds && benchmark.data && (
        <>
          <ComparisonTable data={benchmark.data} dataset={dataset} />
          <div className="grid gap-6 xl:grid-cols-2">
            <RocChart models={ds.models} />
            <LearningCurveChart models={ds.models} />
          </div>
          <ImportanceChart models={ds.models} model={model} />
          <PredictionPanel
            modelId={job?.status === 'done' && job.model_id ? job.model_id : `${dataset}_${model}`}
            available={benchmark.data.trained_models}
          />
        </>
      )}
    </div>
  )
}

function Picker({ label, value, onChange, options }: {
  label: string; value: string; onChange: (v: string) => void; options: [string, string][]
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-neutral-600 dark:text-neutral-300">
      {label}
      <select value={value} onChange={e => onChange(e.target.value)}
        className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  )
}

function JobStatus({ job, error }: { job: QmlJob | null; error: string | null }) {
  if (error) return <p className="mt-3 text-sm text-red-600" role="status">{error}</p>
  if (!job) return null
  const running = job.status === 'queued' || job.status === 'running'
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-neutral-700 dark:text-neutral-200" role="status">
      {running && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      <span>Job {job.job_id}: {job.status}</span>
      {job.status === 'done' && job.holdout_metrics && (
        <span>
          - held-out accuracy {fmt(job.holdout_metrics.accuracy)}, sensitivity {fmt(job.holdout_metrics.sensitivity)},
          specificity {fmt(job.holdout_metrics.specificity)}, AUC {fmt(job.holdout_metrics.auc)}
        </span>
      )}
      {job.status === 'failed' && <span className="text-red-600">{job.error}</span>}
    </div>
  )
}

function ComparisonTable({ data, dataset }: { data: QmlBenchmark; dataset: string }) {
  const ds = data.datasets[dataset]
  return (
    <Card padding="none">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">Classical vs quantum: {ds.info.title}</h2>
        <p className="text-xs text-neutral-500">
          Stratified 5-fold CV (mean ± std), n={ds.n_samples}, positive class = {ds.info.positive_class}.
          Run {data.generated_at} (commit {data.git_commit ?? 'n/a'}).
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left text-xs uppercase text-neutral-500 dark:bg-neutral-800">
            <tr>
              <th className="px-4 py-2">Model</th>
              <th className="px-4 py-2">Family</th>
              {METRICS.map(m => <th key={m} className="px-4 py-2">{m}</th>)}
              <th className="px-4 py-2">Train s</th>
              <th className="px-4 py-2">ms/sample</th>
              <th className="px-4 py-2">Qubits / depth</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(ds.models).map(([id, r]) => (
              <tr key={id} className="border-t border-neutral-200 text-neutral-800 dark:border-neutral-800 dark:text-neutral-100">
                <td className="px-4 py-2 font-medium">
                  <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ background: color(id) }} aria-hidden />
                  {MODEL_LABELS[id] ?? id}
                </td>
                <td className="px-4 py-2 capitalize">{r.family}</td>
                {METRICS.map(m => (
                  <td key={m} className="px-4 py-2 tabular-nums">
                    {fmt(r.metrics[m]?.mean)} <span className="text-neutral-400">± {fmt(r.metrics[m]?.std)}</span>
                  </td>
                ))}
                <td className="px-4 py-2 tabular-nums">{fmt(r.metrics.train_time_s?.mean, 2)}</td>
                <td className="px-4 py-2 tabular-nums">{fmt(r.metrics.infer_ms_per_sample?.mean, 3)}</td>
                <td className="px-4 py-2 tabular-nums">{r.n_qubits ? `${r.n_qubits} / ${r.circuit_depth}` : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

type Models = QmlBenchmark['datasets'][string]['models']

function ChartFrame({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <Card>
      <h2 className="text-base font-semibold text-neutral-900 dark:text-white">{title}</h2>
      <p className="mb-3 text-xs text-neutral-500">{subtitle}</p>
      {children}
    </Card>
  )
}

function SeriesLines({ models, ids, rows, xKey, xLabel, yLabel }: {
  models: Models; ids: string[]; rows: Record<string, number>[]; xKey: string; xLabel: string; yLabel: string
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 20, left: 4 }}>
        <CartesianGrid stroke="var(--qlab-grid)" vertical={false} />
        <XAxis dataKey={xKey} type="number" domain={['dataMin', 'dataMax']} tick={{ fill: 'var(--qlab-axis)', fontSize: 11 }}
          label={{ value: xLabel, position: 'insideBottom', offset: -10, fill: 'var(--qlab-axis)', fontSize: 11 }} />
        <YAxis domain={[0, 1]} tick={{ fill: 'var(--qlab-axis)', fontSize: 11 }}
          label={{ value: yLabel, angle: -90, position: 'insideLeft', fill: 'var(--qlab-axis)', fontSize: 11 }} />
        <Tooltip formatter={(v: number) => v.toFixed(3)} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {ids.filter(id => models[id]).map(id => (
          <Line key={id} dataKey={id} name={MODEL_LABELS[id]} stroke={color(id)} strokeWidth={2}
            dot={false} connectNulls isAnimationActive={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

function RocChart({ models }: { models: Models }) {
  const [group, setGroup] = useState<'quantum' | 'classical'>('quantum')
  const ids = group === 'quantum' ? QUANTUM : CLASSICAL
  const rows = useMemo(() => ids.filter(id => models[id]).flatMap(id =>
    models[id].roc.fpr.map((fpr, i) => ({ fpr, [id]: models[id].roc.tpr[i] }))), [models, ids])
  return (
    <ChartFrame title="ROC curves" subtitle="Pooled out-of-fold predictions. Positive class = disease.">
      <GroupToggle group={group} setGroup={setGroup} />
      <SeriesLines models={models} ids={ids} rows={rows} xKey="fpr" xLabel="False positive rate" yLabel="Sensitivity" />
    </ChartFrame>
  )
}

function LearningCurveChart({ models }: { models: Models }) {
  const [group, setGroup] = useState<'quantum' | 'classical'>('quantum')
  const ids = group === 'quantum' ? QUANTUM : CLASSICAL
  const rows = useMemo(() => {
    const byN: Record<number, Record<string, number>> = {}
    ids.filter(id => models[id]).forEach(id => models[id].learning_curve.forEach(p => {
      byN[p.n_train] = { ...(byN[p.n_train] ?? { n: p.n_train }), [id]: p.val_accuracy }
    }))
    return Object.values(byN).sort((a, b) => a.n - b.n)
  }, [models, ids])
  return (
    <ChartFrame title="Learning curves" subtitle="Validation accuracy vs training-set size (held-out 20%).">
      <GroupToggle group={group} setGroup={setGroup} />
      <SeriesLines models={models} ids={ids} rows={rows} xKey="n" xLabel="Training samples" yLabel="Val. accuracy" />
    </ChartFrame>
  )
}

function GroupToggle({ group, setGroup }: { group: string; setGroup: (g: 'quantum' | 'classical') => void }) {
  return (
    <div className="mb-2 flex gap-2" role="group" aria-label="Model family">
      {(['quantum', 'classical'] as const).map(g => (
        <button key={g} onClick={() => setGroup(g)} aria-pressed={group === g}
          className={`rounded-md px-3 py-1 text-xs font-medium ${group === g
            ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900'
            : 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300'}`}>
          {g === 'quantum' ? 'Quantum / hybrid' : 'Classical'}
        </button>
      ))}
    </div>
  )
}

function ImportanceChart({ models, model }: { models: Models; model: string }) {
  const r = models[model]
  if (!r) return null
  const rows = Object.entries(r.explain.permutation_importance)
    .map(([feature, value]) => ({ feature, value }))
    .sort((a, b) => b.value - a.value)
  return (
    <ChartFrame title={`Feature importance: ${MODEL_LABELS[model]}`}
      subtitle={`Permutation importance (drop in AUC, held-out 20%) on the ${r.explain.selected_features.length} selected features${r.explain.kernel_alignment !== undefined ? ` · kernel-target alignment ${fmt(r.explain.kernel_alignment)}` : ''}.`}>
      <ResponsiveContainer width="100%" height={40 + rows.length * 32}>
        <BarChart data={rows} layout="vertical" margin={{ left: 24, right: 16 }}>
          <CartesianGrid stroke="var(--qlab-grid)" horizontal={false} />
          <XAxis type="number" tick={{ fill: 'var(--qlab-axis)', fontSize: 11 }} />
          <YAxis type="category" dataKey="feature" width={150} tick={{ fill: 'var(--qlab-axis)', fontSize: 11 }} />
          <Tooltip formatter={(v: number) => v.toFixed(4)} />
          <Bar dataKey="value" name="Drop in AUC" fill={color(model)} radius={[0, 4, 4, 0]} barSize={18} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

function PredictionPanel({ modelId, available }: { modelId: string; available: string[] }) {
  const [info, setInfo] = useState<QmlModelInfo | null>(null)
  const [values, setValues] = useState<Record<string, string>>({})
  const [result, setResult] = useState<QmlPrediction | null>(null)
  const [error, setError] = useState<string | null>(null)
  const exists = available.includes(modelId) || modelId.includes('_job_')

  useEffect(() => {
    setInfo(null); setResult(null); setError(null)
    if (!exists) return
    qmlApi.getModel(modelId).then(setInfo).catch(() => setError('Model metadata unavailable.'))
  }, [modelId, exists])

  const run = async () => {
    if (!info) return
    setError(null)
    try {
      const features = info.feature_names.map(f => (values[f] === undefined || values[f] === '' ? null : Number(values[f])))
      setResult(await qmlApi.predict(modelId, features))
    } catch {
      setError('Prediction failed - check that every value is a number.')
    }
  }

  return (
    <ChartFrame title="Single prediction with explanation"
      subtitle={`Model ${modelId}. Blank fields are imputed with the training median. Not a diagnostic tool.`}>
      {!exists && <p className="text-sm text-neutral-500">No saved model for this selection yet. Run the benchmark or train one.</p>}
      {info && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="grid max-h-80 grid-cols-2 gap-2 overflow-y-auto pr-2">
            {info.feature_names.map(f => (
              <label key={f} className="flex flex-col text-xs text-neutral-600 dark:text-neutral-300">
                {f}{info.selected_features.includes(f) && <span className="text-medical-600"> (used)</span>}
                <input inputMode="decimal" value={values[f] ?? ''} onChange={e => setValues(v => ({ ...v, [f]: e.target.value }))}
                  className="rounded border border-neutral-300 bg-white px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-900" />
              </label>
            ))}
          </div>
          <div className="space-y-3">
            <Button onClick={run}>Predict</Button>
            {error && <p className="text-sm text-red-600">{error}</p>}
            {result && (
              <div className="space-y-2 text-sm text-neutral-800 dark:text-neutral-100">
                <p>
                  P({result.positive_class}) = <strong>{fmt(result.probability_disease)}</strong>
                  {' '}→ {result.predicted_label === 1 ? 'positive' : 'negative'} at threshold 0.5
                </p>
                {result.explanation && (
                  <table className="w-full text-xs">
                    <thead><tr className="text-left text-neutral-500"><th>Feature</th><th>Encoded angle</th><th>SHAP</th></tr></thead>
                    <tbody>
                      {result.explanation.map(e => (
                        <tr key={e.feature}><td>{e.feature}</td><td className="tabular-nums">{fmt(e.encoded_value)}</td>
                          <td className="tabular-nums">{e.shap >= 0 ? '+' : ''}{fmt(e.shap, 4)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <p className="text-xs text-amber-700 dark:text-amber-300">{result.disclaimer}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </ChartFrame>
  )
}
