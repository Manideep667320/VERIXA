import React, { useEffect, useState } from 'react'

const NAV_ITEMS = ['Home', 'Product', 'Case Studies', 'Contact']

interface NavbarProps {
  activeNav?: string
  onNavChange?: (nav: string) => void
}

export default function Navbar({
  activeNav = 'Home',
  onNavChange,
}: NavbarProps) {
  const [currentNav, setCurrentNav] = useState(activeNav)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleSelectNav = (item: string) => {
    setCurrentNav(item)
    onNavChange?.(item)
    setMobileMenuOpen(false)
  }

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
      <header className="shrink-0 z-1 flex items-center justify-between md:justify-center w-full max-w-[720px] gap-[clamp(18px,2.8vw,28px)] anim-slide-down">
        {/* Logo */}
        <a
          href="#home"
          aria-label="Home"
          className="shrink-0 w-[48px] h-[48px] md:w-[clamp(40px,4.4vw,46px)] md:h-[clamp(40px,4.4vw,46px)] rounded-full bg-white [box-shadow:var(--nav-shadow)] grid place-items-center overflow-hidden border-[1.5px] border-white transition-transform duration-[280ms] ease-[cubic-bezier(0.22,1,0.36,1)] hover:scale-[1.04]"
        >
          <img
            src="/assets/logo.webp"
            alt=""
            width={52}
            height={52}
            className="w-[72%] h-[72%] object-contain"
          />
        </a>

        {/* Desktop Nav Pill */}
        <nav
          className="hidden md:flex flex-1 items-center justify-evenly h-[clamp(44px,5.2vw,48px)] max-w-[430px] px-2 py-1 rounded-full bg-white [box-shadow:var(--nav-shadow)]"
          aria-label="Primary"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = currentNav === item
            return (
              <a
                key={item}
                href={`#${item.toLowerCase().replace(/\s+/g, '-')}`}
                onClick={() => handleSelectNav(item)}
                className={`relative font-sans-ui font-medium text-[clamp(13px,1.4vw,15px)] tracking-[-0.01em] text-[var(--nav-text)] px-2.5 py-2 transition-opacity duration-200 ${
                  isActive
                    ? 'opacity-100 active-nav-dot'
                    : 'opacity-50 hover:opacity-75'
                }`}
              >
                {item}
              </a>
            )
          })}
        </nav>

        {/* Desktop Sign In */}
        <a
          href="#sign-in"
          className="hidden md:inline-flex shrink-0 items-center justify-center h-[clamp(44px,5.2vw,48px)] px-5 rounded-full bg-[var(--pill-dark)] text-[var(--sign-in-text)] font-medium text-[clamp(13px,1.4vw,15px)] tracking-[-0.01em] [box-shadow:var(--nav-shadow)] transition-all duration-200 hover:bg-[#323234] hover:text-white hover:-translate-y-px"
        >
          Sign in
        </a>

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
          className="fixed inset-0 z-2 bg-black/62 backdrop-blur-md anim-overlay"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sheet Menu */}
      {mobileMenuOpen && (
        <nav
          id="mobile-menu"
          aria-label="Mobile"
          className="fixed z-3 top-[88px] left-1/2 -translate-x-1/2 w-[min(420px,calc(100vw-28px))] flex flex-col items-stretch gap-1 p-[22px_18px_20px] rounded-[28px] bg-white shadow-[0_20px_60px_rgba(0,0,0,0.45)] anim-menu"
        >
          {NAV_ITEMS.map((item, index) => {
            const isActive = currentNav === item
            return (
              <a
                key={item}
                href={`#${item.toLowerCase().replace(/\s+/g, '-')}`}
                onClick={() => handleSelectNav(item)}
                style={{ animationDelay: `${0.08 + index * 0.06}s` }}
                className={`anim-link relative flex items-center justify-center min-h-[46px] font-medium text-[16px] text-[var(--nav-text)] ${
                  isActive ? 'active-mobile-dot font-semibold' : ''
                }`}
              >
                {item}
              </a>
            )
          })}
          <a
            href="#sign-in"
            onClick={() => setMobileMenuOpen(false)}
            style={{ animationDelay: '0.32s' }}
            className="anim-link flex items-center justify-center mt-2 rounded-full bg-[var(--pill-dark)] text-[var(--sign-in-text)] font-medium text-[16px] min-h-[48px]"
          >
            Sign in
          </a>
        </nav>
      )}
    </>
  )
}
