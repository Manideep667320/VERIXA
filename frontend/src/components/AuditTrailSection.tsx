import { Check } from '@phosphor-icons/react'
import { motion, useReducedMotion, type Variants } from 'framer-motion'
import ScrollReveal from './ScrollReveal'

const EVENTS = [
  { time: '12:03', label: 'Request received' },
  { time: '12:03', label: 'Evidence retrieved' },
  { time: '12:04', label: 'Decision generated' },
  { time: '12:04', label: 'Policy checked' },
  { time: '12:04', label: 'Approval requested' },
  { time: '12:06', label: 'Approval granted' },
  { time: '12:06', label: 'Ticket created' },
  { time: '12:06', label: 'Technician assigned' },
  { time: '12:07', label: 'Customer notified' },
  { time: '12:07', label: 'Actions verified' },
]

const EASE = [0.22, 1, 0.36, 1] as const
const STAGGER = 0.11

export default function AuditTrailSection() {
  const prefersReducedMotion = useReducedMotion()
  const skip = prefersReducedMotion === true

  const listVariants: Variants = {
    hidden: {},
    visible: { transition: { staggerChildren: skip ? 0 : STAGGER } },
  }
  const railVariants: Variants = {
    hidden: { scaleY: 0 },
    visible: {
      scaleY: 1,
      transition: {
        duration: skip ? 0 : EVENTS.length * STAGGER,
        ease: 'linear',
      },
    },
  }
  const rowVariants: Variants = {
    hidden: { opacity: 0, x: -12 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: skip ? 0 : 0.35, ease: EASE },
    },
  }
  const dotVariants: Variants = {
    hidden: {
      backgroundColor: 'rgba(0,0,0,0)',
      borderColor: 'rgba(255,255,255,0.3)',
    },
    visible: {
      backgroundColor: 'rgba(255,255,255,0.9)',
      borderColor: 'rgba(255,255,255,0.9)',
      transition: { duration: skip ? 0 : 0.25 },
    },
  }
  const checkVariants: Variants = {
    hidden: { scale: 0, opacity: 0 },
    visible: {
      scale: 1,
      opacity: 1,
      transition: skip
        ? { duration: 0 }
        : {
            delay: EVENTS.length * STAGGER,
            type: 'spring',
            stiffness: 400,
            damping: 12,
          },
    },
  }
  const statusVariants: Variants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: skip
        ? { duration: 0 }
        : { delay: EVENTS.length * STAGGER + 0.1, duration: 0.3, ease: EASE },
    },
  }

  return (
    <section
      id="audit-trail"
      className="relative z-1 bg-black px-[clamp(14px,3vw,32px)] py-[clamp(56px,10vh,110px)] scroll-mt-[96px]"
    >
      <div className="max-w-[900px] mx-auto flex flex-col items-center text-center">
        <ScrollReveal>
          <div className="text-[11px] md:text-[12px] uppercase tracking-[0.18em] text-[var(--muted-text)] font-medium">
            The Audit Trail
          </div>
        </ScrollReveal>

        <ScrollReveal delay={80} className="mt-3">
          <h2 className="font-display font-normal text-[clamp(24px,4vw,44px)] tracking-[-0.03em] leading-[1.15] text-white max-w-[560px]">
            Every Decision, Explained
          </h2>
        </ScrollReveal>

        <ScrollReveal delay={160} className="mt-4">
          <p className="max-w-[520px] text-[clamp(14px,1.4vw,16px)] leading-[1.6] text-[#d0d0d0] opacity-80 font-sans-ui">
            No hidden chain-of-thought. Just a concise, evidence-linked
            timeline of what the agent saw, decided, and did.
          </p>
        </ScrollReveal>

        <ScrollReveal
          delay={240}
          className="w-full mt-[clamp(32px,5vh,56px)] max-w-[640px]"
        >
          <div className="rounded-[20px] border border-white/10 bg-[#0a0a0a] shadow-[0_0_0_1px_rgba(255,255,255,0.04),0_30px_80px_rgba(0,0,0,0.55)] overflow-hidden text-left">
            {/* Terminal-style title bar */}
            <div className="flex items-center justify-between gap-3 px-5 py-3.5 border-b border-white/10 bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5" aria-hidden="true">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#f2635a]/70" />
                  <span className="w-2.5 h-2.5 rounded-full bg-[#f2b84b]/70" />
                  <span className="w-2.5 h-2.5 rounded-full bg-[#3ecf8e]/70" />
                </div>
                <span className="font-mono text-[12px] text-[#c4c2c3] tracking-[0.02em]">
                  RUN-1042
                </span>
              </div>
              <motion.span
                variants={statusVariants}
                initial={skip ? 'visible' : 'hidden'}
                whileInView="visible"
                viewport={{ once: true, amount: 0.3 }}
                className="inline-flex items-center gap-1.5 rounded-full border border-[#3ecf8e]/35 bg-[#3ecf8e]/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.06em] text-[#3ecf8e]"
              >
                <Check size={10} weight="bold" />
                Completed
              </motion.span>
            </div>

            <motion.div
              className="relative px-5 py-2"
              initial={skip ? 'visible' : 'hidden'}
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={listVariants}
            >
              <motion.div
                className="absolute left-[23px] top-3 bottom-3 w-px bg-white/15 origin-top"
                variants={railVariants}
                aria-hidden="true"
              />

              {EVENTS.map((event, i) => {
                const isLast = i === EVENTS.length - 1
                return (
                  <motion.div
                    key={`${event.time}-${event.label}`}
                    variants={rowVariants}
                    className={`group relative flex items-center justify-between gap-4 py-2.5 pl-5 -mx-2 px-2 rounded-md transition-colors hover:bg-white/[0.03] ${
                      i < EVENTS.length - 1 ? 'border-b border-white/5' : ''
                    }`}
                  >
                    <motion.span
                      variants={dotVariants}
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full border"
                      aria-hidden="true"
                    />
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="font-mono text-[11px] text-[var(--muted-text)] tabular-nums shrink-0">
                        {event.time}
                      </span>
                      <span
                        className={`font-sans-ui text-[13.5px] truncate ${
                          isLast ? 'text-white font-medium' : 'text-[#d0d0d0]'
                        }`}
                      >
                        {event.label}
                      </span>
                    </div>
                    {isLast && (
                      <motion.span
                        variants={checkVariants}
                        className="grid place-items-center w-[18px] h-[18px] rounded-full bg-[#3ecf8e]/15 shrink-0"
                      >
                        <Check size={11} weight="bold" color="#3ecf8e" />
                      </motion.span>
                    )}
                  </motion.div>
                )
              })}
            </motion.div>

            {/* Run summary footer */}
            <div className="flex items-center justify-between gap-4 px-5 py-3.5 border-t border-white/10 bg-white/[0.02] font-mono text-[11px] text-[var(--muted-text)]">
              <span>Duration 4m 32s</span>
              <span>5 evidence sources</span>
              <span>1 approval</span>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}
