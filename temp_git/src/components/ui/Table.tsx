import { HTMLAttributes, useMemo } from 'react'
import { cn } from '../../utils/helpers'
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'

export interface Column<T> {
  key: string
  header: string
  accessor: keyof T | ((row: T) => React.ReactNode)
  width?: string
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  render?: (value: unknown, row: T) => React.ReactNode
  className?: string
  headerClassName?: string
}

export interface TableProps<T> extends HTMLAttributes<HTMLTableElement> {
  data: T[]
  columns: Column<T>[]
  keyExtractor: (row: T) => string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (key: string, order: 'asc' | 'desc') => void
  onRowClick?: (row: T) => void
  selectable?: boolean
  selectedKeys?: Set<string>
  onSelectionChange?: (keys: Set<string>) => void
  loading?: boolean
  emptyMessage?: string
  stickyHeader?: boolean
  rowClassName?: (row: T) => string
}

export function Table<T>({
  data,
  columns,
  keyExtractor,
  sortBy,
  sortOrder,
  onSort,
  onRowClick,
  selectable = false,
  selectedKeys = new Set(),
  onSelectionChange,
  loading = false,
  emptyMessage = 'No data available',
  stickyHeader = true,
  rowClassName,
  className,
  ...props
}: TableProps<T>) {
  const handleSort = (key: string) => {
    if (!onSort) return
    const newOrder = sortBy === key && sortOrder === 'asc' ? 'desc' : 'asc'
    onSort(key, newOrder)
  }

  const handleSelectAll = (checked: boolean) => {
    if (!onSelectionChange) return
    if (checked) {
      const newKeys = new Set(data.map(keyExtractor))
      onSelectionChange(newKeys)
    } else {
      onSelectionChange(new Set())
    }
  }

  const handleSelectRow = (key: string, checked: boolean) => {
    if (!onSelectionChange) return
    const newKeys = new Set(selectedKeys)
    if (checked) {
      newKeys.add(key)
    } else {
      newKeys.delete(key)
    }
    onSelectionChange(newKeys)
  }

  if (loading) {
    return (
      <div className="overflow-x-auto rounded-xl border border-neutral-200 dark:border-neutral-800">
        <table className="w-full" role="grid" aria-busy="true">
          <thead className="bg-neutral-50 dark:bg-neutral-900">
            <tr>
              {selectable && <th className="px-4 py-3 w-12" />}
              {columns.map(column => (
                <th
                  key={column.key}
                  className={cn(
                    'px-4 py-3 text-left font-semibold text-neutral-600 dark:text-neutral-400 border-b border-neutral-200 dark:border-neutral-800',
                    column.headerClassName
                  )}
                  style={{ width: column.width }}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="animate-pulse">
                {selectable && <td className="px-4 py-3 w-12" />}
                {columns.map(column => (
                  <td key={column.key} className="px-4 py-3">
                    <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded" style={{ width: '60%' }} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="overflow-x-auto rounded-xl border border-neutral-200 dark:border-neutral-800">
        <table className="w-full" role="grid">
          <thead className="bg-neutral-50 dark:bg-neutral-900">
            <tr>
              {selectable && <th className="px-4 py-3 w-12" />}
              {columns.map(column => (
                <th
                  key={column.key}
                  className={cn(
                    'px-4 py-3 text-left font-semibold text-neutral-600 dark:text-neutral-400 border-b border-neutral-200 dark:border-neutral-800',
                    column.headerClassName
                  )}
                  style={{ width: column.width }}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={columns.length + (selectable ? 1 : 0)} className="px-4 py-12 text-center text-neutral-500 dark:text-neutral-400">
                {emptyMessage}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className={cn('overflow-x-auto rounded-xl border border-neutral-200 dark:border-neutral-800', className)}>
      <table className="w-full" role="grid" {...props}>
        <thead className={cn('bg-neutral-50 dark:bg-neutral-900', stickyHeader && 'sticky top-0 z-10')}>
          <tr>
            {selectable && (
              <th className="px-4 py-3 w-12">
                <input
                  type="checkbox"
                  checked={selectedKeys.size === data.length && data.length > 0}
                  onChange={e => handleSelectAll(e.target.checked)}
                  className="h-4 w-4 rounded border-neutral-300 text-medical-600 focus:ring-2 focus:ring-medical-500/20"
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map(column => (
              <th
                key={column.key}
                className={cn(
                  'px-4 py-3 text-left font-semibold text-neutral-600 dark:text-neutral-400 border-b border-neutral-200 dark:border-neutral-800',
                  column.sortable && 'cursor-pointer select-none hover:bg-neutral-100 dark:hover:bg-neutral-800',
                  column.align === 'center' && 'text-center',
                  column.align === 'right' && 'text-right',
                  column.headerClassName
                )}
                style={{ width: column.width }}
                onClick={column.sortable ? () => handleSort(column.key) : undefined}
                aria-sort={sortBy === column.key ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                <div className="flex items-center gap-1.5">
                  {column.header}
                  {column.sortable && (
                    <span className="flex flex-col -space-y-1">
                      {sortBy === column.key && sortOrder === 'asc' ? (
                        <ChevronUp className="h-3 w-3 text-medical-500" />
                      ) : (
                        <ChevronUp className="h-3 w-3 text-neutral-300 dark:text-neutral-600" />
                      )}
                      {sortBy === column.key && sortOrder === 'desc' ? (
                        <ChevronDown className="h-3 w-3 text-medical-500" />
                      ) : (
                        <ChevronDown className="h-3 w-3 text-neutral-300 dark:text-neutral-600" />
                      )}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
          {data.map(row => {
            const key = keyExtractor(row)
            const isSelected = selectedKeys.has(key)
            return (
              <tr
                key={key}
                className={cn(
                  'transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-neutral-50 dark:hover:bg-neutral-800/50',
                  isSelected && 'bg-medical-50 dark:bg-medical-900/20',
                  rowClassName?.(row)
                )}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {selectable && (
                  <td className="px-4 py-3 w-12">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={e => { e.stopPropagation(); handleSelectRow(key, e.target.checked) }}
                      className="h-4 w-4 rounded border-neutral-300 text-medical-600 focus:ring-2 focus:ring-medical-500/20"
                      aria-label={`Select row ${key}`}
                    />
                  </td>
                )}
                {columns.map(column => {
                  const value = typeof column.accessor === 'function'
                    ? column.accessor(row)
                    : row[column.accessor as keyof T]
                  return (
                    <td
                      key={column.key}
                      className={cn(
                        'px-4 py-3 text-sm text-neutral-900 dark:text-neutral-100',
                        column.align === 'center' && 'text-center',
                        column.align === 'right' && 'text-right',
                        column.className
                      )}
                    >
                      {column.render ? column.render(value, row) : (value as React.ReactNode)}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
  pageSizeOptions?: number[]
  showPageSizeSelector?: boolean
  className?: string
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50, 100],
  showPageSizeSelector = true,
  className,
}: PaginationProps) {
  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)

  const pages = useMemo(() => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    const pages: (number | 'ellipsis')[] = [1]

    if (currentPage > 3) {
      pages.push('ellipsis')
    }

    const start = Math.max(2, currentPage - 1)
    const end = Math.min(totalPages - 1, currentPage + 1)

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    if (currentPage < totalPages - 2) {
      pages.push('ellipsis')
    }

    pages.push(totalPages)

    return pages
  }, [currentPage, totalPages])

  return (
    <div className={cn('flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-neutral-200 dark:border-neutral-800', className)}>
      <div className="text-sm text-neutral-600 dark:text-neutral-400">
        Showing <span className="font-medium">{startItem}</span> to{' '}
        <span className="font-medium">{endItem}</span> of{' '}
        <span className="font-medium">{totalItems}</span> results
      </div>

      <div className="flex items-center gap-2">
        {showPageSizeSelector && onPageSizeChange && (
          <select
            value={pageSize}
            onChange={e => onPageSizeChange(Number(e.target.value))}
            className="px-3 py-1.5 text-sm border border-neutral-300 rounded-lg bg-white dark:bg-neutral-800 dark:border-neutral-600 focus:ring-2 focus:ring-medical-500/20"
            aria-label="Page size"
          >
            {pageSizeOptions.map(size => (
              <option key={size} value={size}>{size} per page</option>
            ))}
          </select>
        )}

        <nav className="flex items-center gap-1" aria-label="Pagination">
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
            className="p-2 rounded-lg text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="First page"
            aria-disabled={currentPage === 1}
          >
            <ChevronsUpDown className="h-4 w-4 rotate-180" />
          </button>

          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="p-2 rounded-lg text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Previous page"
            aria-disabled={currentPage === 1}
          >
            <ChevronUp className="h-4 w-4" />
          </button>

          <div className="flex items-center gap-1 mx-1">
            {pages.map((page, i) =>
              page === 'ellipsis' ? (
                <span key={`ellipsis-${i}`} className="px-2 text-neutral-400">...</span>
              ) : (
                <button
                  key={page}
                  onClick={() => onPageChange(page)}
                  className={cn(
                    'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                    currentPage === page
                      ? 'bg-medical-500 text-white'
                      : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                  )}
                  aria-label={`Page ${page}`}
                  aria-current={currentPage === page ? 'page' : undefined}
                >
                  {page}
                </button>
              )
            )}
          </div>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Next page"
            aria-disabled={currentPage === totalPages}
          >
            <ChevronDown className="h-4 w-4" />
          </button>

          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Last page"
            aria-disabled={currentPage === totalPages}
          >
            <ChevronsUpDown className="h-4 w-4" />
          </button>
        </nav>
      </div>
    </div>
  )
}