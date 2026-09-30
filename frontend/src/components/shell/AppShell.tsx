import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import TopHeader from './TopHeader'

interface AppShellProps {
  contextLabel: string
  title: string
  children: ReactNode
}

export default function AppShell({ contextLabel, title, children }: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopHeader contextLabel={contextLabel} title={title} />
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  )
}
