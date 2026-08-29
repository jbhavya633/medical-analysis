import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow, parseISO, isValid, differenceInYears, differenceInDays, differenceInHours, differenceInMinutes } from 'date-fns'
import { Patient, LabResult, VitalSigns, RiskScore, AIInsight } from '../types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date, pattern = 'MMM d, yyyy'): string {
  const d = typeof date === 'string' ? parseISO(date) : date
  if (!isValid(d)) return 'Invalid date'
  return format(d, pattern)
}

export function formatDateTime(date: string | Date, pattern = 'MMM d, yyyy h:mm a'): string {
  const d = typeof date === 'string' ? parseISO(date) : date
  if (!isValid(d)) return 'Invalid date'
  return format(d, pattern)
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseISO(date) : date
  if (!isValid(d)) return 'Unknown'
  return formatDistanceToNow(d, { addSuffix: true })
}

export function formatTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseISO(date) : date
  if (!isValid(d)) return 'Invalid time'
  return format(d, 'h:mm a')
}

export function calculateAge(dateOfBirth: string): number {
  const dob = parseISO(dateOfBirth)
  if (!isValid(dob)) return 0
  return differenceInYears(new Date(), dob)
}

export function calculateAgePrecise(dateOfBirth: string): { years: number; months: number; days: number } {
  const dob = parseISO(dateOfBirth)
  if (!isValid(dob)) return { years: 0, months: 0, days: 0 }

  const now = new Date()
  let years = differenceInYears(now, dob)
  const anniversary = new Date(dob)
  anniversary.setFullYear(now.getFullYear())
  if (anniversary > now) years--

  const anniversaryThisYear = new Date(dob)
  anniversaryThisYear.setFullYear(now.getFullYear())
  if (anniversaryThisYear > now) {
    anniversaryThisYear.setFullYear(now.getFullYear() - 1)
  }

  let months = 0
  let tempDate = new Date(anniversaryThisYear)
  while (tempDate <= now) {
    tempDate.setMonth(tempDate.getMonth() + 1)
    if (tempDate <= now) months++
  }

  const lastMonth = new Date(anniversaryThisYear)
  lastMonth.setMonth(lastMonth.getMonth() + months)
  const days = differenceInDays(now, lastMonth)

  return { years, months, days }
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length - 3) + '...'
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function debounce<T extends (...args: unknown[]) => unknown>(fn: T, delay: number): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

export function throttle<T extends (...args: unknown[]) => unknown>(fn: T, limit: number): (...args: Parameters<T>) => void {
  let inThrottle = false
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

export function parseNumber(value: string | number): number {
  if (typeof value === 'number') return value
  const parsed = parseFloat(value)
  return isNaN(parsed) ? 0 : parsed
}

export function roundTo(value: number, decimals: number): number {
  const factor = Math.pow(10, decimals)
  return Math.round(value * factor) / factor
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

export function lerp(start: number, end: number, factor: number): number {
  return start + (end - start) * factor
}

export function getInterpretationClass(interpretation: LabResult['interpretation']): string {
  switch (interpretation) {
    case 'critical': return 'badge-critical'
    case 'abnormal': return 'badge-warning'
    case 'high': return 'badge-warning'
    case 'low': return 'badge-info'
    case 'normal':
    default: return 'badge-success'
  }
}

export function getInterpretationLabel(interpretation: LabResult['interpretation']): string {
  switch (interpretation) {
    case 'critical': return 'Critical'
    case 'abnormal': return 'Abnormal'
    case 'high': return 'High'
    case 'low': return 'Low'
    case 'normal':
    default: return 'Normal'
  }
}

export function getVitalSignsStatus(vital: VitalSigns, type: keyof VitalSigns): { value: number | undefined; status: 'normal' | 'warning' | 'critical' } {
  const value = vital[type] as number | undefined
  if (value === undefined) return { value: undefined, status: 'normal' }

  const thresholds: Record<string, { warning: [number, number]; critical: [number, number] }> = {
    temperature: { warning: [37.5, 38.5], critical: [39, 41] },
    heartRate: { warning: [100, 50], critical: [130, 40] },
    respiratoryRate: { warning: [24, 10], critical: [30, 8] },
    bloodPressureSystolic: { warning: [140, 90], critical: [180, 70] },
    bloodPressureDiastolic: { warning: [90, 60], critical: [120, 50] },
    oxygenSaturation: { warning: [92, 90], critical: [88, 85] },
  }

  const threshold = thresholds[type]
  if (!threshold) return { value, status: 'normal' }

  const [warningHigh, warningLow] = threshold.warning
  const [criticalHigh, criticalLow] = threshold.critical

  if (value >= criticalHigh || value <= criticalLow) return { value, status: 'critical' }
  if (value >= warningHigh || value <= warningLow) return { value, status: 'warning' }
  return { value, status: 'normal' }
}

export function getRiskScoreClass(category: RiskScore['category']): string {
  switch (category) {
    case 'very-high': return 'badge-critical'
    case 'high': return 'badge-warning'
    case 'moderate': return 'badge-info'
    case 'low':
    default: return 'badge-success'
  }
}

export function getAIInsightPriorityClass(priority: AIInsight['priority']): string {
  switch (priority) {
    case 'critical': return 'border-l-4 border-l-critical-500 bg-critical-50 dark:bg-critical-900/20'
    case 'high': return 'border-l-4 border-l-vital-500 bg-vital-50 dark:bg-vital-900/20'
    case 'medium': return 'border-l-4 border-l-blue-500 bg-blue-50 dark:bg-blue-900/20'
    case 'low':
    default: return 'border-l-4 border-l-neutral-400 bg-neutral-50 dark:bg-neutral-800/50'
  }
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`
}

export function getModalityColor(modality: string): string {
  const colors: Record<string, string> = {
    CT: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200',
    MR: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200',
    XRAY: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200',
    US: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200',
    PET: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-200',
    PT: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-200',
    NM: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-200',
    MG: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-200',
    DX: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200',
    CR: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200',
    ECG: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
    RTSTRUCT: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200',
    RTDOSE: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200',
    RTPLAN: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200',
    SEG: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-200',
  }
  return colors[modality.toUpperCase()] || 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200'
}

export function getModalityIcon(modality: string): string {
  const icons: Record<string, string> = {
    CT: '📦',
    MR: '🧠',
    XRAY: '🩻',
    US: '🔊',
    PET: '⚛️',
    PT: '⚛️',
    NM: '☢️',
    MG: '🩻',
    DX: '🩻',
    CR: '🩻',
    ECG: '💓',
    RTSTRUCT: '🎯',
    RTDOSE: '☢️',
    RTPLAN: '📋',
    SEG: '🔍',
  }
  return icons[modality.toUpperCase()] || '📄'
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function retry<T>(fn: () => Promise<T>, attempts = 3, delay = 1000): Promise<T> {
  return fn().catch(err => {
    if (attempts <= 1) throw err
    return sleep(delay).then(() => retry(fn, attempts - 1, delay * 2))
  })
}

export function groupBy<T>(array: T[], key: keyof T | ((item: T) => string)): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const groupKey = typeof key === 'function' ? key(item) : String(item[key])
    if (!groups[groupKey]) groups[groupKey] = []
    groups[groupKey].push(item)
    return groups
  }, {} as Record<string, T[]>)
}

export function sortBy<T>(array: T[], key: keyof T | ((item: T) => unknown), order: 'asc' | 'desc' = 'asc'): T[] {
  return [...array].sort((a, b) => {
    const aVal = typeof key === 'function' ? key(a) : a[key]
    const bVal = typeof key === 'function' ? key(b) : b[key]
    if (aVal < bVal) return order === 'asc' ? -1 : 1
    if (aVal > bVal) return order === 'asc' ? 1 : -1
    return 0
  })
}

export function uniqueBy<T>(array: T[], key: keyof T | ((item: T) => unknown)): T[] {
  const seen = new Set()
  return array.filter(item => {
    const val = typeof key === 'function' ? key(item) : item[key]
    if (seen.has(val)) return false
    seen.add(val)
    return true
  })
}

export function chunk<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = []
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size))
  }
  return chunks
}

export function omit<T extends Record<string, unknown>, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> {
  const result = { ...obj }
  keys.forEach(key => delete result[key])
  return result
}

export function pick<T extends Record<string, unknown>, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
  const result = {} as Pick<T, K>
  keys.forEach(key => { if (key in obj) result[key] = obj[key] })
  return result
}

export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

export function isEmpty(obj: unknown): boolean {
  if (obj == null) return true
  if (Array.isArray(obj)) return obj.length === 0
  if (typeof obj === 'object') return Object.keys(obj).length === 0
  return false
}

export function getContrastColor(hexColor: string): string {
  const hex = hexColor.replace('#', '')
  const r = parseInt(hex.substr(0, 2), 16)
  const g = parseInt(hex.substr(2, 2), 16)
  const b = parseInt(hex.substr(4, 2), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#000000' : '#ffffff'
}

export function hslToHex(h: number, s: number, l: number): string {
  s /= 100
  l /= 100
  const k = (n: number) => (n + h / 30) % 12
  const a = s * Math.min(l, 1 - l)
  const f = (n: number) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)))
  const toHex = (x: number) => Math.round(255 * x).toString(16).padStart(2, '0')
  return `#${toHex(f(0))}${toHex(f(8))}${toHex(f(4))}`
}

export function hexToHsl(hex: string): { h: number; s: number; l: number } {
  const cleanHex = hex.replace('#', '')
  const r = parseInt(cleanHex.substr(0, 2), 16) / 255
  const g = parseInt(cleanHex.substr(2, 2), 16) / 255
  const b = parseInt(cleanHex.substr(4, 2), 16) / 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h = 0
  let s = 0
  const l = (max + min) / 2

  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break
      case g: h = (b - r) / d + 2; break
      case b: h = (r - g) / d + 4; break
    }
    h /= 6
  }

  return { h: h * 360, s: s * 100, l: l * 100 }
}

export function generateColorPalette(baseColor: string, count: number): string[] {
  const { h, s, l } = hexToHsl(baseColor)
  const colors: string[] = []

  for (let i = 0; i < count; i++) {
    const newH = (h + (360 / count) * i) % 360
    colors.push(hslToHex(newH, s, l))
  }

  return colors
}