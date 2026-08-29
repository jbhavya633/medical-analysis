import { forwardRef, HTMLAttributes } from 'react'
import { cn } from '../../utils/helpers'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'medical' | 'clinical' | 'vital' | 'critical' | 'success' | 'warning' | 'info' | 'neutral'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
  dotColor?: string
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', dot, dotColor, children, ...props }, ref) => {
    const variantClasses = {
      default: 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200',
      medical: 'bg-medical-100 text-medical-800 dark:bg-medical-900/30 dark:text-medical-200',
      clinical: 'bg-clinical-100 text-clinical-800 dark:bg-clinical-900/30 dark:text-clinical-200',
      vital: 'bg-vital-100 text-vital-800 dark:bg-vital-900/30 dark:text-vital-200',
      critical: 'bg-critical-100 text-critical-800 dark:bg-critical-900/30 dark:text-critical-200',
      success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200',
      warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200',
      info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200',
      neutral: 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200',
    }

    const sizeClasses = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-0.5 text-xs',
      lg: 'px-3 py-1 text-sm',
    }

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full font-medium',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', dotColor ? '' : 'bg-current')}
            style={dotColor ? { backgroundColor: dotColor } : undefined}
          />
        )}
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

export interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'pending' | 'completed' | 'cancelled' | 'error' | 'warning' | 'success'
  size?: 'sm' | 'md' | 'lg'
  showDot?: boolean
}

export const StatusBadge = ({ status, size = 'md', showDot = true }: StatusBadgeProps) => {
  const statusConfig: Record<string, { variant: BadgeProps['variant']; label: string; dotColor?: string }> = {
    active: { variant: 'medical', label: 'Active', dotColor: '#14b8a6' },
    inactive: { variant: 'neutral', label: 'Inactive', dotColor: '#737373' },
    pending: { variant: 'warning', label: 'Pending', dotColor: '#f59e0b' },
    completed: { variant: 'success', label: 'Completed', dotColor: '#22c55e' },
    cancelled: { variant: 'neutral', label: 'Cancelled', dotColor: '#737373' },
    error: { variant: 'critical', label: 'Error', dotColor: '#ef4444' },
    warning: { variant: 'warning', label: 'Warning', dotColor: '#f59e0b' },
    success: { variant: 'success', label: 'Success', dotColor: '#22c55e' },
  }

  const config = statusConfig[status] || { variant: 'default', label: status, dotColor: undefined }

  return (
    <Badge variant={config.variant} size={size} dot={showDot} dotColor={config.dotColor}>
      {config.label}
    </Badge>
  )
}

export interface PriorityBadgeProps {
  priority: 'low' | 'medium' | 'high' | 'critical'
  size?: 'sm' | 'md' | 'lg'
}

export const PriorityBadge = ({ priority, size = 'md' }: PriorityBadgeProps) => {
  const priorityConfig: Record<string, { variant: BadgeProps['variant']; label: string; icon: React.ReactNode }> = {
    low: { variant: 'info', label: 'Low', icon: '▼' },
    medium: { variant: 'warning', label: 'Medium', icon: '●' },
    high: { variant: 'vital', label: 'High', icon: '▲' },
    critical: { variant: 'critical', label: 'Critical', icon: '◆' },
  }

  const config = priorityConfig[priority]

  return (
    <Badge variant={config.variant} size={size}>
      <span className="flex items-center gap-1">
        <span className="text-xs">{config.icon}</span>
        {config.label}
      </span>
    </Badge>
  )
}

export interface InterpretationBadgeProps {
  interpretation: 'normal' | 'abnormal' | 'critical' | 'low' | 'high'
  size?: 'sm' | 'md' | 'lg'
}

export const InterpretationBadge = ({ interpretation, size = 'md' }: InterpretationBadgeProps) => {
  const interpretationConfig: Record<string, { variant: BadgeProps['variant']; label: string }> = {
    normal: { variant: 'success', label: 'Normal' },
    abnormal: { variant: 'warning', label: 'Abnormal' },
    critical: { variant: 'critical', label: 'Critical' },
    low: { variant: 'info', label: 'Low' },
    high: { variant: 'warning', label: 'High' },
  }

  const config = interpretationConfig[interpretation]

  return <Badge variant={config.variant} size={size}>{config.label}</Badge>
}