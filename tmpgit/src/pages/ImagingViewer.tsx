import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
  ZoomIn, ZoomOut, RotateCw, RotateCcw, Minimize,
  ChevronLeft, Search, Layers, Download, Info,
  Grid, FilePlus, FileText, Brain
} from 'lucide-react'
import { MOCK_PATIENTS } from '../data/mockData'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { cn, formatDate, formatRelativeTime } from '../utils/helpers'
import { ImagingStudy, ImagingSeries, ImagingInstance } from '../types'

export function ImagingViewer() {
  const { patientId } = useParams<{ patientId: string }>()
  const [searchParams] = useSearchParams()
  const [studies, setStudies] = useState<ImagingStudy[]>([])
  const [selectedStudy, setSelectedStudy] = useState<ImagingStudy | null>(null)
  const [selectedSeries, setSelectedSeries] = useState<ImagingSeries | null>(null)
  const [selectedInstance, setSelectedInstance] = useState<ImagingInstance | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [showMetadata, setShowMetadata] = useState(false)
  const [overlay, setOverlay] = useState<'none' | 'segmentation' | 'heatmap' | 'measurement'>('none')

  useEffect(() => {
    if (patientId) {
      const patient = MOCK_PATIENTS.find(p => p.id === patientId)
      if (patient) {
        setStudies(patient.imagingStudies)
        if (patient.imagingStudies.length > 0) {
          const study = patient.imagingStudies[0]
          setSelectedStudy(study)
          if (study.series.length > 0) {
            const series = study.series[0]
            setSelectedSeries(series)
            if (series.instances.length > 0) {
              setSelectedInstance(series.instances[0])
            }
          }
        }
      }
    }
  }, [patientId])

  useEffect(() => {
    const studyId = searchParams.get('study')
    const seriesId = searchParams.get('series')
    if (studyId) {
      const study = studies.find(s => s.id === studyId)
      if (study) {
        setSelectedStudy(study)
        if (seriesId) {
          const series = study.series.find(s => s.id === seriesId)
          if (series) {
            setSelectedSeries(series)
            if (series.instances.length > 0) setSelectedInstance(series.instances[0])
          }
        } else if (study.series.length > 0) {
          setSelectedSeries(study.series[0])
          setSelectedInstance(study.series[0].instances[0])
        }
      }
    }
  }, [searchParams, studies])

  // const seriesForStudy = selectedStudy?.series || []

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 lg:p-6 border-b border-neutral-200 dark:border-neutral-800">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-2xl font-bold">Imaging viewer</h2>
            <p className="text-neutral-500 text-sm">
              DICOM viewer · Multi-planar reconstruction · AI overlays · Cornerstone3D integration
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" leftIcon={<FilePlus className="h-4 w-4" />}>Upload DICOM</Button>
            <Button variant="secondary" size="sm" leftIcon={<Download className="h-4 w-4" />}>Export</Button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
            <input
              type="search"
              placeholder="Filter studies, series, modalities..."
              className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800"
            />
          </div>
          <div className="flex items-center gap-2">
            <Button variant={viewMode === 'grid' ? 'primary' : 'outline'} size="icon" onClick={() => setViewMode('grid')}>
              <Grid className="h-4 w-4" />
            </Button>
            <Button variant={viewMode === 'list' ? 'primary' : 'outline'} size="icon" onClick={() => setViewMode('list')}>
              <FileText className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={() => setShowMetadata(!showMetadata)}>
              <Info className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-72 lg:w-80 border-r border-neutral-200 dark:border-neutral-800 flex flex-col overflow-hidden">
          <div className="p-3 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
            <h3 className="font-semibold">Studies ({studies.length})</h3>
            <Badge variant="medical" size="sm">{studies.reduce((a, s) => a + s.series.length, 0)} series</Badge>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {studies.map(study => (
              <div
                key={study.id}
                onClick={() => { setSelectedStudy(study); setSelectedSeries(study.series[0] || null); setSelectedInstance(study.series[0]?.instances[0] || null) }}
                className={cn(
                  'p-3 rounded-xl cursor-pointer transition-all',
                  selectedStudy?.id === study.id
                    ? 'bg-medical-50 dark:bg-medical-900/30 border border-medical-200 dark:border-medical-800'
                    : 'hover:bg-neutral-100 dark:hover:bg-neutral-800/50'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="info" size="sm">{study.modality}</Badge>
                    <span className="text-xs text-neutral-500">{study.bodyPart}</span>
                  </div>
                  <span className="text-xs text-neutral-400">{study.series.length} series</span>
                </div>
                <div className="text-sm font-medium mt-1 truncate">{study.description}</div>
                <div className="flex items-center justify-between mt-2 text-xs text-neutral-500">
                  <span>{formatDate(study.studyDate)}</span>
                  <Badge size="sm" variant={study.status === 'completed' ? 'success' : 'warning'}>{study.status}</Badge>
                </div>
                {study.aiFindings && study.aiFindings.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {study.aiFindings.slice(0, 2).map(f => (
                      <Badge key={f.id} variant="clinical" size="sm">{f.finding}</Badge>
                    ))}
                    {study.aiFindings.length > 2 && <Badge variant="info" size="sm">+{study.aiFindings.length - 2}</Badge>}
                  </div>
                )}
              </div>
            ))}
            {studies.length === 0 && (
              <div className="text-center py-8 text-neutral-400">
                <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No imaging studies for this patient</p>
              </div>
            )}
          </div>
        </aside>

        <div className="flex-1 flex flex-col overflow-hidden relative">
          {selectedStudy && (
            <div className="h-14 border-b border-neutral-200 dark:border-neutral-800 px-4 flex items-center justify-between bg-white/50 dark:bg-neutral-900/50 backdrop-blur-sm">
              <div className="flex items-center gap-3">
                <Badge variant="info">{selectedStudy.modality}</Badge>
                <div>
                  <div className="font-medium">{selectedStudy.description}</div>
                  <div className="text-xs text-neutral-500">{selectedStudy.bodyPart} · {selectedStudy.series.length} series · {formatRelativeTime(selectedStudy.studyDate)}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {selectedStudy.aiFindings && selectedStudy.aiFindings.length > 0 && (
                  <Badge variant="clinical" className="gap-1">
                    <Brain className="h-3 w-3" />
                    {selectedStudy.aiFindings.length} AI findings
                  </Badge>
                )}
              </div>
            </div>
          )}

          {selectedSeries && (
            <div className="h-12 border-b border-neutral-200 dark:border-neutral-800 px-4 flex items-center gap-4 bg-white/50 dark:bg-neutral-900/50 backdrop-blur-sm overflow-x-auto">
              {selectedStudy?.series.map(s => (
                <button
                  key={s.id}
                  onClick={() => { setSelectedSeries(s); setSelectedInstance(s.instances[0] || null) }}
                  className={cn(
                    'flex-shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap',
                    selectedSeries.id === s.id
                      ? 'bg-medical-100 text-medical-700 dark:bg-medical-900/30 dark:text-medical-300'
                      : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                  )}
                >
                  {s.seriesNumber}. {s.modality} {s.bodyPart} ({s.instances.length} slices)
                </button>
              ))}
            </div>
          )}

          <div className="flex-1 flex relative overflow-hidden">
            {selectedInstance && selectedSeries ? (
              <>
                <div className="flex-1 flex items-center justify-center relative bg-neutral-900">
                  <div className={cn(
                    'relative transition-transform duration-100',
                    `rotate-[${rotation}deg] scale-[${zoom}]`
                  )}>
                    <div className="w-full h-full flex items-center justify-center">
                      <MockDicomDisplay
                        instance={selectedInstance}
                        series={selectedSeries}
                        overlay={overlay}
                      />
                    </div>
                  </div>

                  <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center justify-between gap-2 text-white/80 text-xs font-mono">
                    <div className="flex items-center gap-4 bg-black/50 px-3 py-2 rounded-lg backdrop-blur-sm">
                      <span>{selectedInstance.instanceNumber}/{selectedSeries.instances.length}</span>
                      <span>{selectedSeries.modality} {selectedSeries.bodyPart}</span>
                      <span>{selectedInstance.rows}×{selectedInstance.columns} · {selectedInstance.bitsAllocated}bit</span>
                    </div>
                    <div className="flex items-center gap-2 bg-black/50 px-3 py-2 rounded-lg backdrop-blur-sm">
                      <span>WL: {selectedInstance.windowCenter}</span>
                      <span>WW: {selectedInstance.windowWidth}</span>
                    </div>
                  </div>
                </div>

                <div className="absolute bottom-4 right-4 flex flex-col gap-2 z-10">
                  <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => setZoom(z => Math.min(z * 1.2, 5))} title="Zoom in">
                    <ZoomIn className="h-5 w-5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => setZoom(z => Math.max(z / 1.2, 0.2))} title="Zoom out">
                    <ZoomOut className="h-5 w-5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => setRotation(r => (r + 90) % 360)} title="Rotate CW">
                    <RotateCw className="h-5 w-5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => setRotation(r => (r - 90 + 360) % 360)} title="Rotate CCW">
                    <RotateCcw className="h-5 w-5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => { setZoom(1); setRotation(0) }} title="Reset view">
                    <Minimize className="h-5 w-5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="bg-white/90 dark:bg-neutral-800/90" onClick={() => setOverlay(o => o === 'none' ? 'segmentation' : o === 'segmentation' ? 'heatmap' : o === 'heatmap' ? 'measurement' : 'none')} title="Toggle AI overlay">
                    <Layers className="h-5 w-5" />
                  </Button>
                </div>

                <div className="absolute top-4 left-4 flex flex-col gap-2 z-10">
                  {selectedSeries.instances.length > 1 && (
                    <div className="bg-white/90 dark:bg-neutral-800/90 rounded-lg p-2 backdrop-blur-sm">
                      <input
                        type="range"
                        min={1}
                        max={selectedSeries.instances.length}
                        value={selectedInstance.instanceNumber}
                        onChange={e => {
                          const idx = Number(e.target.value) - 1
                          setSelectedInstance(selectedSeries.instances[idx])
                        }}
                        className="w-48 h-2 accent-medical-500"
                      />
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center bg-neutral-100 dark:bg-neutral-900">
                <div className="text-center text-neutral-400">
                  <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg">Select a study to view images</p>
                  <p className="text-sm mt-1">DICOM viewer with MPR, 3D reconstruction, and AI overlays</p>
                </div>
              </div>
            )}
          </div>

          {selectedInstance && selectedSeries && (
            <div className="h-20 border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 flex items-center gap-2 px-4 overflow-x-auto">
              {selectedSeries.instances.map(inst => (
                <button
                  key={inst.id}
                  onClick={() => setSelectedInstance(inst)}
                  className={cn(
                    'flex-shrink-0 w-28 h-20 rounded-lg border-2 transition-all relative overflow-hidden',
                    selectedInstance.id === inst.id
                      ? 'border-medical-500 ring-2 ring-medical-500/20'
                      : 'border-transparent hover:border-neutral-300 dark:hover:border-neutral-700'
                  )}
                >
                  <MockThumbnail instance={inst} />
                  {inst.aiAnnotations && inst.aiAnnotations.length > 0 && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-clinical-500 rounded-full" title="AI annotation" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {showMetadata && selectedInstance && (
          <div className="w-80 border-l border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 overflow-y-auto">
            <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
              <h3 className="font-semibold">DICOM metadata</h3>
              <Button variant="ghost" size="icon" onClick={() => setShowMetadata(false)}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>
            <div className="p-4 space-y-2 text-sm font-mono">
              {Object.entries(selectedInstance.metadata || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4">
                  <span className="text-neutral-500">{k}</span>
                  <span className="text-neutral-900 dark:text-neutral-100 truncate max-w-[60%]">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function MockDicomDisplay({ instance, series, overlay }: { instance: ImagingInstance; series: ImagingSeries; overlay: string }) {
  const [seed] = useState(Math.random() * 1000)

  return (
    <svg width="100%" height="100%" viewBox="0 0 512 512" style={{ maxWidth: '100%', maxHeight: '100%' }}>
      <defs>
        <radialGradient id="dicomGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#1a1a2e" />
          <stop offset="100%" stopColor="#0f0f1a" />
        </radialGradient>
        <filter id="noise">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch" result="noise" seed={seed} />
          <feColorMatrix in="noise" type="saturate" values="0" />
          <feComponentTransfer>
            <feFuncA type="table" tableValues="0 0.15" />
          </feComponentTransfer>
        </filter>
        <filter id="anatomy">
          <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" seed={seed + 100} result="anat" />
          <feColorMatrix in="anat" type="saturate" values="0" />
          <feComponentTransfer>
            <feFuncA type="table" tableValues="0 0.08" />
          </feComponentTransfer>
        </filter>
      </defs>

      <rect width="512" height="512" fill="url(#dicomGrad)" />
      <rect width="512" height="512" fill="white" opacity="0.02" filter="url(#noise)" />
      <rect width="512" height="512" fill="white" opacity="0.04" filter="url(#anatomy)" />

      {overlay === 'segmentation' && (
        <g opacity="0.35">
          <ellipse cx="256" cy="256" rx="120" ry="100" fill="#22c55e" opacity="0.4" />
          <ellipse cx="256" cy="256" rx="80" ry="65" fill="#22c55e" opacity="0.6" />
        </g>
      )}

      {overlay === 'heatmap' && (
        <g opacity="0.5">
          <defs>
            <radialGradient id="heat" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.8" />
              <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
            </radialGradient>
          </defs>
          <ellipse cx="320" cy="200" rx="60" ry="50" fill="url(#heat)" />
        </g>
      )}

      {overlay === 'measurement' && (
        <g stroke="#f59e0b" stroke-width="2" fill="none">
          <line x1="180" y1="256" x2="340" y2="256" />
          <line x1="256" y1="180" x2="256" y2="330" />
          <text x="260" y="175" fontSize="14" fill="#f59e0b" fontFamily="monospace">42.3 mm</text>
          <text x="345" y="260" fontSize="14" fill="#f59e0b" fontFamily="monospace">58.7 mm</text>
        </g>
      )}

      <g fontSize="11" fill="white" opacity="0.7" fontFamily="monospace">
        <text x="12" y="20">{series.modality} {series.bodyPart}</text>
        <text x="12" y="36">Instance {instance.instanceNumber}/{series.instances.length}</text>
        <text x="12" y="52">WL/WW: {instance.windowCenter}/{instance.windowWidth}</text>
        <text x="12" y="500" textAnchor="end">Demo DICOM · Not for diagnosis</text>
      </g>
    </svg>
  )
}

function MockThumbnail({ instance }: { instance: ImagingInstance }) {
  return (
    <svg width="100%" height="100%" viewBox="0 0 64 64">
      <rect width="64" height="64" fill="#0f0f1a" />
      <rect width="64" height="64" fill="white" opacity="0.03" filter="url(#noise)" />
      <rect width="64" height="64" fill="white" opacity="0.05" filter="url(#anatomy)" />
      <text x="32" y="36" textAnchor="middle" fontSize="7" fill="white" opacity="0.5" fontFamily="monospace">#{instance.instanceNumber}</text>
    </svg>
  )
}