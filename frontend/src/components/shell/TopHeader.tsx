import { Search, Bell } from 'lucide-react'

interface TopHeaderProps {
  contextLabel: string
  title: string
}

export default function TopHeader({ contextLabel, title }: TopHeaderProps) {
  return (
    <header className="flex items-center justify-between gap-6 h-[76px] shrink-0 px-6 border-b border-white/10 bg-black">
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
          {contextLabel}
        </div>
        <h1 className="mt-0.5 text-[18px] font-semibold text-white tracking-[-0.01em] truncate">
          {title}
        </h1>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <div className="relative hidden sm:block">
          <Search
            size={14}
            strokeWidth={1.75}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--muted-text)]"
          />
          <input
            type="text"
            placeholder="Search workspace"
            className="h-8 w-[200px] rounded-lg border border-white/10 bg-white/[0.03] pl-8 pr-3 text-[12.5px] text-white placeholder:text-[var(--muted-text)] outline-none transition-colors focus:border-white/25"
          />
        </div>

        <button
          type="button"
          aria-label="Notifications"
          className="grid place-items-center w-8 h-8 rounded-lg border border-white/10 bg-white/[0.03] text-[#c4c2c3] transition-colors hover:bg-white/[0.06] hover:text-white"
        >
          <Bell size={15} strokeWidth={1.75} />
        </button>

        <div className="hidden md:flex items-center gap-2.5 pl-3 border-l border-white/10">
          <span className="grid place-items-center w-8 h-8 rounded-full bg-[var(--pill-dark)] border border-white/15 text-[12px] font-semibold text-white shrink-0">
            OM
          </span>
          <div className="leading-tight">
            <div className="text-[12.5px] font-medium text-white">Operations</div>
            <div className="text-[11px] text-[var(--muted-text)]">Manager</div>
          </div>
        </div>
      </div>
    </header>
  )
}
