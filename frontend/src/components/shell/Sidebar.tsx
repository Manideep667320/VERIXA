import { useEffect, useState } from 'react'
import {
  LayoutGrid,
  FileCheck2,
  ShieldCheck,
  History,
  BarChart3,
  ScrollText,
  ChevronRight,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from 'cn'
import { healthApi } from '@/services/api'
import VerixaLogo from '../VerixaLogo'

const NAV_ITEMS = [
  { to: '/agent', label: 'Agent', icon: LayoutGrid },
  { to: '/decisions', label: 'Decisions', icon: FileCheck2 },
  { to: '/approvals', label: 'Approvals', icon: ShieldCheck },
  { to: '/audit', label: 'Audit Trail', icon: History },
  { to: '/insights', label: 'Insights', icon: BarChart3 },
  { to: '/policy', label: 'Policy', icon: ScrollText },
]

type HealthState = 'checking' | 'online' | 'offline'

export default function Sidebar() {
  const [health, setHealth] = useState<HealthState>('checking')

  useEffect(() => {
    let cancelled = false
    healthApi
      .check()
      .then(() => {
        if (!cancelled) setHealth('online')
      })
      .catch(() => {
        if (!cancelled) setHealth('offline')
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <aside className="hidden md:flex flex-col shrink-0 w-[236px] h-screen sticky top-0 border-r border-white/10 bg-[#0a0a0a] px-4 py-5">
      <NavLink to="/" className="px-1 group flex items-center" title="Back to Overview">
        <VerixaLogo size={22} showWordmark={true} />
      </NavLink>

      <div className="mt-8 px-1 text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
        Workspace
      </div>

      <nav className="mt-2 flex flex-col gap-0.5">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13.5px] font-medium transition-colors',
                isActive
                  ? 'bg-white text-black'
                  : 'text-[#c4c2c3] hover:bg-white/5 hover:text-white'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} strokeWidth={1.75} />
                <span className="flex-1">{label}</span>
                {isActive && <ChevronRight size={14} strokeWidth={2} />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-4">
        <div className="border-t border-white/10 pt-4 px-1">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
            System Status
          </div>
          <div className="mt-2 flex items-center gap-2 text-[12.5px] text-[#c4c2c3]">
            <span
              className={cn(
                'w-1.5 h-1.5 rounded-full',
                health === 'online' && 'bg-[#3ecf8e]',
                health === 'offline' && 'bg-[#f2635a]',
                health === 'checking' && 'bg-[#f2b84b]'
              )}
              aria-hidden="true"
            />
            {health === 'online' && 'All systems operational'}
            {health === 'offline' && 'Backend unreachable'}
            {health === 'checking' && 'Checking status…'}
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2.5 border-t border-white/10 pt-4 px-1">
          <span className="grid place-items-center w-8 h-8 rounded-full bg-[var(--pill-dark)] border border-white/15 text-[12px] font-semibold text-white shrink-0">
            OM
          </span>
          <div className="min-w-0 leading-tight">
            <div className="text-[13px] font-medium text-white truncate">Operations</div>
            <div className="text-[11.5px] text-[var(--muted-text)] truncate">Manager</div>
          </div>
        </div>
      </div>
    </aside>
  )
}
