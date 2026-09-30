import React, { useState } from 'react'
import BackgroundVideo from '../components/BackgroundVideo'
import Navbar from '../components/Navbar'
import HeroSection from '../components/HeroSection'
import StatsFooter from '../components/StatsFooter'

export default function LandingPage() {
  const [activeNav, setActiveNav] = useState('Home')

  return (
    <div className="relative min-h-screen bg-black text-white overflow-hidden select-none">
      {/* Full-bleed looping background video */}
      <BackgroundVideo />

      {/* Single viewport page container */}
      <div className="relative z-1 flex flex-col items-center justify-between h-screen h-[100dvh] overflow-hidden px-[clamp(14px,3vw,32px)] py-[clamp(16px,2.4vh,28px)]">
        <Navbar activeNav={activeNav} onNavChange={setActiveNav} />
        <HeroSection />
        <StatsFooter />
      </div>
    </div>
  )
}
