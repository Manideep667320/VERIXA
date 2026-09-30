import BackgroundVideo from '../components/BackgroundVideo'
import Navbar from '../components/Navbar'
import HeroSection from '../components/HeroSection'
import PipelineSection from '../components/PipelineSection'
import OutcomesSection from '../components/OutcomesSection'
import GuardrailsBand from '../components/GuardrailsBand'
import AuditTrailSection from '../components/AuditTrailSection'
import ClosingCTA from '../components/ClosingCTA'

export default function LandingPage() {
  return (
    <div className="relative bg-black text-white">
      <Navbar />

      {/* Locked single-viewport hero */}
      <section id="home" className="relative h-screen h-[100dvh] overflow-hidden">
        <BackgroundVideo />
        <div className="relative z-1 flex flex-col items-center justify-center h-full px-[clamp(14px,3vw,32px)] pt-[clamp(96px,14vh,120px)] pb-[clamp(16px,2.4vh,28px)]">
          <HeroSection />
        </div>
      </section>

      {/* Scrollable content below the fold */}
      <PipelineSection />
      <OutcomesSection />
      <GuardrailsBand />
      <AuditTrailSection />
      <ClosingCTA />
    </div>
  )
}
