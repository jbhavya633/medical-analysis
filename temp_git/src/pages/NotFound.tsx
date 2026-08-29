import { Link } from 'react-router-dom'
import { Home, Compass, Search } from 'lucide-react'
import { Button } from '../components/ui/Button'

export function NotFound() {
  return (
    <div className="min-h-full flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="text-9xl font-bold bg-gradient-medical bg-clip-text text-transparent mb-4">404</div>
        <h1 className="text-2xl font-bold mb-2">Page not found</h1>
        <p className="text-neutral-500 mb-8">
          The page you're looking for doesn't exist or has been moved. The MedFusion workspace is still here.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Button variant="outline" leftIcon={<Home className="h-4 w-4" />} onClick={() => window.location.href = '/'}>
            Back to dashboard
          </Button>
          <Button variant="outline" leftIcon={<Compass className="h-4 w-4" />} onClick={() => window.location.href = '/patients'}>
            Browse patients
          </Button>
        </div>
        <div className="mt-8 p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900 text-sm text-neutral-500 flex items-center gap-2 justify-center">
          <Search className="h-4 w-4" />
          Try searching from the top bar or check the URL.
        </div>
      </div>
    </div>
  )
}