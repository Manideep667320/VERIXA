interface VerixaLogoProps {
  size?: number
  showWordmark?: boolean
  showMark?: boolean
  className?: string
}

export default function VerixaLogo({
  size = 24,
  showWordmark = true,
  showMark = true,
  className = '',
}: VerixaLogoProps) {
  return (
    <div className={`flex items-center gap-1.5 select-none ${className}`}>
      {/* Freestanding Architectural Swiss Monogram V */}
      {showMark && (
        <svg
          viewBox="0 0 100 100"
          className="shrink-0 transition-opacity duration-200 group-hover:opacity-85"
          style={{ width: size, height: size }}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <polygon
            points="16,20 32,20 50,52.8 68,20 84,20 50,82"
            fill="#FFFFFF"
          />
        </svg>
      )}

      {/* Pure Swiss Geometric Wordmark (Continues from V mark into ERIXA) */}
      {showWordmark && (
        <span className="font-sans font-bold tracking-[0.22em] text-[16px] md:text-[17px] uppercase leading-none text-white transition-opacity duration-200 group-hover:opacity-85">
          {showMark ? 'ERIXA' : 'VERIXA'}
        </span>
      )}
    </div>
  )
}
