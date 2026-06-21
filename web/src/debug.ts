/** ?debug=1 in the URL or VITE_DEBUG=true at build time */
export function isDebugMode(): boolean {
  if (import.meta.env.VITE_DEBUG === 'true') return true
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).get('debug') === '1'
}

/** Strip book/deck/slide/chapter references from engine copy in production UI. */
export function publicText(text: string | undefined, debug: boolean): string {
  if (!text) return ''
  if (debug) return text

  let t = text

  // [Richer Retirement slides 26, 39] and similar bracket citations
  t = t.replace(/\s*\[[^\]]*(?:Richer Retirement|Principle|slide|Ch\.?\s*\d+)[^\]]*\]/gi, '')

  // (Ch. 8), (Principle 3 caveat), (Richer Retirement …)
  t = t.replace(
    /\s*\([^)]*(?:Richer Retirement|Principle\s+\d+|Ch\.?\s*\d+|slide\s*\d+)[^)]*\)/gi,
    '',
  )

  // Whole "Richer Retirement …" citation prefixes (allow periods in "Ch.")
  t = t.replace(/\bRicher Retirement\s+Ch\.?\s*\d+\s*[—–-]\s*/gi, '')
  t = t.replace(/\bRicher Retirement\s*[—–-]\s*/gi, '')
  t = t.replace(/\bRicher Retirement\b/gi, '')

  // Trailing / inline chapter refs: ", Ch. 13" or " (Ch. 12)"
  t = t.replace(/,?\s*Ch\.?\s*\d+(\s*\/\s*slide\s*\d+)?/gi, '')

  // Principle N (with optional "caveat")
  t = t.replace(/\s*\(Principle\s+\d+[^)]*\)/gi, '')
  t = t.replace(/\bPrinciple\s+\d+(\s+caveat)?/gi, '')

  // Rule number refs: #46 (Principle …) / Larry example
  t = t.replace(/\s*#\d+[^.[\n]*/gi, '')

  // Book / deck terminology
  t = t.replace(/\bBook FA\b/gi, 'Fixed nominal spending')
  t = t.replace(/\bbook FA\b/g, 'fixed nominal spending')
  t = t.replace(/\bDeck FA\b/gi, 'Fixed nominal spending')
  t = t.replace(/\bdeck FA\b/gi, 'fixed nominal spending')
  t = t.replace(/\bin the deck\b/gi, 'historically')
  t = t.replace(/\bdeck\b/gi, 'historical')
  t = t.replace(/\bDeck\b/g, 'Default')

  // Orphan punctuation and whitespace
  t = t.replace(/\s*[—–-]\s*$/g, '')
  t = t.replace(/\s+([,.;])/g, '$1')
  t = t.replace(/\s{2,}/g, ' ')
  return t.trim()
}
