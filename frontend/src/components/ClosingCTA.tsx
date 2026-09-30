import { motion, useReducedMotion } from 'framer-motion'
import { Link } from 'react-router-dom'
import ScrollReveal from './ScrollReveal'

export default function ClosingCTA() {
  const prefersReducedMotion = useReducedMotion()
  const skip = prefersReducedMotion === true

  return (
    <section className="relative z-1 overflow-hidden bg-black px-[clamp(14px,3vw,32px)] py-[clamp(64px,12vh,128px)]">
      <div
        aria-hidden="true"
        className="absolute inset-0 opacity-[0.06] pointer-events-none"
        style={{
          backgroundImage:
            'radial-gradient(rgba(255,255,255,0.6) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
      />

      <div className="relative z-10 max-w-[720px] mx-auto flex flex-col items-center text-center">
        <ScrollReveal>
          <h2 className="font-display font-normal text-[clamp(26px,4.5vw,52px)] tracking-[-0.03em] leading-[1.15] text-white">
            Act When Safe. Ask When Necessary.
            <br />
            Explain Always.
          </h2>
        </ScrollReveal>

        <ScrollReveal delay={100} className="mt-4">
          <p className="max-w-[520px] text-[clamp(14px,1.4vw,16px)] leading-[1.6] text-[#d0d0d0] opacity-80 font-sans-ui">
            We don't give an AI unrestricted access to enterprise systems. We
            give it evidence, bounded actions, policy, and verification.
          </p>
        </ScrollReveal>

        <ScrollReveal
          delay={200}
          className="relative mt-[clamp(20px,3vh,32px)]"
        >
          <motion.div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 m-auto w-[280px] h-[140px] rounded-full blur-[50px]"
            style={{
              background:
                'radial-gradient(circle, rgba(255,255,255,0.35), transparent 70%)',
            }}
            animate={skip ? { opacity: 0.5 } : { opacity: [0.4, 0.7, 0.4] }}
            transition={
              skip
                ? undefined
                : { duration: 3.2, repeat: Infinity, ease: 'easeInOut' }
            }
          />
          <Link
            to="/agent"
            className="relative inline-flex items-center justify-center px-[clamp(22px,3vw,28px)] py-[clamp(11px,1.6vh,13px)] rounded-full bg-white text-black font-semibold text-[clamp(13.5px,1.5vw,14.5px)] shadow-[0_0_0_1px_rgba(255,255,255,0.15),0_0_22px_rgba(255,255,255,0.32),0_0_44px_rgba(255,255,255,0.12)] transition-all duration-[280ms] ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-[2px] hover:scale-[1.02] hover:shadow-[0_0_0_1px_rgba(255,255,255,0.22),0_0_28px_rgba(255,255,255,0.45),0_0_56px_rgba(255,255,255,0.2)]"
          >
            Request A Demo
          </Link>
        </ScrollReveal>

        <ScrollReveal delay={280} className="mt-[clamp(32px,5vh,48px)]">
          <p className="text-[11px] text-[var(--muted-text)] font-sans-ui">
            © 2026 Verixa — Evidence-to-Action Enterprise AI Agent
          </p>
        </ScrollReveal>
      </div>
    </section>
  )
}
