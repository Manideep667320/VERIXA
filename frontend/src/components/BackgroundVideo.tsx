import React from 'react'

const EXACT_VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260809_012548_ef22562c-c0ae-4816-ad9d-f8922af4e6a7.mp4'

export default function BackgroundVideo() {
  return (
    <div className="absolute inset-0 bg-black overflow-hidden z-0 pointer-events-none">
      <video
        className="absolute inset-0 w-full h-full object-cover pointer-events-none z-0"
        autoPlay
        muted
        loop
        playsInline
      >
        <source src={EXACT_VIDEO_URL} type="video/mp4" />
      </video>
    </div>
  )
}
