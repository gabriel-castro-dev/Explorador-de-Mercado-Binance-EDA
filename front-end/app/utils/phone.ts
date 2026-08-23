/**
 * Telefone BR: máscara de exibição ↔ E.164 (contrato da API: ^\+[1-9]\d{7,14}$).
 * Funções puras (testáveis sem Nuxt); sem dependência de máscara externa.
 */

export const E164_RE = /^\+[1-9]\d{7,14}$/

/**
 * Entrada digitada → E.164 ou null se inválida.
 * - Já em formato internacional (`+…`): valida direto.
 * - Só dígitos: assume Brasil — DDD + 8/9 dígitos → prefixa +55.
 * - `55…` com 12–13 dígitos também é aceito como BR completo.
 */
export function parsePhoneInput(raw: string): string | null {
  const trimmed = raw.trim()
  if (!trimmed) return null
  if (trimmed.startsWith('+')) {
    const candidate = `+${trimmed.slice(1).replace(/\D/g, '')}`
    return E164_RE.test(candidate) ? candidate : null
  }
  const digits = trimmed.replace(/\D/g, '')
  if (digits.length === 10 || digits.length === 11) {
    const candidate = `+55${digits}`
    return E164_RE.test(candidate) ? candidate : null
  }
  if (digits.startsWith('55') && (digits.length === 12 || digits.length === 13)) {
    const candidate = `+${digits}`
    return E164_RE.test(candidate) ? candidate : null
  }
  return null
}

/** E.164 BR → "(11) 91234-5678" para exibição; outros países ficam como estão. */
export function formatBrPhoneDisplay(e164: string | null | undefined): string {
  if (!e164) return ''
  const m = /^\+55(\d{2})(\d{8,9})$/.exec(e164)
  if (!m || !m[1] || !m[2]) return e164
  const [, ddd, rest] = m
  const split = rest.length - 4
  return `(${ddd}) ${rest.slice(0, split)}-${rest.slice(split)}`
}

/** Máscara ao digitar (só para entrada BR em dígitos): "(11) 91234-5678". */
export function maskBrPhoneInput(raw: string): string {
  if (raw.trim().startsWith('+')) return raw.trim()
  const digits = raw.replace(/\D/g, '').slice(0, 11)
  if (!digits.length) return ''
  if (digits.length <= 2) return `(${digits}`
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  const split = digits.length <= 10 ? 6 : 7
  return `(${digits.slice(0, 2)}) ${digits.slice(2, split)}-${digits.slice(split)}`
}
