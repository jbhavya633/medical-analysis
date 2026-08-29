import { useState, useEffect } from 'react'
import {
  User, Bell, Shield, Palette, Database, Bot, Plug,
  Download, Check, X, Plus, Key, Eye, EyeOff, Lock,
  Globe, Wifi, Server, RefreshCw, Save, Trash2,
  AlertTriangle, Brain, Zap, Scan, Calendar
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { Tabs, TabList, TabTrigger, TabContent } from '../components/ui/Tabs'
import { Switch } from '../components/ui/Switch'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../hooks/useAuth'
import { DATASETS, MODELS } from '../data/mockData'
import { cn } from '../utils/helpers'

export function Settings() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('profile')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Settings</h2>
          <p className="text-neutral-500 text-sm">Manage your workspace, integrations, and MedFusion preferences</p>
        </div>
        <Button onClick={handleSave} leftIcon={<Save className="h-4 w-4" />}>
          {saved ? <Check className="h-4 w-4" /> : null}
          {saved ? 'Saved' : 'Save changes'}
        </Button>
      </div>

      <div className="flex gap-2 border-b border-neutral-200 dark:border-neutral-800">
        {[
          { id: 'profile', label: 'Profile', icon: User },
          { id: 'appearance', label: 'Appearance', icon: Palette },
          { id: 'notifications', label: 'Notifications', icon: Bell },
          { id: 'security', label: 'Security', icon: Shield },
          { id: 'datasets', label: 'Datasets', icon: Database },
          { id: 'integrations', label: 'Integrations', icon: Plug },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-1.5',
              activeTab === t.id
                ? 'text-medical-600 border-medical-500'
                : 'text-neutral-500 hover:text-neutral-700 border-transparent'
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'profile' && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>User profile</CardTitle>
            <CardDescription>Personal and professional details</CardDescription>
          </CardHeader>
          <div className="space-y-4 mt-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-clinical flex items-center justify-center text-white text-xl font-bold">
                {user?.name?.split(' ').map(n => n[0]).join('')}
              </div>
              <Button variant="outline" size="sm">Change avatar</Button>
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input label="Full name" defaultValue={user?.name} />
              <Input label="Email" type="email" defaultValue={user?.email} />
              <Input label="Role" defaultValue={user?.role} disabled />
              <Input label="Department" defaultValue="Cardiology" />
              <Input label="Institution" defaultValue="MedFusion Demo Hospital" />
              <Input label="NPI" defaultValue="1234567890" />
            </div>
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-sm font-medium mb-2">Permissions</div>
              <div className="flex flex-wrap gap-2">
                {['read:patients', 'write:notes', 'run:ai', 'view:imaging', 'admin:datasets'].map(p => (
                  <Badge key={p} variant="medical" size="sm">{p}</Badge>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {activeTab === 'appearance' && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Theme and display preferences</CardDescription>
          </CardHeader>
          <div className="space-y-6 mt-4">
            <div>
              <div className="text-sm font-medium mb-2">Theme mode</div>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'light', label: 'Light', icon: '☀️' },
                  { value: 'dark', label: 'Dark', icon: '🌙' },
                  { value: 'system', label: 'System', icon: '💻' },
                ].map(t => (
                  <button
                    key={t.value}
                    onClick={() => setTheme(t.value as any)}
                    className={cn(
                      'p-4 rounded-xl border-2 transition-all text-center',
                      theme === t.value
                        ? 'border-medical-500 bg-medical-50 dark:bg-medical-900/30'
                        : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300'
                    )}
                  >
                    <div className="text-2xl mb-1">{t.icon}</div>
                    <div className="text-sm font-medium">{t.label}</div>
                  </button>
                ))}
              </div>
              <p className="text-xs text-neutral-500 mt-2">Current: <span className="capitalize">{resolvedTheme}</span></p>
            </div>
            <div className="space-y-3">
              {[
                { label: 'Compact density', desc: 'Use tighter spacing throughout the UI' },
                { label: 'High contrast', desc: 'Increase contrast for accessibility' },
                { label: 'Animations', desc: 'Enable smooth transitions and effects' },
                { label: 'Reduce motion', desc: 'Minimize non-essential animations' },
              ].map(s => (
                <div key={s.label} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                  <div>
                    <div className="font-medium">{s.label}</div>
                    <div className="text-xs text-neutral-500">{s.desc}</div>
                  </div>
                  <Switch defaultChecked={s.label !== 'Reduce motion'} />
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {activeTab === 'notifications' && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>Choose what alerts you receive</CardDescription>
          </CardHeader>
          <div className="space-y-3 mt-4">
            {[
              { icon: AlertTriangle, title: 'Critical lab alerts', desc: 'Immediately notify on critical lab results', default: true },
              { icon: Brain, title: 'AI insight notifications', desc: 'New AI insights from fusion layer', default: true },
              { icon: Zap, title: 'ECG rhythm alerts', desc: 'Abnormal ECG rhythms detected by model', default: true },
              { icon: Scan, title: 'Imaging findings', desc: 'Radiology AI findings available', default: false },
              { icon: Calendar, title: 'Patient updates', desc: 'Care team notes and orders', default: false },
              { icon: Globe, title: 'Dataset updates', desc: 'New dataset versions available', default: true },
            ].map(n => (
              <div key={n.title} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800">
                    <n.icon className="h-5 w-5 text-medical-500" />
                  </div>
                  <div>
                    <div className="font-medium">{n.title}</div>
                    <div className="text-xs text-neutral-500">{n.desc}</div>
                  </div>
                </div>
                <Switch defaultChecked={n.default} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'security' && (
        <div className="space-y-6">
          <Card className="p-6">
            <CardHeader>
              <CardTitle>Password & authentication</CardTitle>
              <CardDescription>Update credentials and 2FA</CardDescription>
            </CardHeader>
            <div className="space-y-4 mt-4">
              <Input label="Current password" type="password" placeholder="••••••••" leftIcon={<Lock className="h-4 w-4" />} />
              <Input label="New password" type="password" placeholder="••••••••" leftIcon={<Lock className="h-4 w-4" />} />
              <Input label="Confirm new password" type="password" placeholder="••••••••" leftIcon={<Lock className="h-4 w-4" />} />
            </div>
          </Card>
          <Card className="p-6">
            <CardHeader>
              <CardTitle>Active sessions</CardTitle>
              <CardDescription>Devices currently logged in</CardDescription>
            </CardHeader>
            <div className="space-y-3 mt-4">
              {[
                { device: 'Chrome · Windows', location: 'Boston, MA', current: true, time: 'now' },
                { device: 'Safari · iPhone', location: 'Boston, MA', current: false, time: '3h ago' },
                { device: 'Firefox · Linux', location: 'Unknown', current: false, time: '2d ago' },
              ].map((s, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800">
                      <Server className="h-5 w-5 text-neutral-500" />
                    </div>
                    <div>
                      <div className="font-medium">{s.device} {s.current && <Badge variant="success" size="sm">This device</Badge>}</div>
                      <div className="text-xs text-neutral-500">{s.location} · {s.time}</div>
                    </div>
                  </div>
                  {!s.current && <Button variant="ghost" size="sm" className="text-critical-600">Revoke</Button>}
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-6">
            <CardHeader>
              <CardTitle>API keys</CardTitle>
              <CardDescription>Programmatic access to MedFusion API</CardDescription>
            </CardHeader>
            <div className="space-y-3 mt-4">
              {[
                { name: 'ml-train-pipeline', created: '2024-01-15', lastUsed: '2h ago' },
                { name: 'dashboard-ingest', created: '2024-03-22', lastUsed: '1d ago' },
              ].map(k => (
                <div key={k.name} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800">
                      <Key className="h-5 w-5 text-warning-500" />
                    </div>
                    <div>
                      <div className="font-mono font-medium">{k.name}</div>
                      <div className="text-xs text-neutral-500">Created {k.created} · Used {k.lastUsed}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm">Reveal</Button>
                    <Button variant="ghost" size="sm" className="text-critical-600"><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
              ))}
              <Button variant="outline" leftIcon={<Plus className="h-4 w-4" />}>Generate new key</Button>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'datasets' && (
        <div className="space-y-6">
          <Card className="p-6">
            <CardHeader>
              <CardTitle>Dataset registry</CardTitle>
              <CardDescription>MIMIC-IV family, PTB-XL, CheXpert Plus, AutoPET, ADNI, EchoNet</CardDescription>
            </CardHeader>
            <div className="space-y-3 mt-4">
              {DATASETS.map(d => (
                <div key={d.id} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                  <div className="flex items-center gap-3">
                    <div className={cn('p-2 rounded-lg', getDatasetColor(d.status))}>
                      <Database className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="font-medium">{d.name}</div>
                      <div className="text-xs text-neutral-500">{d.role}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={d.status === 'ready' ? 'success' : d.status === 'download' ? 'medical' : 'warning'} size="sm">
                      {d.status}
                    </Badge>
                    {d.status === 'download' && (
                      <Button variant="outline" size="sm" leftIcon={<Download className="h-3.5 w-3.5" />}>Download</Button>
                    )}
                    {d.status === 'credentialed' && (
                      <Badge variant="warning" size="sm" leftIcon={<Lock className="h-3 w-3" />}>Locked</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'integrations' && (
        <div className="space-y-6">
          <Card className="p-6">
            <CardHeader>
              <CardTitle>Model registry</CardTitle>
              <CardDescription>Specialized models across modalities</CardDescription>
            </CardHeader>
            <div className="grid sm:grid-cols-2 gap-3 mt-4">
              {MODELS.map(m => (
                <div key={m.id} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                  <div>
                    <div className="font-medium">{m.name}</div>
                    <div className="text-xs text-neutral-500">{m.task} · {m.dataset}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={m.status === 'deployed' ? 'success' : 'clinical'} size="sm">{m.status}</Badge>
                    <Switch defaultChecked={m.status === 'deployed'} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-6">
            <CardHeader>
              <CardTitle>External connections</CardTitle>
              <CardDescription>EHR, PACS, lab, and FHIR endpoints</CardDescription>
            </CardHeader>
            <div className="space-y-3 mt-4">
              {[
                { name: 'Epic FHIR R4', status: 'connected', desc: 'Production EHR interface' },
                { name: 'MIMIC-IV Demo', status: 'connected', desc: 'De-identified research DB' },
                { name: 'DICOM PACS', status: 'disconnected', desc: 'Imaging studies stream' },
                { name: 'Lab LIS', status: 'connected', desc: 'Real-time lab events' },
                { name: 'WebSocket stream', status: 'connected', desc: 'Realtime AI insights' },
              ].map(c => (
                <div key={c.name} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                  <div className="flex items-center gap-3">
                    <div className={cn('p-2 rounded-lg', c.status === 'connected' ? 'bg-success-100 text-success-600' : 'bg-neutral-100 text-neutral-500')}>
                      {c.status === 'connected' ? <Wifi className="h-5 w-5" /> : <Plug className="h-5 w-5" />}
                    </div>
                    <div>
                      <div className="font-medium">{c.name}</div>
                      <div className="text-xs text-neutral-500">{c.desc}</div>
                    </div>
                  </div>
                  <Badge variant={c.status === 'connected' ? 'success' : 'warning'} size="sm" leftIcon={c.status === 'connected' ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}>
                    {c.status}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

function getDatasetColor(status: string) {
  switch (status) {
    case 'ready': return 'bg-success-100 text-success-600'
    case 'download': return 'bg-medical-100 text-medical-600'
    case 'credentialed': return 'bg-warning-100 text-warning-600'
    default: return 'bg-neutral-100 text-neutral-500'
  }
}