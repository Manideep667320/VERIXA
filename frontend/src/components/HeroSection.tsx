import React from 'react'

export default function HeroSection() {
  return (
    <main className="flex-1 z-1 flex flex-col items-center justify-center text-center w-full max-w-[900px]">
      {/* Trust Row */}
      <div
        className="anim-reveal inline-flex items-center mb-[clamp(16px,2.5vh,26px)] max-[420px]:[--trust-size:34px] group cursor-default"
        style={{ '--d': '0.05s' } as React.CSSProperties}
      >
        <div className="flex items-center" aria-hidden="true">
          <span className="relative w-[var(--trust-size)] h-[var(--trust-size)] p-[5px] rounded-full bg-[var(--trust-bg)] border border-[var(--trust-border)] box-border z-1 transition-transform duration-350 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-[2px]">
            <span className="grid place-items-center w-full h-full rounded-full bg-white">
              <i className="fa-brands fa-microsoft text-[#111] text-[calc(var(--trust-size)*0.34)] leading-none" />
            </span>
          </span>
          <span className="relative w-[var(--trust-size)] h-[var(--trust-size)] p-[5px] rounded-full bg-[var(--trust-bg)] border border-[var(--trust-border)] box-border -ml-[calc(var(--trust-size)*0.42)] z-2 transition-transform duration-350 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-[4px]">
            <span className="grid place-items-center w-full h-full rounded-full bg-white">
              <i className="fa-brands fa-amazon text-[#111] text-[calc(var(--trust-size)*0.34)] leading-none" />
            </span>
          </span>
          <span className="relative w-[var(--trust-size)] h-[var(--trust-size)] p-[5px] rounded-full bg-[var(--trust-bg)] border border-[var(--trust-border)] box-border -ml-[calc(var(--trust-size)*0.42)] z-4 transition-transform duration-350 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-[2px]">
            <span className="grid place-items-center w-full h-full rounded-full bg-white">
              <i className="fa-brands fa-google text-[#111] text-[calc(var(--trust-size)*0.34)] leading-none" />
            </span>
          </span>
        </div>
        <div className="inline-flex items-center h-[var(--trust-size)] -ml-[calc(var(--trust-size)*0.42)] pl-[calc(var(--trust-size)*0.58)] pr-4 rounded-full bg-[var(--trust-bg)] border border-[var(--trust-border)] text-[var(--trust-text)] font-medium text-[clamp(12px,1.4vw,13.5px)] max-[720px]:text-[12px] whitespace-nowrap z-3">
          Trusted by 2000+ Enterprises
        </div>
      </div>

      {/* Headline */}
      <h1 className="font-display font-normal text-[clamp(28px,6.2vw,80px)] tracking-[-0.04em] max-[720px]:tracking-[-0.08em] max-[420px]:tracking-[-0.09em] leading-[1.12] max-[720px]:leading-[1.05] max-[420px]:leading-[1.04] text-white whitespace-nowrap overflow-hidden">
        <span className="block headline-line-1">Intelligence</span>
        <span className="block headline-line-2">Designed To Evolve</span>
      </h1>

      {/* Subhead */}
      <p
        className="anim-reveal max-w-[min(500px,92%)] mt-[clamp(14px,2vh,22px)] max-h-[700px]:mt-[10px] text-[clamp(calc(13.5px+2pt),calc(1.55vw+2pt),calc(16.5px+2pt))] font-normal leading-[1.55] text-[#d0d0d0] opacity-80"
        style={{ '--d': '0.28s' } as React.CSSProperties}
      >
        Build applications that reason, adapt and collaborate using a modular
        AI platform designed for production.
      </p>

      {/* CTA */}
      <a
        href="#get-started"
        className="anim-pulse inline-flex items-center justify-center mt-[clamp(18px,2.6vh,28px)] max-h-[700px]:mt-[14px] px-[clamp(22px,3vw,28px)] py-[clamp(11px,1.6vh,13px)] rounded-full bg-white text-black font-semibold text-[clamp(13.5px,1.5vw,14.5px)] shadow-[0_0_0_1px_rgba(255,255,255,0.15),0_0_22px_rgba(255,255,255,0.32),0_0_44px_rgba(255,255,255,0.12)] transition-all duration-[280ms] ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-[2px] hover:scale-[1.02] hover:shadow-[0_0_0_1px_rgba(255,255,255,0.22),0_0_28px_rgba(255,255,255,0.45),0_0_56px_rgba(255,255,255,0.2)]"
        style={{ '--d': '0.4s' } as React.CSSProperties}
      >
        Get Started
      </a>
    </main>
  )
}
