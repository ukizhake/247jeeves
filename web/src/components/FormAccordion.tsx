import { useId, useState, type ReactNode } from 'react'
import { FORM_ACCENT_STYLES, type FormAccent } from './formAccents'

interface Props {
  title: string
  accent: FormAccent
  debugSuffix?: string
  debug?: boolean
  children: ReactNode
}

export function FormAccordion({ title, accent, debugSuffix, debug, children }: Props) {
  const [open, setOpen] = useState(false)
  const panelId = useId()
  const label = debug && debugSuffix ? `${title} ${debugSuffix}` : title
  const styles = FORM_ACCENT_STYLES[accent]

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
