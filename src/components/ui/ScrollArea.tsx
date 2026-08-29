import { forwardRef, useImperativeHandle, useRef, HTMLAttributes } from 'react'
import { cn } from '../../utils/helpers'

interface ScrollAreaProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
  scrollbars?: 'auto' | 'always' | 'never' | 'hover'
}

export interface ScrollAreaHandle {
  scrollTo: (options?: ScrollToOptions | number, y?: number) => void
  scrollToTop: () => void
  scrollToLeft: () => void
  readonly scrollTop: number
  readonly scrollLeft: number
}

export const ScrollArea = forwardRef<ScrollAreaHandle, ScrollAreaProps>(
  ({ className, scrollbars = 'auto', children, ...props }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null)
    const contentRef = useRef<HTMLDivElement>(null)

    useImperativeHandle(ref, () => ({
      scrollTo: (options?: ScrollToOptions | number, y?: number) => {
        if (typeof options === 'number') {
          containerRef.current?.scrollTo(options, y ?? 0)
        } else {
          containerRef.current?.scrollTo(options)
        }
      },
      scrollToTop: () => {
        containerRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
      },
      scrollToLeft: () => {
        containerRef.current?.scrollTo({ left: 0, behavior: 'smooth' })
      },
      get scrollTop() {
        return containerRef.current?.scrollTop ?? 0
      },
      get scrollLeft() {
        return containerRef.current?.scrollLeft ?? 0
      },
    }))

    const scrollbarClasses = {
      auto: 'scrollbar-auto',
      always: 'scrollbar-always',
      never: 'scrollbar-hidden',
      hover: 'scrollbar-hover',
    }

    return (
      <div
        ref={containerRef}
        className={cn(
          'relative overflow-auto',
          scrollbarClasses[scrollbars],
          className
        )}
        {...props}
      >
        <div ref={contentRef} className="min-w-fit min-h-fit">
          {children}
        </div>
      </div>
    )
  }
)

ScrollArea.displayName = 'ScrollArea'

export interface ScrollAreaScrollbarProps extends HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical'
  className?: string
}

export const ScrollAreaScrollbar = forwardRef<HTMLDivElement, ScrollAreaScrollbarProps>(
  ({ className, orientation = 'vertical', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex touch-none select-none transition-opacity',
          orientation === 'vertical' ? 'h-full w-2.5' : 'h-2.5 w-full',
          className
        )}
        {...props}
      >
        <div className={cn(
          'relative rounded-full bg-neutral-300/50 dark:bg-neutral-700/50 transition-all',
          orientation === 'vertical' ? 'w-full' : 'h-full'
        )} />
      </div>
    )
  }
)

ScrollAreaScrollbar.displayName = 'ScrollAreaScrollbar'