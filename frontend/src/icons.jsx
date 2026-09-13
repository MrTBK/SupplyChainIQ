import React from 'react'

// Hand-drawn geometric icon set (stroke 1.8, round caps, currentColor).
// Zero dependencies, no emoji. Status/illustration icons arrive in F3.
const PATHS = {
  grid: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></>,
  box: <><path d="M12 3 4.5 7.5v9L12 21l7.5-4.5v-9L12 3Z" /><path d="M4.5 7.5 12 12l7.5-4.5M12 12v9" /></>,
  users: <><circle cx="9" cy="8" r="3.2" /><path d="M3.5 19c.6-3 2.8-4.5 5.5-4.5S13.9 16 14.5 19" /><circle cx="16.5" cy="9" r="2.4" /><path d="M15.5 14.6c2.3.2 4 1.6 4.5 4" /></>,
  truck: <><path d="M2.5 6.5h11v10h-11zM13.5 10.5h4l3 3.5v2.5h-7" /><circle cx="7" cy="18" r="1.8" /><circle cx="17" cy="18" r="1.8" /></>,
  chart: <><path d="M4 4v15.5h16" /><path d="M7.5 14.5l3.5-4 2.5 2.5 4.5-5.5" /></>,
  alert: <><path d="M12 3.5 2.8 19.5h18.4L12 3.5Z" /><path d="M12 9.5v4.5" /><circle cx="12" cy="16.8" r="0.4" /></>,
  bulb: <><path d="M12 3.5a5.5 5.5 0 0 0-3.2 10c.8.6 1.2 1.3 1.2 2.2h4c0-.9.4-1.6 1.2-2.2A5.5 5.5 0 0 0 12 3.5Z" /><path d="M10 19.5h4M10.8 21.5h2.4" /></>,
  database: <><ellipse cx="12" cy="5.5" rx="7.5" ry="2.5" /><path d="M4.5 5.5v13c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5v-13" /><path d="M4.5 12c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5" /></>,
  pulse: <><path d="M3 12h4l2.5-6 4 12 2.5-6H21" /></>,
  shield: <><path d="M12 3 5 5.8v5.4c0 4.4 2.9 7.4 7 9.3 4.1-1.9 7-4.9 7-9.3V5.8L12 3Z" /><path d="m9 11.5 2.2 2.2L15.5 9.5" /></>,
  bell: <><path d="M6 9.5a6 6 0 0 1 12 0c0 4 1.5 5.5 1.5 5.5h-15S6 13.5 6 9.5" /><path d="M10 18.5a2.2 2.2 0 0 0 4 0" /></>,
  key: <><circle cx="8.5" cy="12" r="4.5" /><path d="M13 12h8M18 12v4M15.5 12v2.5" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  collapse: <><path d="m14 7-5 5 5 5" /></>,
  search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></>,
  logout: <><path d="M14 4H6v16h8" /><path d="m10 12 7 0M15 8.5 18.5 12 15 15.5" /></>,
  user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 20c.8-3.6 3.4-5.2 7-5.2s6.2 1.6 7 5.2" /></>,
  check: <><path d="m5 12.5 4.5 4.5L19 7.5" /></>,
  x: <><path d="M6 6l12 12M18 6 6 18" /></>,
}

export default function Icon({ name, size = 18, label }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : true}
      role={label ? 'img' : undefined}
      aria-label={label}
      style={{ flexShrink: 0, verticalAlign: '-3px' }}
    >
      {PATHS[name] || PATHS.grid}
    </svg>
  )
}

export function BrandMark({ size = 30 }) {
  return (
    <span className="sci-brand-mark" style={{ width: size, height: size }} aria-hidden="true">
      <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3 4.5 7.5v9L12 21l7.5-4.5v-9L12 3Z" />
        <path d="M4.5 7.5 12 12l7.5-4.5M12 12v9" />
      </svg>
    </span>
  )
}
