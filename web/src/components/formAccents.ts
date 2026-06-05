export type FormAccent =
  | 'emerald'
  | 'amber'
  | 'sky'
  | 'violet'
  | 'teal'
  | 'indigo'
  | 'orange'
  | 'cyan'
  | 'fuchsia'

export const FORM_ACCENT_STYLES: Record<
  FormAccent,
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
  violet: {
    shell: 'border-violet-800/70 bg-violet-950/25',
    left: 'border-l-violet-500',
    header: 'text-violet-200',
    headerHover: 'hover:bg-violet-950/50',
    toggle: 'border-violet-700/60 bg-violet-950/60 text-violet-300',
    panel: 'border-violet-800/50 bg-violet-950/15',
  },
  teal: {
    shell: 'border-teal-800/70 bg-teal-950/25',
    left: 'border-l-teal-500',
    header: 'text-teal-200',
    headerHover: 'hover:bg-teal-950/50',
    toggle: 'border-teal-700/60 bg-teal-950/60 text-teal-300',
    panel: 'border-teal-800/50 bg-teal-950/15',
  },
  indigo: {
    shell: 'border-indigo-800/70 bg-indigo-950/25',
    left: 'border-l-indigo-500',
    header: 'text-indigo-200',
    headerHover: 'hover:bg-indigo-950/50',
    toggle: 'border-indigo-700/60 bg-indigo-950/60 text-indigo-300',
    panel: 'border-indigo-800/50 bg-indigo-950/15',
  },
  orange: {
    shell: 'border-orange-800/70 bg-orange-950/25',
    left: 'border-l-orange-500',
    header: 'text-orange-200',
    headerHover: 'hover:bg-orange-950/50',
    toggle: 'border-orange-700/60 bg-orange-950/60 text-orange-300',
    panel: 'border-orange-800/50 bg-orange-950/15',
  },
  cyan: {
    shell: 'border-cyan-800/70 bg-cyan-950/25',
    left: 'border-l-cyan-500',
    header: 'text-cyan-200',
    headerHover: 'hover:bg-cyan-950/50',
    toggle: 'border-cyan-700/60 bg-cyan-950/60 text-cyan-300',
    panel: 'border-cyan-800/50 bg-cyan-950/15',
  },
  fuchsia: {
    shell: 'border-fuchsia-800/70 bg-fuchsia-950/25',
    left: 'border-l-fuchsia-500',
    header: 'text-fuchsia-200',
    headerHover: 'hover:bg-fuchsia-950/50',
    toggle: 'border-fuchsia-700/60 bg-fuchsia-950/60 text-fuchsia-300',
    panel: 'border-fuchsia-800/50 bg-fuchsia-950/15',
  },
}
