import type { ReactNode } from 'react'
import { FORM_ACCENT_STYLES, type FormAccent } from './formAccents'

interface Props {
  title: string
  accent: FormAccent
  debugSuffix?: string
  debug?: boolean
  children: ReactNode
}

export function FormSection({ title, accent, debugSuffix, debug, children }: Props) {
  const label = debug && debugSuffix ? `${title} ${debugSuffix}` : title
  const styles = FORM_ACCENT_STYLES[accent]

  return (
    <div
      className={`sm:col-span-2 overflow-hidden rounded-lg border border-l-4 shadow-sm ${styles.shell} ${styles.left}`}
    >
      <div className={`px-4 py-3.5 text-sm font-semibold ${styles.header}`}>{label}</div>
      <div className={`grid gap-4 border-t p-4 sm:grid-cols-2 ${styles.panel}`}>{children}</div>
    </div>
  )
}
