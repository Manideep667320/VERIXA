import React, { useEffect, useRef, useState } from 'react'

interface StatItem {
  icon: string
  target: number
  suffix: string
  decimals: number
  label: string
  delay: string
  startOffset: number
  duration: number
}

const STATS_DATA: StatItem[] = [
  {
    icon: '<',
    target: 120,
    suffix: 'ms',
    decimals: 0,
    label: 'Inference Time',
    delay: '0.5s',
    startOffset: 480,
    duration: 1500,
  },
  {
    icon: '%',
    target: 99.99,
    suffix: '%',
    decimals: 2,
    label: 'Platform Uptime',
    delay: '0.58s',
    startOffset: 570,
    duration: 1580,
  },
  {
    icon: '*',
    target: 24,
    suffix: '/7',
    decimals: 0,
    label: 'Autonomous Runtime',
    delay: '0.66s',
    startOffset: 660,
    duration: 1660,
  },
  {
    icon: '#',
    target: 2.4,
    suffix: 'M',
    decimals: 1,
    label: 'Context Windows',
    delay: '0.74s',
    startOffset: 750,
    duration: 1740,
  },
]

function StatCounter({ stat }: { stat: StatItem }) {
  const [displayValue, setDisplayValue] = useState<string>(() => {
    if (
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      return stat.target.toFixed(stat.decimals)
    }
    return (0).toFixed(stat.decimals)
  })
  const counterRef = useRef<HTMLDivElement>(null)
  const animatedRef = useRef(false)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return
    }

    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3)

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting || animatedRef.current) return
          animatedRef.current = true

          const timeoutId = window.setTimeout(() => {
            const startTime = performance.now()
            const animate = (currentTime: number) => {
              const elapsed = currentTime - startTime
              const progress = Math.min(1, elapsed / stat.duration)
              const eased = easeOutCubic(progress)
              const currentVal = stat.target * eased
              setDisplayValue(currentVal.toFixed(stat.decimals))

              if (progress < 1) {
                requestAnimationFrame(animate)
              }
            }
            requestAnimationFrame(animate)
          }, stat.startOffset)

          return () => clearTimeout(timeoutId)
        })
      },
      { threshold: 0.25 }
    )

    if (counterRef.current) {
      observer.observe(counterRef.current)
    }

    return () => observer.disconnect()
  }, [stat])

  return (
    <div
      ref={counterRef}
      className="anim-reveal flex flex-col items-center text-center gap-0.5"
      style={{ '--d': stat.delay } as React.CSSProperties}
    >
      <div className="font-display text-[clamp(22px,3vw,33px)] text-white leading-none">
        {stat.icon}
      </div>
      <div className="font-sans-ui text-[clamp(18px,2.2vw,26px)] font-medium tracking-[-0.025em] tabular-nums text-white leading-[1.2]">
        <span>{displayValue}</span>
        <span className="text-white">{stat.suffix}</span>
      </div>
      <div className="text-[var(--muted)] text-[clamp(11px,1.2vw,12.5px)] font-normal">
        {stat.label}
      </div>
    </div>
  )
}

export default function StatsFooter() {
  return (
    <footer
      className="shrink-0 z-1 grid grid-cols-2 md:grid-cols-4 w-full max-w-[920px] gap-x-[18px] gap-y-3 md:gap-x-[18px] md:gap-y-3 pt-[clamp(8px,1.4vh,16px)] max-h-[700px]:pt-1.5"
      aria-label="Platform metrics"
    >
      {STATS_DATA.map((stat) => (
        <StatCounter key={stat.label} stat={stat} />
      ))}
    </footer>
  )
}
