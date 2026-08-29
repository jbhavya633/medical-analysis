import { cn } from '../../utils/helpers'

interface LoadingScreenProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
  fullScreen?: boolean
  className?: string
}

export function LoadingScreen({ message = 'Loading...', size = 'md', fullScreen = false, className }: LoadingScreenProps) {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-10 w-10',
    lg: 'h-14 w-14',
  }

  const containerClasses = fullScreen
    ? 'fixed inset-0 z-50 flex items-center justify-center bg-white/80 dark:bg-neutral-950/80 backdrop-blur-sm'
    : 'flex items-center justify-center'

  return (
    <div className={cn(containerClasses, className)} role="status" aria-live="polite" aria-label={message}>
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="relative">
          <svg className={cn(sizeClasses[size], 'text-medical-500 animate-spin')} viewBox="0 0 100 100" preserveAspectRatio="xMidYMid">
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeDasharray="200, 100"
              strokeLinecap="round"
              className="opacity-25"
            />
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeDasharray="120, 200"
              strokeLinecap="round"
              className="animate-spin"
              style={{ transformOrigin: 'center', transform: 'rotate(-90deg)' }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className={cn(
              'rounded-full bg-gradient-medical animate-pulse',
              size === 'sm' && 'h-3 w-3',
              size === 'md' && 'h-4 w-4',
              size === 'lg' && 'h-5 w-5'
            )} />
          </div>
        </div>
        {message && (
          <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">{message}</p>
        )}
      </div>
    </div>
  )
}

interface SkeletonProps {
  variant?: 'text' | 'title' | 'avatar' | 'card' | 'table-row' | 'chart' | 'image'
  className?: string
  width?: string | number
  height?: string | number
  count?: number
}

export function Skeleton({ variant = 'text', className, width, height, count = 1 }: SkeletonProps) {
  const variants = {
    text: 'h-4 w-full',
    title: 'h-6 w-3/4',
    avatar: 'h-10 w-10 rounded-full',
    card: 'h-48 rounded-xl',
    'table-row': 'h-12',
    chart: 'h-64 rounded-xl',
    image: 'aspect-video rounded-xl',
  }

  const baseClass = 'animate-pulse bg-neutral-200 dark:bg-neutral-800 rounded'

  const items = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      className={cn(baseClass, variants[variant], className)}
      style={{ width, height }}
    />
  ))

  if (count === 1) return items[0]
  return <div className={cn('space-y-3', className)}>{items}</div>
}

interface ProgressProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'medical' | 'clinical' | 'vital' | 'critical'
  showLabel?: boolean
  label?: string
  className?: string
}

export function Progress({ value, max = 100, size = 'md', variant = 'default', showLabel = false, label, className }: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  }

  const variantClasses = {
    default: 'bg-medical-500',
    medical: 'bg-gradient-medical',
    clinical: 'bg-gradient-clinical',
    vital: 'bg-gradient-vital',
    critical: 'bg-gradient-critical',
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between mb-1.5">
        {label && <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">{label}</span>}
        {showLabel && <span className="text-sm font-mono text-neutral-500 dark:text-neutral-400">{Math.round(percentage)}%</span>}
      </div>
      <div className={cn('relative overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800', sizeClasses[size])}>
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            variantClasses[variant]
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  )
}

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  variant?: 'default' | 'medical' | 'clinical' | 'vital' | 'critical'
  className?: string
}

export function Spinner({ size = 'md', variant = 'default', className }: SpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  }

  const variantClasses = {
    default: 'text-medical-500',
    medical: 'text-medical-500',
    clinical: 'text-clinical-500',
    vital: 'text-vital-500',
    critical: 'text-critical-500',
  }

  return (
    <svg
      className={cn(sizeClasses[size], variantClasses[variant], 'animate-spin', className)}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  )
}