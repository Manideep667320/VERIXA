import { cn } from 'cn'

export type StatusTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

const TONE_CLASSES: Record<StatusTone, string> = {
  neutral: 'border-white/15 text-[#c4c2c3]',
  success: 'border-[#3ecf8e]/40 text-[#3ecf8e]',
  warning: 'border-[#f2b84b]/40 text-[#f2b84b]',
  danger: 'border-[#f2635a]/40 text-[#f2635a]',
  info: 'border-white/25 text-white',
}

interface StatusBadgeProps {
  label: string
  tone?: StatusTone
  className?: string
}

export default function StatusBadge({
  label,
  tone = 'neutral',
  className,
}: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.05em] whitespace-nowrap',
        TONE_CLASSES[tone],
        className
      )}
    >
      {label}
    </span>
  )
}
