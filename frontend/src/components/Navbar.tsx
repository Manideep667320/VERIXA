import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const NAV_ITEMS = [
  { id: 'home', label: 'Home' },
  { id: 'decision-layer', label: 'Decision Layer' },
  { id: 'outcomes', label: 'Outcomes' },
  { id: 'guardrails', label: 'Guardrails' },
  { id: 'audit-trail', label: 'Audit Trail' },
]

export default function Navbar() {
  const [activeId, setActiveId] = useState('home')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleSelectNav = (id: string) => {
    setActiveId(id)
    setMobileMenuOpen(false)
  }

  // Deep-link support: a hard page load with a #hash fires the browser's native
  // anchor jump before React has mounted the target section, so it silently no-ops.
  // Re-run it once mounted.
  useEffect(() => {
    const hash = window.location.hash.slice(1)
    if (!hash) return
    const target = document.getElementById(hash)
    if (!target) return
    requestAnimationFrame(() => {
      target.scrollIntoView({ behavior: 'auto' })
      setActiveId(hash)
    })
  }, [])

  // Scroll-spy: highlight whichever section currently sits in the viewport's focal band
  useEffect(() => {
    const sections = NAV_ITEMS.map((item) => document.getElementById(item.id)).filter(
      (el): el is HTMLElement => el !== null
    )
    if (sections.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveId(entry.target.id)
        })
      },
      { rootMargin: '-45% 0px -50% 0px', threshold: 0 }
    )

    sections.forEach((section) => observer.observe(section))
    return () => observer.disconnect()
  }, [])

  // Keyboard Escape and viewport resize handling
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileMenuOpen(false)
    }
    const handleResize = () => {
      if (window.innerWidth > 720) setMobileMenuOpen(false)
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  // Lock body scroll when mobile menu is active
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.classList.add('menu-open')
    } else {
      document.body.classList.remove('menu-open')
    }
  }, [mobileMenuOpen])

  return (
    <>
      <header className="fixed top-0 inset-x-0 z-40 flex items-center justify-between md:justify-center w-full gap-[clamp(18px,2.8vw,28px)] px-[clamp(14px,3vw,32px)] py-[clamp(16px,2.4vh,28px)] anim-slide-down">
        {/* Logo */}
        <a
          href="#home"
          aria-label="Home"
          onClick={() => handleSelectNav('home')}
          className="shrink-0 w-[48px] h-[48px] md:w-[clamp(40px,4.4vw,46px)] md:h-[clamp(40px,4.4vw,46px)] rounded-full [box-shadow:var(--nav-shadow)] grid place-items-center overflow-hidden border-[1.5px] border-white transition-transform duration-[280ms] ease-[cubic-bezier(0.22,1,0.36,1)] hover:scale-[1.04]"
        >
          <img
            src="/assets/logo.webp"
            alt="Evidence-to-Action"
            width={92}
            height={92}
            className="w-full h-full object-cover"
          />
        </a>

        {/* Desktop Nav Pill */}
        <nav
          className="hidden md:flex flex-1 items-center justify-evenly h-[clamp(44px,5.2vw,48px)] max-w-[540px] px-2 py-1 rounded-full bg-white [box-shadow:var(--nav-shadow)]"
          aria-label="Primary"
        >
          {NAV_ITEMS.map(({ id, label }) => {
            const isActive = activeId === id
            return (
              <a
                key={id}
                href={`#${id}`}
                onClick={() => handleSelectNav(id)}
                className={`relative font-sans-ui font-medium text-[clamp(12px,1.25vw,14px)] tracking-[-0.01em] text-[var(--nav-text)] px-2.5 py-2 whitespace-nowrap transition-opacity duration-200 ${
                  isActive
                    ? 'opacity-100 active-nav-dot'
                    : 'opacity-50 hover:opacity-75'
                }`}
              >
                {label}
              </a>
            )
          })}
        </nav>

        {/* Desktop Launch App */}
        <Link
          to="/agent"
          className="hidden md:inline-flex shrink-0 items-center justify-center h-[clamp(44px,5.2vw,48px)] px-5 rounded-full bg-[var(--pill-dark)] text-[var(--sign-in-text)] font-medium text-[clamp(13px,1.4vw,15px)] tracking-[-0.01em] [box-shadow:var(--nav-shadow)] transition-all duration-200 hover:bg-[#323234] hover:text-white hover:-translate-y-px"
        >
          Launch App
        </Link>

        {/* Mobile Burger Button */}
        <button
          type="button"
          aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileMenuOpen}
          aria-controls="mobile-menu"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className={`md:hidden relative shrink-0 w-12 h-12 rounded-full grid place-items-center z-4 transition-colors duration-200 ${
            mobileMenuOpen ? 'bg-white' : 'bg-[#28282a]'
          }`}
        >
          <span
            className={`absolute left-1/2 w-[18px] h-[1.5px] -ml-[9px] rounded-sm transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              mobileMenuOpen
                ? 'bg-black translate-y-0 rotate-45'
                : 'bg-white -translate-y-[6.5px]'
            }`}
          />
          <span
            className={`absolute left-1/2 w-[18px] h-[1.5px] -ml-[9px] rounded-sm transition-all duration-200 ${
              mobileMenuOpen ? 'bg-black opacity-0' : 'bg-white opacity-100'
            }`}
          />
          <span
            className={`absolute left-1/2 w-[18px] h-[1.5px] -ml-[9px] rounded-sm transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              mobileMenuOpen
                ? 'bg-black translate-y-0 -rotate-45'
                : 'bg-white translate-y-[6.5px]'
            }`}
          />
        </button>
      </header>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-[41] bg-black/62 backdrop-blur-md anim-overlay"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sheet Menu */}
      {mobileMenuOpen && (
        <nav
          id="mobile-menu"
          aria-label="Mobile"
          className="fixed z-[42] top-[88px] left-1/2 -translate-x-1/2 w-[min(420px,calc(100vw-28px))] flex flex-col items-stretch gap-1 p-[22px_18px_20px] rounded-[28px] bg-white shadow-[0_20px_60px_rgba(0,0,0,0.45)] anim-menu"
        >
          {NAV_ITEMS.map(({ id, label }, index) => {
            const isActive = activeId === id
            return (
              <a
                key={id}
                href={`#${id}`}
                onClick={() => handleSelectNav(id)}
                style={{ animationDelay: `${0.08 + index * 0.06}s` }}
                className={`anim-link relative flex items-center justify-center min-h-[46px] font-medium text-[16px] text-[var(--nav-text)] ${
                  isActive ? 'active-mobile-dot font-semibold' : ''
                }`}
              >
                {label}
              </a>
            )
          })}
          <Link
            to="/agent"
            onClick={() => setMobileMenuOpen(false)}
            style={{ animationDelay: '0.38s' }}
            className="anim-link flex items-center justify-center mt-2 rounded-full bg-[var(--pill-dark)] text-[var(--sign-in-text)] font-medium text-[16px] min-h-[48px]"
          >
            Launch App
          </Link>
        </nav>
      )}
    </>
  )
}
