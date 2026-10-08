import * as React from 'react'
import { cn } from '../../utils/helpers'

interface TabsContextValue {
  value: string
  onValueChange: (value: string) => void
  variant: 'default' | 'medical' | 'clinical' | 'pills'
  orientation: 'horizontal' | 'vertical'
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

function useTabsContext() {
  const context = React.useContext(TabsContext)
  if (!context) {
    throw new Error('Tabs components must be used within Tabs')
  }
  return context
}

interface TabsProps {
  defaultValue: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'medical' | 'clinical' | 'pills'
  orientation?: 'horizontal' | 'vertical'
}

export function Tabs({ defaultValue, onValueChange, children, className, variant = 'default', orientation = 'horizontal' }: TabsProps) {
  const [value, setValue] = React.useState(defaultValue)

  const handleValueChange = (newValue: string) => {
    setValue(newValue)
    onValueChange?.(newValue)
  }

  const variantClasses = {
    default: 'border-b border-neutral-200 dark:border-neutral-800',
    medical: 'border-b border-medical-200 dark:border-medical-800',
    clinical: 'border-b border-clinical-200 dark:border-clinical-800',
    pills: '',
  }

  const contextValue: TabsContextValue = {
    value,
    onValueChange: handleValueChange,
    variant,
    orientation,
  }

  return (
    <TabsContext.Provider value={contextValue}>
      <div className={cn(variantClasses[variant], className)} data-orientation={orientation}>
        <TabsList>
          {React.Children.map(children, child => {
            if (React.isValidElement(child) && child.type === TabsList) {
              return React.cloneElement(child)
            }
            return child
          })}
        </TabsList>
        <div className="mt-4">
          {React.Children.map(children, child => {
            if (React.isValidElement(child) && child.type === TabContent) {
              return React.cloneElement(child)
            }
            return child
          })}
        </div>
      </div>
    </TabsContext.Provider>
  )
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
}

export function TabsList({ children, className }: TabsListProps) {
  const { variant, orientation } = useTabsContext()

  const baseClasses = orientation === 'horizontal'
    ? 'flex gap-1'
    : 'flex flex-col gap-1'

  const variantClasses = {
    default: '',
    medical: '',
    clinical: '',
    pills: '',
  }

  return (
    <div
      role="tablist"
      aria-orientation={orientation}
      className={cn(baseClasses, variantClasses[variant], className)}
    >
      {children}
    </div>
  )
}

interface TabTriggerProps {
  value: string
  children: React.ReactNode
  className?: string
  disabled?: boolean
}

export function TabTrigger({ value, children, className, disabled }: TabTriggerProps) {
  const { value: currentValue, onValueChange, variant, orientation } = useTabsContext()
  const isActive = currentValue === value

  const triggerVariantClasses = {
    default: 'border-b-2 border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300 dark:hover:text-neutral-300 dark:hover:border-neutral-600 data-[state=active]:text-medical-600 data-[state=active]:border-medical-500',
    medical: 'border-b-2 border-transparent text-neutral-500 hover:text-medical-600 hover:border-medical-300 dark:hover:text-medical-400 dark:hover:border-medical-700 data-[state=active]:text-medical-600 data-[state=active]:border-medical-500',
    clinical: 'border-b-2 border-transparent text-neutral-500 hover:text-clinical-600 hover:border-clinical-300 dark:hover:text-clinical-400 dark:hover:border-clinical-700 data-[state=active]:text-clinical-600 data-[state=active]:border-clinical-500',
    pills: 'rounded-lg bg-transparent text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800 data-[state=active]:bg-medical-100 data-[state=active]:text-medical-600 dark:data-[state=active]:bg-medical-900/30 dark:data-[state=active]:text-medical-400',
  }

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`panel-${value}`}
      id={`tab-${value}`}
      data-state={isActive ? 'active' : 'inactive'}
      onClick={() => !disabled && onValueChange(value)}
      disabled={disabled}
      className={cn(
        'px-4 py-2 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-medical-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap',
        triggerVariantClasses[variant],
        orientation === 'vertical' && 'justify-start',
        className
      )}
    >
      {children}
    </button>
  )
}

interface TabContentProps {
  value: string
  children: React.ReactNode
  className?: string
  forceMount?: boolean
}

export function TabContent({ value, children, className, forceMount = false }: TabContentProps) {
  const { value: currentValue } = useTabsContext()
  const isActive = currentValue === value

  if (!isActive && !forceMount) {
    return null
  }

  return (
    <div
      role="tabpanel"
      id={`panel-${value}`}
      aria-labelledby={`tab-${value}`}
      className={cn('mt-4 animate-fade-in', className)}
      hidden={!isActive && !forceMount}
    >
      {children}
    </div>
  )
}

Tabs.List = TabsList
Tabs.Trigger = TabTrigger
Tabs.Content = TabContent