import { forwardRef, InputHTMLAttributes, TextareaHTMLAttributes, SelectHTMLAttributes } from 'react'
import { cn } from '../../utils/helpers'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, leftIcon, rightIcon, id, ...props }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
    const errorId = `${inputId}-error`
    const hintId = `${inputId}-hint`

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-neutral-400">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full rounded-lg border bg-white px-4 py-2.5 text-sm placeholder:text-neutral-400 transition-all duration-200',
              'focus:ring-2 focus:ring-medical-500/20',
              leftIcon ? 'pl-10' : '',
              rightIcon ? 'pr-10' : '',
              error
                ? 'border-critical-500 focus:border-critical-500 focus:ring-critical-500/20'
                : 'border-neutral-300 focus:border-medical-500 dark:border-neutral-600 dark:bg-neutral-800 dark:focus:border-medical-400',
              className
            )}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? errorId : hint ? hintId : undefined}
            {...props}
          />
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-neutral-400">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-critical-600 dark:text-critical-400" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-neutral-500 dark:text-neutral-400">
            {hint}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`
    const errorId = `${inputId}-error`
    const hintId = `${inputId}-hint`

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            'w-full rounded-lg border bg-white px-4 py-2.5 text-sm placeholder:text-neutral-400 transition-all duration-200 resize-y min-h-[100px]',
            'focus:ring-2 focus:ring-medical-500/20',
            error
              ? 'border-critical-500 focus:border-critical-500 focus:ring-critical-500/20'
              : 'border-neutral-300 focus:border-medical-500 dark:border-neutral-600 dark:bg-neutral-800 dark:focus:border-medical-400',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          {...props}
        />
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-critical-600 dark:text-critical-400" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-neutral-500 dark:text-neutral-400">
            {hint}
          </p>
        )}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  hint?: string
  options: { value: string; label: string; disabled?: boolean }[]
  placeholder?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, hint, options, placeholder, id, ...props }, ref) => {
    const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`
    const errorId = `${selectId}-error`
    const hintId = `${selectId}-hint`

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={selectId} className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(
            'w-full rounded-lg border bg-white px-4 py-2.5 text-sm transition-all duration-200 appearance-none',
            'focus:ring-2 focus:ring-medical-500/20',
            'bg-[url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 20 20\'%3E%3Cpath stroke=\'%236b7280\' stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'1.5\' d=\'M6 8l4 4 4-4\'/%3E%3C/svg%3E")] bg-[length:1.5rem_1.5rem] bg-[right_0.5rem_center] bg-no-repeat pr-10',
            error
              ? 'border-critical-500 focus:border-critical-500 focus:ring-critical-500/20'
              : 'border-neutral-300 focus:border-medical-500 dark:border-neutral-600 dark:bg-neutral-800 dark:focus:border-medical-400',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map(option => (
            <option key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-critical-600 dark:text-critical-400" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-neutral-500 dark:text-neutral-400">
            {hint}
          </p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

export interface CheckboxProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  description?: string
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, id, ...props }, ref) => {
    const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`

    return (
      <div className="flex items-start gap-3">
        <input
          ref={ref}
          type="checkbox"
          id={checkboxId}
          className={cn(
            'mt-0.5 h-4 w-4 rounded border-neutral-300 text-medical-600 focus:ring-2 focus:ring-medical-500/20',
            'disabled:opacity-50 disabled:pointer-events-none',
            className
          )}
          {...props}
        />
        <div className="flex flex-col">
          <label htmlFor={checkboxId} className="text-sm font-medium text-neutral-900 dark:text-neutral-100 cursor-pointer">
            {label}
          </label>
          {description && (
            <p className="text-sm text-neutral-500 dark:text-neutral-400">{description}</p>
          )}
        </div>
      </div>
    )
  }
)

Checkbox.displayName = 'Checkbox'

export interface RadioGroupProps {
  label: string
  options: { value: string; label: string; description?: string; disabled?: boolean }[]
  value: string
  onChange: (value: string) => void
  error?: string
  hint?: string
  orientation?: 'horizontal' | 'vertical'
}

export function RadioGroup({ label, options, value, onChange, error, hint, orientation = 'vertical' }: RadioGroupProps) {
  const groupId = `radiogroup-${Math.random().toString(36).substr(2, 9)}`
  const errorId = `${groupId}-error`
  const hintId = `${groupId}-hint`

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
        {label}
      </label>
      <div
        role="radiogroup"
        aria-labelledby={`${groupId}-label`}
        aria-describedby={error ? errorId : hint ? hintId : undefined}
        className={cn('space-y-2', orientation === 'horizontal' && 'flex flex-wrap gap-4')}
      >
        {options.map(option => (
          <label
            key={option.value}
            className={cn(
              'flex items-center gap-3 cursor-pointer transition-colors',
              orientation === 'horizontal' ? 'whitespace-nowrap' : ''
            )}
          >
            <input
              type="radio"
              name={groupId}
              value={option.value}
              checked={value === option.value}
              onChange={() => !option.disabled && onChange(option.value)}
              disabled={option.disabled}
              className="h-4 w-4 text-medical-600 border-neutral-300 focus:ring-2 focus:ring-medical-500/20 disabled:opacity-50"
            />
            <div>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{option.label}</span>
              {option.description && (
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{option.description}</p>
              )}
            </div>
          </label>
        ))}
      </div>
      {error && (
        <p id={errorId} className="mt-1.5 text-sm text-critical-600 dark:text-critical-400" role="alert">
          {error}
        </p>
      )}
      {hint && !error && (
        <p id={hintId} className="mt-1.5 text-sm text-neutral-500 dark:text-neutral-400">
          {hint}
        </p>
      )}
    </div>
  )
}