import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Brain, AlertTriangle, Shield, CheckCircle, XCircle,
  Zap, Stethoscope, FileText, Search, Filter, Download,
  RefreshCw, HelpCircle, ChevronRight, Layers
} from 'lucide-react'
import { MOCK_PATIENTS } from '../data/mockData'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge, PriorityBadge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal, ConfirmDialog } from '../components/ui/Modal'
import { Tabs, TabList, TabTrigger, TabContent } from '../components/ui/Tabs'
import { Table, Column } from '../components/ui/Table'
import { Progress } from '../components/ui/Progress'
import { cn, formatRelativeTime, calculateAge } from '../utils/helpers'
import { AIInsight, RiskScore } from '../types'
import { MODELS } from '../data/mockData'

export function ClinicalDecisionSupport() {
  const { patientId } = useParams<{ patientId: string }>()
  const [activeTab, setActiveTab] = useState<'insights' | 'risks' | 'models' | 'evidence'>('insights')
  const [selectedInsight, setSelectedInsight] = useState<AIInsight | null>(null)
  const [showEvidence, setShowEvidence] = useState(false)

  const patient = patientId ? MOCK_PATIENTS.find(p => p.id === patientId) : null
  const insights = patient ? patient.aiInsights : MOCK_PATIENTS.flatMap(p => p.aiInsights.map(i => ({ ...i, patient: p })))
  const risks = patient ? patient.riskScores : MOCK_PATIENTS.flatMap(p => p.riskScores.map(r => ({ ...r, patient: p })))

  const runFusion = async () => {
    // Simulate running the multimodal fusion model
    await new Promise(r => setTimeout(r, 1500))
    // In real app, this would call the backend AI service
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Clinical decision support</h2>
          <p className="text-neutral-500 text-sm">
            Multimodal evidence fusion · Specialized models per modality · Calibrated risk scores
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>Export CDS report</Button>
          <Button leftIcon={<RefreshCw className="h-4 w-4" />} onClick={runFusion} loading={false}>
            Run fusion analysis
          </Button>
        </div>
      </div>

      {patient && (
        <div className="flex items-center gap-4 p-4 bg-neutral-50 dark:bg-neutral-900/50 rounded-xl border border-neutral-200 dark:border-neutral-800">
          <div className="w-12 h-12 rounded-xl bg-gradient-medical flex items-center justify-center">
            <Stethoscope className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold">{patient.lastName}, {patient.firstName}</div>
            <div className="text-sm text-neutral-500">{calculateAge(patient.dateOfBirth)}{patient.sex} · {patient.mrn} · {patient.conditions[0]?.display || 'No active conditions'}</div>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-500">
            <span>{insights.length} insights</span>
            <span>{risks.length} risk scores</span>
            <Badge variant="clinical" size="sm">MedFusion v2.1</Badge>
          </div>
        </div>
      )}

      <div className="flex gap-2 border-b border-neutral-200 dark:border-neutral-800">
        {[
          { id: 'insights', label: 'AI insights', icon: Brain, count: insights.length },
          { id: 'risks', label: 'Risk scores', icon: Shield, count: risks.length },
          { id: 'models', label: 'Model registry', icon: Layers, count: MODELS.length },
          { id: 'evidence', label: 'Evidence graph', icon: FileText, count: 0 },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-1.5',
              activeTab === t.id
                ? 'text-medical-600 border-medical-500'
                : 'text-neutral-500 hover:text-neutral-700 border-transparent'
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
            {t.count > 0 && <Badge size="sm" variant="medical">{t.count}</Badge>}
          </button>
        ))}
      </div>

      {activeTab === 'insights' && (
        <div className="space-y-4">
          {insights.length === 0 ? (
            <Card className="p-12 text-center">
              <Brain className="h-16 w-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" />
              <h3 className="text-lg font-medium mb-2">No AI insights generated</h3>
              <p className="text-neutral-500 mb-4">Click "Run fusion analysis" to trigger the multimodal evidence fusion layer.</p>
              <Button leftIcon={<Zap className="h-4 w-4" />} onClick={runFusion}>Generate insights</Button>
            </Card>
          ) : (
            insights.map(insight => (
              <Card key={insight.id} className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={cn('p-2.5 rounded-xl flex-shrink-0', insight.priority === 'critical' ? 'bg-critical-100 text-critical-600' : insight.priority === 'high' ? 'bg-warning-100 text-warning-600' : 'bg-clinical-100 text-clinical-600')}>
                        <Brain className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-medium truncate">{insight.title}</h3>
                          <PriorityBadge priority={insight.priority} size="sm" />
                          <Badge variant="clinical" size="sm">{insight.type}</Badge>
                          <span className="text-xs text-neutral-500 ml-auto">{formatRelativeTime(insight.createdAt)}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <div className="text-right">
                          <div className="text-sm font-medium">{Math.round(insight.confidence * 100)}% confidence</div>
                          <Progress value={insight.confidence * 100} max={100} className="w-32 h-1.5" showLabel={false} />
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-neutral-600 dark:text-neutral-400 mb-3">{insight.summary}</div>
                    {insight.recommendations.length > 0 && (
                      <div className="space-y-1 mb-3">
                        {insight.recommendations.map((r, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-medical-700 dark:text-medical-300">
                            <CheckCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                            {r}
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center gap-3 text-xs text-neutral-500">
                      <span>Status: <span className={cn('font-medium capitalize', insight.status === 'new' ? 'text-critical-600' : insight.status === 'reviewed' ? 'text-medical-600' : 'text-neutral-500')}>{insight.status}</span></span>
                      <span>Model: {insight.modelId}</span>
                      <span>Evidence sources: {insight.evidence.length}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 flex-shrink-0">
                    <Button size="sm" variant="outline" onClick={() => setSelectedInsight(insight)}>Review</Button>
                    <Button size="sm" variant="ghost" onClick={() => setShowEvidence(true)} leftIcon={<Layers className="h-3.5 w-3.5" />}>Evidence</Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === 'risks' && (
        <div className="space-y-4">
          {risks.length === 0 ? (
            <Card className="p-12 text-center">
              <Shield className="h-16 w-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" />
              <h3 className="text-lg font-medium mb-2">No risk scores calculated</h3>
              <p className="text-neutral-500">Risk models require sufficient clinical data. Ensure labs, vitals, and diagnoses are current.</p>
            </Card>
          ) : (
            risks.map(risk => (
              <Card key={risk.id} className="p-5">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={cn('p-2.5 rounded-xl flex-shrink-0', getRiskColor(risk.score))}>
                        <Shield className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="font-medium">{risk.name}</h3>
                        <div className="text-sm text-neutral-500">{risk.category} · {risk.modelId}</div>
                      </div>
                      <div className="flex items-center gap-3 ml-auto">
                        <div className="text-right">
                          <div className="text-2xl font-bold">{Math.round(risk.score * 100)}%</div>
                          <div className="text-xs text-neutral-500">Risk probability</div>
                        </div>
                        <Progress value={risk.score * 100} max={100} className="w-40 h-2.5" showLabel={false} color={getRiskColor(risk.score).replace('bg-', '').replace('-500', '-600')} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
                        <div className="text-neutral-500">Percentile</div>
                        <div className="font-mono font-medium">{risk.percentile}th</div>
                      </div>
                      <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
                        <div className="text-neutral-500">Threshold</div>
                        <div className="font-mono font-medium">{Math.round(risk.threshold * 100)}%</div>
                      </div>
                      <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
                        <div className="text-neutral-500">Time horizon</div>
                        <div className="font-mono font-medium">{risk.timeHorizon}</div>
                      </div>
                      <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
                        <div className="text-neutral-500">Updated</div>
                        <div className="font-mono font-medium">{formatRelativeTime(risk.computedAt)}</div>
                      </div>
                    </div>
                    <details className="mt-3">
                      <summary className="text-sm text-medical-600 cursor-pointer">Contributing factors ({risk.factors.length})</summary>
                      <ul className="mt-2 space-y-1 text-xs text-neutral-500">
                        {risk.factors.map((f, i) => (
                          <li key={i} className="flex items-center gap-2">
                            <span className={cn('w-2 h-2 rounded', f.direction === 'increases' ? 'bg-critical-500' : 'bg-medical-500')} />
                            {f.factor} ({f.direction})
                          </li>
                        ))}
                      </ul>
                    </details>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === 'models' && (
        <Card className="p-5">
          <div className="space-y-4">
            {MODELS.map(model => (
              <div key={model.id} className="flex items-center justify-between p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                <div className="flex items-center gap-4">
                  <div className={cn('p-3 rounded-xl', model.modality === 'ecg' ? 'bg-critical-100 text-critical-600' : model.modality === 'imaging' ? 'bg-medical-100 text-medical-600' : 'bg-clinical-100 text-clinical-600')}>
                    {model.modality === 'ecg' && <Zap className="h-6 w-6" />}
                    {model.modality === 'imaging' && <Layers className="h-6 w-6" />}
                    {model.modality === 'clinical' && <Brain className="h-6 w-6" />}
                  </div>
                  <div>
                    <div className="font-medium">{model.name}</div>
                    <div className="text-sm text-neutral-500">{model.task} · {model.dataset} · {model.modality}</div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-neutral-400">
                      <span>Architecture: {model.architecture}</span>
                      <span>Params: {model.parameters}</span>
                      <span>Version: {model.version}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <Badge variant={model.status === 'deployed' ? 'success' : 'clinical'}>{model.status}</Badge>
                  <div className="text-right text-sm">
                    <div className="font-mono text-neutral-600 dark:text-neutral-400">
                      {model.metrics.auc ? `AUC ${model.metrics.auc}` : model.metrics.dice ? `Dice ${model.metrics.dice}` : model.metrics.mae ? `MAE ${model.metrics.mae}` : `Prec ${model.metrics.precision}`}
                    </div>
                    <div className="text-xs text-neutral-500">{model.metrics.sensitivity ? `Sens ${model.metrics.sensitivity}` : ''} {model.metrics.specificity ? `Spec ${model.metrics.specificity}` : ''}</div>
                  </div>
                  <Button size="sm" variant="outline">View details</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'evidence' && (
        <Card className="p-5">
          <CardHeader className="mb-4">
            <CardTitle>Evidence graph</CardTitle>
            <CardDescription>How each insight connects to source modalities (ECG, imaging, labs, notes)</CardDescription>
          </CardHeader>
          <div className="h-96 flex items-center justify-center bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
            <div className="text-center text-neutral-400">
              <Layers className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Evidence graph visualization</p>
              <p className="text-sm mt-2">Interactive D3 force-directed graph showing insight ↔ modality edges with weight</p>
              <p className="text-xs mt-4">Requires backend graph service (Neo4j / NetworkX)</p>
            </div>
          </div>
        </Card>
      )}

      <Modal isOpen={!!selectedInsight} onClose={() => setSelectedInsight(null)} title="Insight review" size="lg">
        {selectedInsight && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
              <div className={cn('p-3 rounded-xl', selectedInsight.priority === 'critical' ? 'bg-critical-100 text-critical-600' : 'bg-clinical-100 text-clinical-600')}>
                <Brain className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-medium">{selectedInsight.title}</h3>
                <div className="flex items-center gap-2 text-sm text-neutral-500 mt-1">
                  <PriorityBadge priority={selectedInsight.priority} size="sm" />
                  <Badge variant="clinical" size="sm">{selectedInsight.type}</Badge>
                  <span>Confidence: {Math.round(selectedInsight.confidence * 100)}%</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Summary</h4>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">{selectedInsight.summary}</p>
            </div>
            {selectedInsight.recommendations.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {selectedInsight.recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-medical-700 dark:text-medical-300">
                      <CheckCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {selectedInsight.evidence.length > 0 && (
              <details className="border-t border-neutral-200 dark:border-neutral-800 pt-4">
                <summary className="font-medium cursor-pointer">Evidence sources ({selectedInsight.evidence.length})</summary>
                <ul className="mt-3 space-y-2 text-sm">
                  {selectedInsight.evidence.map(e => (
                    <li key={e.sourceId} className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
                      <div className="flex items-center gap-3">
                        <Badge variant={e.modality === 'ecg' ? 'critical' : e.modality === 'imaging' ? 'medical' : 'vital'} size="sm">{e.modality}</Badge>
                        <div>
                          <div className="font-mono text-xs">{e.sourceId}</div>
                          <div className="text-xs text-neutral-500">{e.finding}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono">Weight: {e.weight}</div>
                        <div className="text-xs text-neutral-500">{e.timestamp}</div>
                      </div>
                    </li>
                  ))}
                </ul>
              </details>
            )}
            <div className="flex justify-end gap-2 border-t border-neutral-200 dark:border-neutral-800 pt-4">
              <Button variant="outline" onClick={() => setSelectedInsight(null)}>Close</Button>
              <Button onClick={() => { /* mark reviewed */ setSelectedInsight(null) }}>Mark reviewed</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

function getRiskColor(score: number) {
  if (score >= 0.7) return 'bg-critical-100 text-critical-600'
  if (score >= 0.4) return 'bg-warning-100 text-warning-600'
  if (score >= 0.2) return 'bg-vital-100 text-vital-600'
  return 'bg-success-100 text-success-600'
}