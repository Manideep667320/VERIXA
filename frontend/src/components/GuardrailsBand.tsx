import React from 'react'
import {
  ClipboardText,
  ShieldCheck,
  UsersThree,
  Fingerprint,
} from '@phosphor-icons/react'
import { motion, useReducedMotion, type Variants } from 'framer-motion'
import ScrollReveal from './ScrollReveal'

type PhosphorIcon = typeof ShieldCheck

type SequenceItem =
  | { kind: 'chip'; label: string }
  | { kind: 'gate'; icon: PhosphorIcon; label: string }

const SEQUENCE: SequenceItem[] = [
  { kind: 'chip', label: 'LLM Proposes' },
  { kind: 'gate', icon: ClipboardText, label: 'Schema Validated' },
  { kind: 'gate', icon: ShieldCheck, label: 'Policy Enforced' },
  { kind: 'gate', icon: UsersThree, label: 'Human-in-the-Loop' },
  { kind: 'gate', icon: Fingerprint, label: 'Fully Audited' },
  { kind: 'chip', label: 'Executes' },
]

const EASE = [0.22, 1, 0.36, 1] as const

export default function GuardrailsBand() {
  const prefersReducedMotion = useReducedMotion()
  const skip = prefersReducedMotion === true

  const containerVariants: Variants = {
    hidden: {},
    visible: { transition: { staggerChildren: skip ? 0 : 0.18 } },
  }
  const itemVariants: Variants = {
    hidden: { opacity: 0, scale: 0.92 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { duration: skip ? 0 : 0.35, ease: EASE },
    },
  }
  const gateBoxVariants: Variants = {
    hidden: { borderColor: 'rgba(255,255,255,0.15)', scale: 1 },
    visible: {
      borderColor: 'rgba(255,255,255,0.9)',
      scale: skip ? 1 : [1, 1.08, 1],
      transition: { duration: skip ? 0 : 0.4, ease: EASE },
    },
  }
  const iconVariants: Variants = {
    hidden: { opacity: 0.35 },
    visible: { opacity: 1, transition: { duration: skip ? 0 : 0.35 } },
  }
  const lineVariantsX: Variants = {
    hidden: { scaleX: 0 },
    visible: { scaleX: 1, transition: { duration: skip ? 0 : 0.25 } },
  }
  const lineVariantsY: Variants = {
    hidden: { scaleY: 0 },
    visible: { scaleY: 1, transition: { duration: skip ? 0 : 0.25 } },
  }

  const renderItem = (item: SequenceItem, key: number) => {
    if (item.kind === 'chip') {
      return (
        <motion.div
          key={key}
          variants={itemVariants}
          className="inline-flex items-center justify-center h-[calc(var(--trust-size)-6px)] px-4 rounded-full bg-[var(--pill-dark)] border border-[var(--trust-border)] text-[var(--trust-text)] font-sans-ui font-medium text-[clamp(12px,1.2vw,13.5px)] whitespace-nowrap"
        >
          {item.label}
        </motion.div>
      )
    }
    const Icon = item.icon
    return (
      <motion.div
        key={key}
        variants={itemVariants}
        className="flex flex-col items-center gap-2"
      >
        <motion.div
          variants={gateBoxVariants}
          className="grid place-items-center w-[var(--trust-size)] h-[var(--trust-size)] rounded-[10px] bg-[var(--trust-bg)] border"
        >
          <motion.span
            variants={iconVariants}
            className="grid place-items-center"
          >
            <Icon size={18} weight="bold" color="#ffffff" />
          </motion.span>
        </motion.div>
        <span className="text-[11px] text-[var(--muted-text)] font-sans-ui whitespace-nowrap">
          {item.label}
        </span>
      </motion.div>
    )
  }

  return (
    <section
      id="guardrails"
      className="relative z-1 bg-black px-[clamp(14px,3vw,32px)] py-[clamp(48px,8vh,88px)] scroll-mt-[96px]"
    >
      <div className="max-w-[820px] mx-auto flex flex-col items-center text-center">
        <ScrollReveal>
          <div className="text-[11px] md:text-[12px] uppercase tracking-[0.18em] text-[var(--muted-text)] font-medium">
            Bounded By Design
          </div>
        </ScrollReveal>

        <ScrollReveal delay={80} className="mt-3">
          <p className="max-w-[480px] text-[clamp(14px,1.4vw,16px)] leading-[1.6] text-[#d0d0d0] opacity-80 font-sans-ui">
            The LLM proposes. Deterministic application code authorizes,
            executes, and remembers.
          </p>
        </ScrollReveal>

        <div className="w-full mt-[clamp(28px,4.5vh,44px)]">
          {/* Desktop: horizontal checkpoint gate */}
          <motion.div
            className="hidden md:flex items-center justify-center flex-wrap gap-y-4"
            initial={skip ? 'visible' : 'hidden'}
            whileInView="visible"
            viewport={{ once: true, amount: 0.5 }}
            variants={containerVariants}
          >
            {SEQUENCE.map((item, i) => (
              <React.Fragment key={i}>
                {renderItem(item, i)}
                {i < SEQUENCE.length - 1 && (
                  <motion.span
                    variants={lineVariantsX}
                    className="w-[24px] h-px bg-white/15 origin-left mx-1.5"
                    aria-hidden="true"
                  />
                )}
              </React.Fragment>
            ))}
          </motion.div>

          {/* Mobile: vertical checkpoint gate */}
          <motion.div
            className="flex md:hidden flex-col items-center gap-2"
            initial={skip ? 'visible' : 'hidden'}
            whileInView="visible"
            viewport={{ once: true, amount: 0.5 }}
            variants={containerVariants}
          >
            {SEQUENCE.map((item, i) => (
              <React.Fragment key={i}>
                {renderItem(item, i)}
                {i < SEQUENCE.length - 1 && (
                  <motion.span
                    variants={lineVariantsY}
                    className="w-px h-[16px] bg-white/15 origin-top"
                    aria-hidden="true"
                  />
                )}
              </React.Fragment>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  )
}
