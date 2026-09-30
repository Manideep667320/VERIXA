import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)]">
      {/* Header */}
      <header className="border-b border-[var(--color-border)] px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[var(--color-primary)] rounded-lg flex items-center justify-center text-white font-bold text-sm">
              E2A
            </div>
            <h1 className="text-lg font-semibold">Evidence-to-Action</h1>
          </div>
          <span className="text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] px-3 py-1 rounded-full">
            v0.1.0 · MVP
          </span>
        </div>
      </header>

      {/* Main content area — will be split into panels */}
      <main className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat / Request Panel */}
          <div className="lg:col-span-1 bg-[var(--color-surface)] rounded-xl p-6 border border-[var(--color-border)]">
            <h2 className="text-sm font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-4">
              Request
            </h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              Chat interface will be implemented here.
            </p>
          </div>

          {/* Agent Activity Panel */}
          <div className="lg:col-span-1 bg-[var(--color-surface)] rounded-xl p-6 border border-[var(--color-border)]">
            <h2 className="text-sm font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-4">
              Agent Activity
            </h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              Agent pipeline status will be displayed here.
            </p>
          </div>

          {/* Evidence / Decision Panel */}
          <div className="lg:col-span-1 bg-[var(--color-surface)] rounded-xl p-6 border border-[var(--color-border)]">
            <h2 className="text-sm font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-4">
              Evidence & Decision
            </h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              Evidence, risk, policy, and actions will appear here.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
