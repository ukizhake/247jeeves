import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js/dist/plotly.js'
import type { Data, Layout } from 'plotly.js'
import type { MonteCarloResult } from '../types'

function buildFanChart(result: MonteCarloResult): { data: Data[]; layout: Partial<Layout> } {
  const ages = result.year_bands.map((b) => b.age)
  const p50 = result.year_bands.map((b) => b.p50)
  const p90 = result.year_bands.map((b) => b.p90)
  const p10 = result.year_bands.map((b) => b.p10)

  return {
    data: [
      {
        x: ages,
        y: p90,
        name: '90th %ile',
        type: 'scatter',
        mode: 'lines',
        line: { color: 'rgba(52, 211, 153, 0.35)', width: 0 },
        showlegend: false,
      },
      {
        x: ages,
        y: p10,
        name: '10th–90th band',
        type: 'scatter',
        mode: 'lines',
        fill: 'tonexty',
        fillcolor: 'rgba(52, 211, 153, 0.15)',
        line: { color: 'rgba(52, 211, 153, 0.35)', width: 0 },
      },
      {
        x: ages,
        y: p50,
        name: 'Median',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#34d399', width: 2.5 },
      },
    ],
    layout: {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#cbd5e1' },
      margin: { t: 24, r: 16, b: 48, l: 56 },
      xaxis: { title: { text: 'Age' }, gridcolor: '#334155' },
      yaxis: { title: { text: 'Total wealth ($)' }, tickformat: '$,.0f', gridcolor: '#334155' },
      legend: { orientation: 'h', y: 1.12 },
      height: 340,
      title: {
        text: `Monte Carlo · ${result.num_paths.toLocaleString()} paths · ${(result.mean_return * 100).toFixed(1)}% ± ${(result.return_volatility * 100).toFixed(0)}% vol`,
        font: { size: 13, color: '#94a3b8' },
      },
    },
  }
}

export function MonteCarloChart({ result }: { result: MonteCarloResult }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el || result.year_bands.length === 0) return

    const { data, layout } = buildFanChart(result)
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
  }, [result])

  return <div ref={containerRef} className="w-full min-h-[340px]" />
}
