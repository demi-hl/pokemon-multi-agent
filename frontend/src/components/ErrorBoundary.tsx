import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-8">
          <div className="max-w-md w-full text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-rose-500/10 flex items-center justify-center">
              <svg viewBox="0 0 100 100" className="w-10 h-10 drop-shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                <path d="M 4 50 A 46 46 0 0 1 96 50" fill="none" stroke="#ef4444" strokeWidth="4" strokeLinecap="round" />
                <path d="M 96 50 A 46 46 0 0 1 4 50" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="4" strokeLinecap="round" />
                <line x1="4" y1="50" x2="96" y2="50" stroke="#52525b" strokeWidth="4" />
                <circle cx="50" cy="50" r="12" fill="none" stroke="#52525b" strokeWidth="4" />
                <circle cx="50" cy="50" r="5" fill="white" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-foreground">Something went wrong</h2>
            <p className="text-sm text-muted-foreground">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.reload()
              }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-red-500 text-white hover:bg-red-600 transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
