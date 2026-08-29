import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from './Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ error, errorInfo })
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-950 p-6">
          <div className="max-w-lg w-full text-center">
            <div className="mx-auto w-16 h-16 rounded-2xl bg-critical-100 dark:bg-critical-900/30 flex items-center justify-center mb-6">
              <AlertTriangle className="h-8 w-8 text-critical-600 dark:text-critical-400" />
            </div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
              Something went wrong
            </h1>
            <p className="text-neutral-500 dark:text-neutral-400 mb-6">
              An unexpected error occurred. The clinical team has been notified.
            </p>
            {this.state.error && (
              <pre className="text-left text-xs bg-neutral-100 dark:bg-neutral-900 rounded-lg p-4 mb-6 overflow-auto max-h-40 text-critical-700 dark:text-critical-300">
                {this.state.error.message}
              </pre>
            )}
            <div className="flex items-center justify-center gap-3">
              <Button variant="secondary" leftIcon={<Home className="h-4 w-4" />} onClick={() => { window.location.href = '/' }}>
                Go Home
              </Button>
              <Button leftIcon={<RefreshCw className="h-4 w-4" />} onClick={this.handleReset}>
                Try Again
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
