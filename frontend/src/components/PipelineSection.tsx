import { useRef } from 'react'
import {
  motion,
  useScroll,
  useTransform,
  useReducedMotion,
  type MotionValue,
} from 'framer-motion'
import {
  MessageSquareText,
  Search,
  Brain,
  ShieldCheck,
  Zap,
  BadgeCheck,
  History,
} from 'lucide-react'
import ScrollReveal from './ScrollReveal'

const STEP_DEFS = [
  { label: 'Request', icon: MessageSquareText },
  { label: 'Evidence', icon: Search },
  { label: 'Reasoning', icon: Brain },
  { label: 'Policy', icon: ShieldCheck },
  { label: 'Action / Approval', icon: Zap },
  { label: 'Verification', icon: BadgeCheck },
  { label: 'Audit', icon: History },
]

const MUTED_BG = '#28282a'
const MUTED_TEXT = '#8e8e8e'
const LIT_BG = '#ffffff'
const LIT_ICON = '#000000'
const LIT_LABEL = '#ffffff'

function useNodeColors(
  progress: MotionValue<number>,
  lo: number,
  hi: number
) {
  const bg = useTransform(progress, [lo, hi], [MUTED_BG, LIT_BG])
  const icon = useTransform(progress, [lo, hi], [MUTED_TEXT, LIT_ICON])
  const label = useTransform(progress, [lo, hi], [MUTED_TEXT, LIT_LABEL])
  return { bg, icon, label }
}

export default function PipelineSection() {
  const sectionRef = useRef<HTMLElement>(null)
  const prefersReducedMotion = useReducedMotion()
  const reduced = prefersReducedMotion === true
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start'],
  })

  const railFill = useTransform(scrollYProgress, [0, 1], [0, 1])
  const cometLeft = useTransform(scrollYProgress, [0, 1], ['0%', '100%'])
  const cometTop = useTransform(scrollYProgress, [0, 1], ['0%', '100%'])

  const n0 = useNodeColors(scrollYProgress, -0.08, 0.08)
  const n1 = useNodeColors(scrollYProgress, 0.09, 0.25)
  const n2 = useNodeColors(scrollYProgress, 0.25, 0.41)
  const n3 = useNodeColors(scrollYProgress, 0.42, 0.58)
  const n4 = useNodeColors(scrollYProgress, 0.59, 0.75)
  const n5 = useNodeColors(scrollYProgress, 0.75, 0.91)
  const n6 = useNodeColors(scrollYProgress, 0.92, 1.08)
  const nodes = [n0, n1, n2, n3, n4, n5, n6]

  return (
    <section
      id="decision-layer"
      ref={sectionRef as React.RefObject<HTMLElement>}
      className="relative z-1 bg-black px-[clamp(14px,3vw,32px)] py-[clamp(56px,10vh,110px)] scroll-mt-[96px]"
    >
      <div className="max-w-[1040px] mx-auto flex flex-col items-center text-center">
        <ScrollReveal>
          <div className="text-[11px] md:text-[12px] uppercase tracking-[0.18em] text-[var(--muted-text)] font-medium">
            The Decision Layer
          </div>
        </ScrollReveal>

        <ScrollReveal delay={80} className="mt-3">
          <h2 className="font-display font-normal text-[clamp(24px,4vw,44px)] tracking-[-0.03em] leading-[1.15] text-white max-w-[640px]">
            Evidence In. Accountable Action Out.
          </h2>
        </ScrollReveal>

        <ScrollReveal delay={160} className="mt-4">
          <p className="max-w-[560px] text-[clamp(14px,1.4vw,16px)] leading-[1.6] text-[#d0d0d0] opacity-80 font-sans-ui">
            Every request moves through the same deterministic pipeline — no
            step is skipped, and no action reaches a system of record without
            passing through policy and risk control first.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={240} className="w-full mt-[clamp(40px,7vh,72px)]">
          {/* Desktop: horizontal stepper with traveling signal */}
          <div className="hidden md:block relative">
            <div className="relative flex items-start justify-between">
              {STEP_DEFS.map(({ icon: Icon }, i) => (
                <div key={i} className="relative z-1 flex flex-1 justify-center">
                  <motion.div
                    className="grid place-items-center w-12 h-12 rounded-full border shadow-[0_0_0_1px_rgba(0,0,0,0.4)]"
                    style={{
                      background: reduced ? LIT_BG : nodes[i].bg,
                      borderColor: 'rgba(255,255,255,0.22)',
                    }}
                  >
                    <motion.div
                      style={{ color: reduced ? LIT_ICON : nodes[i].icon }}
                    >
                      <Icon size={19} strokeWidth={1.75} />
                    </motion.div>
                  </motion.div>
                </div>
              ))}

              <div className="absolute left-[24px] right-[24px] top-6 -translate-y-1/2 h-[2px] rounded-full bg-white/10">
                <motion.div
                  className="h-full rounded-full bg-white"
                  style={{
                    scaleX: reduced ? 1 : railFill,
                    transformOrigin: 'left',
                  }}
                />
                <motion.div
                  aria-hidden="true"
                  className="absolute top-1/2 w-3 h-3 -translate-y-1/2 -translate-x-1/2 rounded-full bg-white"
                  style={{
                    left: reduced ? '100%' : cometLeft,
                    boxShadow: '0 0 12px 4px rgba(255,255,255,0.65)',
                  }}
                />
              </div>
            </div>

            <div className="mt-3 flex items-start justify-between">
              {STEP_DEFS.map((step, i) => (
                <motion.div
                  key={step.label}
                  style={{ color: reduced ? LIT_LABEL : nodes[i].label }}
                  className="flex-1 px-1 font-sans-ui font-medium text-[12.5px] leading-tight"
                >
                  {step.label}
                </motion.div>
              ))}
            </div>
          </div>

          {/* Mobile: vertical stepper with traveling signal */}
          <div className="md:hidden relative max-w-[280px] mx-auto">
            <div className="relative flex flex-col items-start gap-8">
              {STEP_DEFS.map(({ icon: Icon, label }, i) => (
                <div key={label} className="relative z-1 flex items-center gap-3.5">
                  <motion.div
                    className="grid place-items-center w-11 h-11 rounded-full border shrink-0"
                    style={{
                      background: reduced ? LIT_BG : nodes[i].bg,
                      borderColor: 'rgba(255,255,255,0.22)',
                    }}
                  >
                    <motion.div
                      style={{ color: reduced ? LIT_ICON : nodes[i].icon }}
                    >
                      <Icon size={17} strokeWidth={1.75} />
                    </motion.div>
                  </motion.div>
                  <motion.div
                    style={{ color: reduced ? LIT_LABEL : nodes[i].label }}
                    className="font-sans-ui font-medium text-[13px]"
                  >
                    {label}
                  </motion.div>
                </div>
              ))}

              <div className="absolute left-6 top-5 bottom-5 -translate-x-1/2 w-[2px] rounded-full bg-white/10">
                <motion.div
                  className="w-full rounded-full bg-white"
                  style={{
                    scaleY: reduced ? 1 : railFill,
                    height: '100%',
                    transformOrigin: 'top',
                  }}
                />
                <motion.div
                  aria-hidden="true"
                  className="absolute left-1/2 w-3 h-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white"
                  style={{
                    top: reduced ? '100%' : cometTop,
                    boxShadow: '0 0 12px 4px rgba(255,255,255,0.65)',
                  }}
                />
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}
