import { lazy, Suspense } from 'react'
import type { YearState } from '../types'

const BalanceChartPlot = lazy(() =>
  import('./BalanceChartPlot').then((m) => ({ default: m.BalanceChartPlot })),
)

export function BalanceChart({ years }: { years: YearState[] }) {
  return (
    <Suspense
      fallback={
        <div
          className="flex h-80 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/50 text-sm text-slate-500"
          aria-busy
        >
          Loading chart…
        </div>
      }
    >
      <BalanceChartPlot years={years} />
    </Suspense>
  )
}
