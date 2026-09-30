import React from 'react'
import { Link } from 'react-router-dom'

export default function HeroSection() {
  return (
    <main className="flex-1 z-1 flex flex-col items-center justify-center text-center w-full max-w-[900px]">
      {/* Headline */}
      <h1 className="font-display font-normal text-[clamp(28px,6.2vw,80px)] tracking-[-0.04em] max-[720px]:tracking-[-0.08em] max-[420px]:tracking-[-0.09em] leading-[1.12] max-[720px]:leading-[1.05] max-[420px]:leading-[1.04] text-white whitespace-nowrap overflow-hidden">
        <span className="block headline-line-1">Evidence-Backed</span>
        <span className="block headline-line-2">Enterprise Action</span>
      </h1>

      {/* Subhead */}
      <p
        className="anim-reveal max-w-[min(560px,92%)] mt-[clamp(14px,2vh,22px)] max-h-[700px]:mt-[10px] text-[clamp(calc(13.5px+2pt),calc(1.55vw+2pt),calc(16.5px+2pt))] font-normal leading-[1.55] text-[#d0d0d0] opacity-80"
        style={{ '--d': '0.28s' } as React.CSSProperties}
      >
        An AI agent that turns policy, evidence and risk into accountable
        action — executing when it's safe, asking for approval when it
        isn't, and refusing when the evidence doesn't hold up.
      </p>

      {/* CTA */}
      <Link
        to="/agent"
        className="anim-pulse inline-flex items-center justify-center mt-[clamp(18px,2.6vh,28px)] max-h-[700px]:mt-[14px] px-[clamp(22px,3vw,28px)] py-[clamp(11px,1.6vh,13px)] rounded-full bg-white text-black font-semibold text-[clamp(13.5px,1.5vw,14.5px)] shadow-[0_0_0_1px_rgba(255,255,255,0.15),0_0_22px_rgba(255,255,255,0.32),0_0_44px_rgba(255,255,255,0.12)] transition-all duration-[280ms] ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-[2px] hover:scale-[1.02] hover:shadow-[0_0_0_1px_rgba(255,255,255,0.22),0_0_28px_rgba(255,255,255,0.45),0_0_56px_rgba(255,255,255,0.2)]"
        style={{ '--d': '0.4s' } as React.CSSProperties}
      >
        See It Decide
      </Link>
    </main>
  )
}
