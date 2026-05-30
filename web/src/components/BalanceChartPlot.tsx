import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js/dist/plotly.js'
import type { Data, Layout } from 'plotly.js'
import type { YearState } from '../types'

function buildChart(years: YearState[]): { data: Data[]; layout: Partial<Layout> } {
  return {
    data: [
      {
        x: years.map((y) => y.age),
        y: years.map((y) => y.traditional_ira),
        name: 'Traditional IRA',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#f59e0b' },
      },
      {
        x: years.map((y) => y.age),
        y: years.map((y) => y.roth_ira),
        name: 'Roth IRA',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#34d399' },
      },
      {
        x: years.map((y) => y.age),
        y: years.map((y) => y.taxable),
        name: 'Taxable',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#60a5fa' },
      },
    ],
    layout: {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#cbd5e1' },
      margin: { t: 24, r: 16, b: 48, l: 56 },
      xaxis: { title: { text: 'Age' }, gridcolor: '#334155' },
      yaxis: { title: { text: 'Balance ($)' }, tickformat: '$,.0f', gridcolor: '#334155' },
      legend: { orientation: 'h', y: 1.12 },
      height: 320,
    },
  }
}

export function BalanceChartPlot({ years }: { years: YearState[] }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el || years.length === 0) return

    const { data, layout } = buildChart(years)
    let cancelled = false

    Plotly.newPlot(el, data, layout, {
      displayModeBar: false,
      responsive: true,
    }).then(() => {
      if (cancelled) Plotly.purge(el)
    })

    const onResize = () => {
      if (containerRef.current) Plotly.Plots.resize(containerRef.current)
    }
    window.addEventListener('resize', onResize)

    return () => {
      cancelled = true
      window.removeEventListener('resize', onResize)
      Plotly.purge(el)
    }
  }, [years])

  return <div ref={containerRef} className="w-full min-h-[320px]" />
}
