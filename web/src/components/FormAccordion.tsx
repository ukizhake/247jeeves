import { useId, useState, type ReactNode } from 'react'

type Accent = 'emerald' | 'amber' | 'sky'

const ACCENT_STYLES: Record<
  Accent,
  { shell: string; left: string; header: string; headerHover: string; toggle: string; panel: string }
> = {
  emerald: {
    shell: 'border-emerald-800/70 bg-emerald-950/25',
    left: 'border-l-emerald-500',
    header: 'text-emerald-200',
    headerHover: 'hover:bg-emerald-950/50',
    toggle: 'border-emerald-700/60 bg-emerald-950/60 text-emerald-300',
    panel: 'border-emerald-800/50 bg-emerald-950/15',
  },
  amber: {
    shell: 'border-amber-800/70 bg-amber-950/25',
    left: 'border-l-amber-500',
    header: 'text-amber-200',
    headerHover: 'hover:bg-amber-950/50',
    toggle: 'border-amber-700/60 bg-amber-950/60 text-amber-300',
    panel: 'border-amber-800/50 bg-amber-950/15',
  },
  sky: {
    shell: 'border-sky-800/70 bg-sky-950/25',
    left: 'border-l-sky-500',
    header: 'text-sky-200',
    headerHover: 'hover:bg-sky-950/50',
    toggle: 'border-sky-700/60 bg-sky-950/60 text-sky-300',
    panel: 'border-sky-800/50 bg-sky-950/15',
  },
}

interface Props {
  title: string
  accent: Accent
  debugSuffix?: string
  debug?: boolean
  children: ReactNode
}

export function FormAccordion({ title, accent, debugSuffix, debug, children }: Props) {
  const [open, setOpen] = useState(false)
  const panelId = useId()
  const label = debug && debugSuffix ? `${title} ${debugSuffix}` : title
  const styles = ACCENT_STYLES[accent]

  return (
    <div
      className={`sm:col-span-2 overflow-hidden rounded-lg border border-l-4 shadow-sm ${styles.shell} ${styles.left}`}
    >
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className={`flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3.5 text-left text-sm font-semibold ${styles.header} ${styles.headerHover}`}
      >
        <span>{label}</span>
        <span
          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md border text-xs font-bold ${styles.toggle}`}
          aria-hidden
        >
          {open ? '−' : '+'}
        </span>
      </button>
      {open && (
        <div
          id={panelId}
          className={`grid gap-4 border-t p-4 sm:grid-cols-2 ${styles.panel}`}
        >
          {children}
        </div>
      )}
    </div>
  )
}
