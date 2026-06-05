import { useRef, useState } from 'react'
import { importFidelityCsv } from '../api/client'
import type { FidelityImportResult, Profile } from '../types'

interface Props {
  profile: Profile
  onApply: (profile: Profile) => void
  disabled?: boolean
  debug?: boolean
}

function money(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

const bucketLabel: Record<string, string> = {
  traditional_ira: 'Traditional',
  roth_ira: 'Roth',
  taxable: 'Taxable',
  cash: 'Cash',
  unknown: 'Unknown',
}

export function FidelityImport({ profile, onApply, disabled, debug = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<FidelityImportResult | null>(null)

  async function handleFile(file: File) {
    setLoading(true)
    setError(null)
    try {
      const result = await importFidelityCsv(file)
      setPreview(result)
    } catch (e) {
      setPreview(null)
      setError(e instanceof Error ? e.message : 'Import failed')
    } finally {
      setLoading(false)
    }
  }

  function applyToPlan() {
    if (!preview) return
    onApply({
      ...profile,
      accounts: {
        traditional_ira: preview.traditional_ira,
        roth_ira: preview.roth_ira,
        taxable: preview.taxable,
        cash: preview.cash,
      },
      taxable_cost_basis_ratio: preview.taxable_cost_basis_ratio,
    })
    setPreview(null)
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 sm:col-span-2">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-slate-200">Import from Fidelity</h3>
          <p className="mt-1 text-xs text-slate-500">
            Upload Portfolio Positions CSV from Fidelity — accounts map to Traditional, Roth,
            Taxable, and Cash (money market sweeps).
          </p>
        </div>
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            disabled={disabled || loading}
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) void handleFile(file)
              e.target.value = ''
            }}
          />
          <button
            type="button"
            disabled={disabled || loading}
            onClick={() => inputRef.current?.click()}
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? 'Parsing…' : 'Choose CSV'}
          </button>
          {preview && (
            <button
              type="button"
              disabled={disabled}
              onClick={applyToPlan}
              className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {debug ? 'Apply to plan' : 'Apply balances'}
            </button>
          )}
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

      {preview && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-300">
            <span>Total: {money(preview.total_value)}</span>
            {preview.as_of && <span className="text-slate-500">As of {preview.as_of}</span>}
            <span className="text-slate-500">{preview.position_count} positions</span>
          </div>
          <div className="grid gap-2 sm:grid-cols-4 text-sm">
            <div className="rounded-md bg-slate-800/80 px-3 py-2">
              <div className="text-xs text-slate-500">Traditional</div>
              <div className="font-medium">{money(preview.traditional_ira)}</div>
            </div>
            <div className="rounded-md bg-slate-800/80 px-3 py-2">
              <div className="text-xs text-slate-500">Roth</div>
              <div className="font-medium">{money(preview.roth_ira)}</div>
            </div>
            <div className="rounded-md bg-slate-800/80 px-3 py-2">
              <div className="text-xs text-slate-500">Taxable</div>
              <div className="font-medium">{money(preview.taxable)}</div>
            </div>
            <div className="rounded-md bg-slate-800/80 px-3 py-2">
              <div className="text-xs text-slate-500">Cash sweep</div>
              <div className="font-medium">{money(preview.cash)}</div>
            </div>
          </div>
          <p className="text-xs text-slate-500">
            Taxable cost basis ratio: {(preview.taxable_cost_basis_ratio * 100).toFixed(1)}% (used
            for withdrawal gain estimates)
          </p>
          <details className="text-sm">
            <summary className="cursor-pointer text-slate-400 hover:text-slate-200">
              {preview.accounts.length} Fidelity accounts
            </summary>
            <ul className="mt-2 space-y-1 text-xs text-slate-400">
              {preview.accounts.map((a) => (
                <li key={a.account_number} className="flex justify-between gap-4">
                  <span>
                    {a.account_name}{' '}
                    <span className="text-slate-600">({bucketLabel[a.bucket] ?? a.bucket})</span>
                  </span>
                  <span className="tabular-nums">{money(a.total_value)}</span>
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  )
}
