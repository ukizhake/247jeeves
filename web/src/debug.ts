/** ?debug=1 in the URL or VITE_DEBUG=true at build time */
export function isDebugMode(): boolean {
  if (import.meta.env.VITE_DEBUG === 'true') return true
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).get('debug') === '1'
}

/** Strip slide/deck parentheticals from engine copy in production UI. */
export function publicText(text: string | undefined, debug: boolean): string {
  if (!text) return ''
  if (debug) return text
  return text
    .replace(/\s*\([^)]*\bslides?\s*[^)]*\)/gi, '')
    .replace(/\s*\([^)]*\bdeck[^)]*\)/gi, '')
    .replace(/\s+/g, ' ')
    .trim()
}
