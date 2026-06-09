import type { ReactNode } from 'react'

export type IconName =
  | 'analysis'
  | 'check'
  | 'document'
  | 'lock'
  | 'roadmap'
  | 'upload'
  | 'warning'

const paths: Record<IconName, ReactNode> = {
  upload: (
    <>
      <path d="M12 16V4" />
      <path d="m7 9 5-5 5 5" />
      <path d="M5 15v4a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-4" />
    </>
  ),
  document: (
    <>
      <path d="M7 3h7l4 4v14H7z" />
      <path d="M14 3v5h4" />
      <path d="M10 13h5M10 17h5" />
    </>
  ),
  analysis: (
    <>
      <path d="M4 19V9M10 19V5M16 19v-7M22 19V3" />
      <path d="M2 19h22" />
    </>
  ),
  lock: (
    <>
      <rect x="5" y="10" width="14" height="11" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </>
  ),
  check: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12 2.5 2.5L16 9" />
    </>
  ),
  warning: (
    <>
      <path d="M12 3 2.5 20h19z" />
      <path d="M12 9v5M12 17.5v.1" />
    </>
  ),
  roadmap: (
    <>
      <circle cx="6" cy="18" r="2" />
      <circle cx="18" cy="6" r="2" />
      <path d="M8 18h3a3 3 0 0 0 3-3V9a3 3 0 0 1 3-3" />
    </>
  ),
}

export function Icon({
  name,
  size = 20,
}: {
  name: IconName
  size?: number
}) {
  return (
    <svg
      aria-hidden="true"
      className="icon"
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
    >
      <g
        stroke="currentColor"
        strokeLinecap="square"
        strokeLinejoin="miter"
        strokeWidth="1.5"
      >
        {paths[name]}
      </g>
    </svg>
  )
}
