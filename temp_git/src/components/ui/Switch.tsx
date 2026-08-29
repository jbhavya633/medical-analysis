import { cn } from '../../utils/helpers'
import { forwardRef, InputHTMLAttributes } from 'react'

interface SwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
}

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(
  ({ label, description, size = 'md', className, id, ...props }, ref) => {
    const switchId = id || `switch-${Math.random().toString(36).substr(2, 9)}`
    const descriptionId = description ? `${switchId}-description` : undefined

    const sizeClasses = {
      sm: 'w-8 h-4',
      md: 'w-11 h-6',
      lg: 'w-14 h-7',
    }

    const thumbSizeClasses = {
      sm: 'w-3 h-3',
      md: 'w-5 h-5',
      lg: 'w-6 h-6',
    }

    return (
      <label className={cn('flex items-start gap-3 cursor-pointer', className)}>
        <div className="relative flex items-center">
          <input
            type="checkbox"
            role="switch"
            id={switchId}
            ref={ref}
            className="peer h-0 w-0 appearance-none"
            aria-describedby={descriptionId}
            {...props}
          />
          <div
            className={cn(
              'relative rounded-full border-2 transition-all duration-200 ease-in-out',
              'border-neutral-300 dark:border-neutral-600',
              'peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-medical-500 peer-focus-visible:ring-offset-2',
              'peer-checked:border-medical-500 peer-checked:bg-medical-500',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              sizeClasses[size]
            )}
            aria-hidden="true"
          >
            <div
              className={cn(
                'rounded-full bg-white shadow-lg transition-transform duration-200 ease-in-out',
                'peer-checked:translate-x-full',
                thumbSizeClasses[size]
              )}
              aria-hidden="true"
            />
          </div>
        </div>
        {(label || description) && (
          <div className="pt-1">
            {label && <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{label}</span>}
            {description && (
              <p id={descriptionId} className="text-xs text-neutral-500 mt-0.5">{description}</p>
            )}
          </div>
        )}
      </label>
    )
  }
)

Switch.displayName = 'Switch'