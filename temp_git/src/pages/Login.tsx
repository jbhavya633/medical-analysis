import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart, Lock, Mail, AlertCircle } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Checkbox } from '../components/ui/Input'

export function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('demo@medfusion.ai')
  const [password, setPassword] = useState('demo123')
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password, remember)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-full grid lg:grid-cols-2">
      <div className="hidden lg:flex relative overflow-hidden bg-neutral-950 text-white flex-col justify-between p-12">
        <div className="absolute inset-0 bg-gradient-to-br from-medical-700/40 via-neutral-950 to-clinical-800/30" />
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-medical-500/20 blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[28rem] h-[28rem] rounded-full bg-clinical-500/20 blur-3xl" />
        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-medical flex items-center justify-center">
              <Heart className="h-6 w-6" />
            </div>
            <div>
              <div className="text-xl font-bold">MedFusion AI</div>
              <div className="text-xs uppercase tracking-widest text-medical-300">Multimodal Clinical Platform</div>
            </div>
          </div>
        </div>
        <div className="relative z-10 space-y-8 max-w-lg">
          <h1 className="text-4xl font-bold leading-tight text-balance">
            Fuse EHR, imaging, ECG and labs into one evidence graph.
          </h1>
          <p className="text-neutral-300 text-lg">
            Built around MIMIC-IV, PTB-XL, CheXpert Plus, AutoPET and EchoNet — specialized models per modality, fused only when evidence actually coexists.
          </p>
          <div className="grid grid-cols-3 gap-4">
            {[
              { k: '800k+', v: 'ECGs (MIMIC-IV-ECG)' },
              { k: '223k', v: 'CXR–report pairs' },
              { k: '10k', v: 'Echo videos' },
            ].map(s => (
              <div key={s.k} className="rounded-xl bg-white/5 border border-white/10 p-4">
                <div className="text-2xl font-bold text-medical-300">{s.k}</div>
                <div className="text-xs text-neutral-400 mt-1">{s.v}</div>
              </div>
            ))}
          </div>
        </div>
        <p className="relative z-10 text-xs text-neutral-500">
          Research / educational use. Not a medical device. De-identified demo data only.
        </p>
      </div>

      <div className="flex items-center justify-center p-8 bg-neutral-50 dark:bg-neutral-950">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-medical flex items-center justify-center text-white">
              <Heart className="h-5 w-5" />
            </div>
            <div className="font-bold text-lg">MedFusion AI</div>
          </div>
          <h2 className="text-2xl font-bold mb-1">Sign in</h2>
          <p className="text-neutral-500 mb-8">Use the demo clinician account to explore the platform.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-critical-50 dark:bg-critical-900/20 text-critical-700 dark:text-critical-300 text-sm">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                {error}
              </div>
            )}
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              leftIcon={<Mail className="h-4 w-4" />}
              required
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              leftIcon={<Lock className="h-4 w-4" />}
              required
            />
            <Checkbox
              label="Remember this workstation"
              checked={remember}
              onChange={e => setRemember(e.target.checked)}
            />
            <Button type="submit" fullWidth loading={loading} size="lg">
              Enter clinical workspace
            </Button>
          </form>

          <div className="mt-6 p-4 rounded-xl bg-medical-50 dark:bg-medical-900/20 text-sm">
            <div className="font-medium text-medical-800 dark:text-medical-200 mb-1">Demo credentials</div>
            <div className="font-mono text-xs text-neutral-600 dark:text-neutral-400">demo@medfusion.ai / demo123</div>
          </div>
        </div>
      </div>
    </div>
  )
}
