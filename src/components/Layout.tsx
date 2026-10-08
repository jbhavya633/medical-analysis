import { useState } from 'react'
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Scan, FlaskConical, Stethoscope, Activity,
  Bot, Settings, LogOut, Moon, Sun, Monitor, Bell, Search, Menu, X,
  ChevronLeft, Heart, Wifi, WifiOff, Loader2, CheckCircle, Atom
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocket } from '../contexts/WebSocketContext'
import { cn, getInitials } from '../utils/helpers'
import { ProgressBar } from '../components/ui/ProgressBar'

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/patients', icon: Users, label: 'Patients' },
  { to: '/imaging', icon: Scan, label: 'Imaging' },
  { to: '/labs', icon: FlaskConical, label: 'Lab Analytics' },
  { to: '/cds', icon: Stethoscope, label: 'Clinical DS' },
  { to: '/ecg', icon: Activity, label: 'ECG Analyzer' },
  { to: '/ai-assistant', icon: Bot, label: 'AI Assistant' },
  { to: '/quantum-lab', icon: Atom, label: 'Quantum Lab' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function Layout() {
  const { user, logout } = useAuth()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const { isConnected } = useWebSocket()
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [notificationsOpen, setNotificationsOpen] = useState(false)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/patients?q=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
    }
  }

  const pageTitle = NAV_ITEMS.find(item =>
    item.end ? location.pathname === item.to : location.pathname.startsWith(item.to)
  )?.label || 'MedFusion AI'

  return (
    <div className="flex h-full bg-neutral-50 dark:bg-neutral-950">
      {mobileOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}

      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50 flex flex-col bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-800 transition-all duration-300',
          sidebarCollapsed ? 'w-[72px]' : 'w-64',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className={cn('flex items-center h-16 px-4 border-b border-neutral-200 dark:border-neutral-800', sidebarCollapsed && 'justify-center')}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-medical flex items-center justify-center shadow-medical">
              <Heart className="h-5 w-5 text-white" />
            </div>
            {!sidebarCollapsed && (
              <div className="min-w-0">
                <div className="font-bold text-neutral-900 dark:text-neutral-50 truncate">MedFusion</div>
                <div className="text-[10px] uppercase tracking-wider text-medical-600 dark:text-medical-400 font-semibold">AI Platform</div>
              </div>
            )}
          </div>
          <button
            className="ml-auto lg:hidden p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                cn(
                  'relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  sidebarCollapsed && 'justify-center px-0',
                  isActive
                    ? 'bg-medical-50 text-medical-700 dark:bg-medical-900/30 dark:text-medical-300'
                    : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100'
                )
              }
              title={sidebarCollapsed ? item.label : undefined}
            >
              {({ isActive }) => (
                <>
                  {isActive && !sidebarCollapsed && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-medical-500 rounded-r-lg" />
                  )}
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-neutral-200 dark:border-neutral-800">
          <button
            onClick={() => setSidebarCollapsed(c => !c)}
            className={cn(
              'hidden lg:flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors',
              sidebarCollapsed && 'justify-center px-0'
            )}
          >
            <ChevronLeft className={cn('h-4 w-4 transition-transform', sidebarCollapsed && 'rotate-180')} />
            {!sidebarCollapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 flex-shrink-0 flex items-center gap-4 px-4 lg:px-6 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-xl border-b border-neutral-200 dark:border-neutral-800">
          <button
            className="lg:hidden p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>

          <h1 className="hidden sm:block text-lg font-semibold text-neutral-900 dark:text-neutral-50 truncate">
            {pageTitle}
          </h1>

          <form onSubmit={handleSearch} className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
              <input
                type="search"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search patients, studies, labs..."
                className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:border-medical-500 focus:ring-2 focus:ring-medical-500/20"
              />
            </div>
          </form>

          <div className="flex items-center gap-1 ml-auto">
            <div
              className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs"
              title={isConnected ? 'Realtime connected' : 'Realtime disconnected'}
            >
              {isConnected ? (
                <Wifi className="h-3.5 w-3.5 text-medical-500" />
              ) : (
                <WifiOff className="h-3.5 w-3.5 text-neutral-400" />
              )}
            </div>

            <button
              onClick={() => setTheme(theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light')}
              className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-500"
              title={`Theme: ${theme}`}
            >
              {theme === 'system' ? <Monitor className="h-4 w-4" /> : resolvedTheme === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </button>

            <div className="relative">
              <button
                onClick={() => setNotificationsOpen(o => !o)}
                className="relative p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-500"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-critical-500 rounded-full" />
              </button>
              {notificationsOpen && (
                <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 shadow-xl z-50 overflow-hidden">
                  <div className="px-4 py-3 border-b border-neutral-200 dark:border-neutral-800 font-semibold text-sm">Notifications</div>
                  <div className="max-h-80 overflow-y-auto">
                    {[
                      { t: 'Critical lab', m: 'K+ 6.2 mmol/L — Patient 10012853', c: 'critical' },
                      { t: 'AI finding', m: 'Possible pneumothorax on CXR study 5123', c: 'warning' },
                      { t: 'ECG alert', m: 'Atrial fibrillation detected — PTB-XL 00456', c: 'info' },
                    ].map((n, i) => (
                      <div key={i} className="px-4 py-3 border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                        <div className="text-sm font-medium">{n.t}</div>
                        <div className="text-xs text-neutral-500 mt-0.5">{n.m}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="h-6 w-px bg-neutral-200 dark:bg-neutral-700 mx-1" />

            <div className="flex items-center gap-2 pl-1">
              <div className="w-8 h-8 rounded-full bg-gradient-clinical flex items-center justify-center text-white text-xs font-semibold">
                {user ? getInitials(user.name) : 'DR'}
              </div>
              <div className="hidden md:block min-w-0">
                <div className="text-sm font-medium truncate">{user?.name}</div>
                <div className="text-[11px] text-neutral-500 capitalize">{user?.role}</div>
              </div>
              <button
                onClick={() => logout()}
                className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-500"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="sticky top-0 z-10 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-xl border-b border-neutral-200 dark:border-neutral-800 px-4 py-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-neutral-500">Build progress</span>
                <ProgressBar value={72} size="sm" variant="medical" className="w-32" />
                <span className="text-xs font-mono text-neutral-400">72%</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-neutral-400">
                <CheckCircle className="h-3.5 w-3.5 text-success-500" />
                <span>Frontend · UI · Auth</span>
                <Loader2 className="h-3.5 w-3.5 text-medical-500 animate-spin" />
                <span>Supabase · ML</span>
              </div>
            </div>
          </div>
          {!location.pathname.startsWith('/quantum-lab') && <div
            role="note"
            className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs font-medium text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200"
          >
            Demo data: patients, studies and results shown here are synthetic and are not real patients. Not a diagnostic tool.
          </div>}
          <Outlet />
        </main>
      </div>
    </div>
  )
}
