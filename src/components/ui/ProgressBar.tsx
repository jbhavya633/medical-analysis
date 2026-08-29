import { cn } from '../../utils/helpers'

interface ProgressBarProps {
  value: number
  max?: number
  showLabel?: boolean
  label?: string
  variant?: 'default' | 'medical' | 'clinical' | 'vital' | 'critical' | 'warning' | 'success'
  size?: 'sm' | 'md' | 'lg'
  className?: string
  animated?: boolean
  stripes?: boolean
}

const variantColors = {
  default: 'bg-neutral-500',
  medical: 'bg-medical-500',
  clinical: 'bg-clinical-500',
  vital: 'bg-vital-500',
  critical: 'bg-critical-500',
  warning: 'bg-warning-500',
  success: 'bg-success-500',
}

const sizeClasses = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
}

export function ProgressBar({
  value,
  max = 100,
  showLabel = false,
  label,
  variant = 'medical',
  size = 'md',
  className,
  animated = false,
  stripes = false,
}: ProgressBarProps) {
  const percentage = Math.max(0, Math.min(100, (value / max) * 100))
  const colorClass = variantColors[variant]
  const sizeClass = sizeClasses[size]

  return (
    <div className={cn('w-full', className)}>
      {(label || showLabel) && (
        <div className="flex items-center justify-between mb-1.5 text-sm">
          <span className="font-medium text-neutral-700 dark:text-neutral-300">{label || ''}</span>
          {showLabel && <span className="font-mono text-neutral-500">{percentage.toFixed(0)}%</span>}
        </div>
      )}
      <div
        className={cn(
          'relative w-full rounded-full bg-neutral-200 dark:bg-neutral-700 overflow-hidden',
          sizeClass,
          animated && 'animate-pulse'
        )}
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            colorClass,
            stripes && 'bg-gradient-to-r from-transparent via-white/30 to-transparent bg-[length:200%_100%] animate-stripes'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

interface MultiStepProgressProps {
  steps: { label: string; completed: boolean; current?: boolean; error?: boolean }[]
  className?: string
  variant?: 'default' | 'medical' | 'clinical'
  showConnectors?: boolean
}

export function MultiStepProgress({
  steps,
  className,
  variant = 'medical',
  showConnectors = true,
}: MultiStepProgressProps) {
  const colorMap = {
    default: { active: 'text-neutral-500', done: 'text-neutral-500', bg: 'bg-neutral-200' },
    medical: { active: 'text-medical-500', done: 'text-medical-500', bg: 'bg-medical-500' },
    clinical: { active: 'text-clinical-500', done: 'text-clinical-500', bg: 'bg-clinical-500' },
  }
  const colors = colorMap[variant]

  return (
    <div className={cn('flex items-center', className)}>
      {steps.map((step, index) => (
        <div key={step.label} className="flex items-center">
          <div className="relative flex items-center">
            {showConnectors && index > 0 && (
              <div
                className={cn(
                  'absolute left-0 top-1/2 -translate-y-1/2 w-full h-1',
                  step.completed ? colors.bg : 'bg-neutral-200 dark:bg-neutral-700'
                )}
                style={{ marginRight: '-50%' }}
              />
            )}
            <div
              className={cn(
                'relative z-10 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all',
                step.completed
                  ? `${colors.done} text-white`
                  : step.current
                  ? `${colors.active} bg-white dark:bg-neutral-900 ring-4 ${colors.bg}/20`
                  : 'text-neutral-400 bg-neutral-100 dark:bg-neutral-800'
              )}
            >
              {step.completed ? '✓' : step.error ? '✕' : index + 1}
            </div>
          </div>
          <div className={cn('ml-2 min-w-[80px] text-sm', step.current ? 'font-medium' : 'text-neutral-500')}>
            {step.label}
          </div>
        </div>
      ))}
    </div>
  )
}

interface CircularProgressProps {
  value: number
  max?: number
  size?: number
  strokeWidth?: number
  variant?: 'default' | 'medical' | 'clinical' | 'vital' | 'critical' | 'warning' | 'success'
  showLabel?: boolean
  label?: string
  className?: string
}

export function CircularProgress({
  value,
  max = 100,
  size = 64,
  strokeWidth = 6,
  variant = 'medical',
  showLabel = true,
  label,
  className,
}: CircularProgressProps) {
  const percentage = Math.max(0, Math.min(100, (value / max) * 100))
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - percentage / 100)

  const colorMap = {
    default: '#737373',
    medical: '#14b8a6',
    clinical: '#a855f7',
    vital: '#f59e0b',
    critical: '#ef4444',
    warning: '#f59e0b',
    success: '#22c55e',
  }

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          className="dark:stroke-neutral-700"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colorMap[variant]}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500 ease-out"
          style={{ strokeDashoffset: offset }}
        />
      </svg>
      {(showLabel || label) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showLabel && <span className="font-bold text-neutral-900 dark:text-neutral-100">{percentage.toFixed(0)}%</span>}
          {label && <span className="text-xs text-neutral-500">{label}</span>}
        </div>
      )}
    </div>
  )
}

interface TaskProgressProps {
  tasks: { id: string; name: string; status: 'pending' | 'running' | 'completed' | 'failed'; progress?: number; error?: string }[]
  onRetry?: (id: string) => void
  className?: string
}

export function TaskProgress({ tasks, onRetry, className }: TaskProgressProps) {
  const completed = tasks.filter(t => t.status === 'completed').length
  const total = tasks.length
  const overall = total > 0 ? (completed / total) * 100 : 0

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium">Overall progress</div>
          <div className="text-xs text-neutral-500">{completed} of {total} tasks completed</div>
        </div>
        <CircularProgress value={overall} size={48} strokeWidth={4} variant="medical" showLabel />
      </div>
      <div className="space-y-2">
        {tasks.map(task => (
          <div key={task.id} className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={cn(
                  'w-2 h-2 rounded-full',
                  task.status === 'completed' && 'bg-success-500',
                  task.status === 'running' && 'bg-medical-500 animate-pulse',
                  task.status === 'failed' && 'bg-critical-500',
                  task.status === 'pending' && 'bg-neutral-400'
                )} />
                <span className="font-medium text-sm">{task.name}</span>
                {task.status === 'running' && <span className="text-xs text-medical-600">Running...</span>}
                {task.status === 'completed' && <span className="text-xs text-success-600">Done</span>}
                {task.status === 'failed' && <span className="text-xs text-critical-600">Failed</span>}
                {task.status === 'pending' && <span className="text-xs text-neutral-400">Pending</span>}
              </div>
              {task.status === 'failed' && onRetry && (
                <button onClick={() => onRetry(task.id)} className="text-sm text-medical-600 hover:underline">Retry</button>
              )}
            </div>
            {task.status === 'running' && task.progress !== undefined && (
              <ProgressBar value={task.progress} size="sm" variant="medical" showLabel />
            )}
            {task.error && (
              <div className="mt-2 text-xs text-critical-600 flex items-center gap-1">
                <span>Error:</span> {task.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}