import { motion, useReducedMotion, type Variants } from 'framer-motion'
import ScrollReveal from './ScrollReveal'

interface Outcome {
  label: string
  title: string
  scenario: string
  result: string
  color: string
}

const OUTCOMES: Outcome[] = [
  {
    label: 'Low Risk',
    title: 'Execute',
    scenario:
      '"Customer reports Product X overheating and is under warranty. Create a service case and assign an available technician."',
    result: 'EXECUTED',
    color: '#3ecf8e',
  },
  {
    label: 'High Risk',
    title: 'Request Approval',
    scenario:
      '"The customer’s machine has a severe failure. Arrange a replacement unit."',
    result: 'APPROVAL REQUIRED',
    color: '#f2b84b',
  },
  {
    label: 'Unclear Evidence',
    title: 'Escalate',
    scenario:
      '"The customer wants Product Y replaced immediately because it is overheating."',
    result: 'ESCALATED — NO ACTION TAKEN',
    color: '#f2635a',
  },
]

const EASE = [0.22, 1, 0.36, 1] as const

const BRANCH_ENDPOINTS = [100, 300, 500]
const BRANCH_D = [
  'M300,55 Q300,95 100,135',
  'M300,55 Q310,100 300,135',
  'M300,55 Q300,95 500,135',
]

export default function OutcomesSection() {
  const prefersReducedMotion = useReducedMotion()
  const dur = prefersReducedMotion === true ? 0 : undefined

  const containerVariants: Variants = {
    hidden: {},
    visible: { transition: { staggerChildren: dur === 0 ? 0 : 0.15 } },
  }
  const trunkVariants: Variants = {
    hidden: { pathLength: 0 },
    visible: { pathLength: 1, transition: { duration: dur ?? 0.5, ease: EASE } },
  }
  const branchVariants: Variants = {
    hidden: { pathLength: 0, opacity: 0 },
    visible: {
      pathLength: 1,
      opacity: 1,
      transition: { duration: dur ?? 0.4, ease: EASE },
    },
  }
  const dotVariants: Variants = {
    hidden: { scale: 0, opacity: 0 },
    visible: { scale: 1, opacity: 1, transition: { duration: dur ?? 0.3 } },
  }
  const cardVariants: Variants = {
    hidden: { opacity: 0, y: 24 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: dur ?? 0.5, ease: EASE },
    },
  }

  return (
    <section
      id="outcomes"
      className="relative z-1 bg-black px-[clamp(14px,3vw,32px)] py-[clamp(56px,10vh,110px)] scroll-mt-[96px]"
    >
      <div className="max-w-[1100px] mx-auto flex flex-col items-center text-center">
        <ScrollReveal>
          <div className="text-[11px] md:text-[12px] uppercase tracking-[0.18em] text-[var(--muted-text)] font-medium">
            Bounded Autonomy
          </div>
        </ScrollReveal>

        <ScrollReveal delay={80} className="mt-3">
          <h2 className="font-display font-normal text-[clamp(24px,4vw,44px)] tracking-[-0.03em] leading-[1.15] text-white max-w-[640px]">
            Three Outcomes. Never A Fourth.
          </h2>
        </ScrollReveal>

        <ScrollReveal delay={160} className="mt-4">
          <p className="max-w-[560px] text-[clamp(14px,1.4vw,16px)] leading-[1.6] text-[#d0d0d0] opacity-80 font-sans-ui">
            The agent never improvises past what evidence and policy allow.
            Every request forks into exactly one of these.
          </p>
        </ScrollReveal>

        <motion.div
          className="w-full mt-[clamp(32px,5vh,56px)]"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={containerVariants}
        >
          <svg
            viewBox="0 0 600 140"
            className="w-full max-w-[500px] mx-auto mb-2 block"
            fill="none"
            aria-hidden="true"
          >
            <motion.path
              d="M300,0 L300,55"
              stroke="rgba(255,255,255,0.25)"
              strokeWidth={1.5}
              variants={trunkVariants}
            />
            {OUTCOMES.map((outcome, i) => (
              <motion.path
                key={outcome.title}
                d={BRANCH_D[i]}
                stroke={outcome.color}
                strokeWidth={1.5}
                variants={branchVariants}
              />
            ))}
            {OUTCOMES.map((outcome, i) => (
              <motion.circle
                key={`${outcome.title}-dot`}
                cx={BRANCH_ENDPOINTS[i]}
                cy={135}
                r={3.5}
                fill={outcome.color}
                variants={dotVariants}
              />
            ))}
          </svg>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-5">
            {OUTCOMES.map((outcome) => (
              <motion.div
                key={outcome.title}
                variants={cardVariants}
                className="group relative h-full flex flex-col gap-4 text-left rounded-[24px] border border-white/10 bg-white/[0.03] p-[clamp(20px,3vw,28px)] transition-all duration-[280ms] ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-1 hover:border-white/20 hover:bg-white/[0.05]"
                style={{
                  borderTopColor: outcome.color,
                  borderTopWidth: 2,
                }}
              >
                <span
                  className="absolute -top-[6px] left-1/2 -translate-x-1/2 w-2.5 h-2.5 rounded-full"
                  style={{ background: outcome.color }}
                  aria-hidden="true"
                />

                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ background: outcome.color }}
                    aria-hidden="true"
                  />
                  <span className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
                    {outcome.label}
                  </span>
                </div>

                <h3 className="font-display font-normal text-[clamp(19px,2.2vw,23px)] tracking-[-0.02em] text-white">
                  {outcome.title}
                </h3>

                <p className="flex-1 text-[13.5px] leading-[1.6] text-[#c4c2c3] font-sans-ui italic">
                  {outcome.scenario}
                </p>

                <div
                  className="inline-flex self-start items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.06em] font-sans-ui"
                  style={{
                    color: outcome.color,
                    borderColor: `${outcome.color}59`,
                    background: `${outcome.color}1f`,
                  }}
                >
                  {outcome.result}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
