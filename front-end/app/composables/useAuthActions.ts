/**
 * Ações de auth contra o Supabase com as mensagens exatas da ux-spec §3.
 * Regra: nunca revelar se um e-mail existe; erros de credencial são sempre genéricos.
 */

export interface AuthResult {
  ok: boolean
  /** Mensagem genérica para exibir (quando ok=false) ou informativa (ok=true). */
  message?: string
  /** Dica discreta adicional (ex.: e-mail não confirmado) — nunca confirma existência. */
  hint?: string
}

export const AUTH_COPY = {
  invalidCredentials: 'E-mail ou senha inválidos.',
  unconfirmedHint: 'Se você acabou de se cadastrar, confirme o e-mail pelo link que enviamos.',
  loginNetwork: 'Não foi possível entrar agora. Tente novamente em alguns segundos.',
  signupNetwork: 'Não foi possível criar a conta agora. Tente novamente.',
  signupSent: (email: string) => `Se este e-mail for novo, enviamos um link de confirmação para ${email}. O link vale por 24 horas.`,
  resendSent: 'Se este e-mail for novo, enviamos outro link.',
  forgotSent: 'Se existir uma conta com este e-mail, você receberá um link em instantes.',
  forgotNetwork: 'Não foi possível enviar o link agora. Tente novamente.',
  passwordUpdated: 'Senha atualizada. Você já está conectado.',
  passwordUpdateFailed: 'Não foi possível salvar a nova senha. O link pode ter expirado — peça um novo.',
  sessionExpired: 'Sua sessão expirou. Entre de novo para continuar — você voltará para onde estava.',
  confirmFailed: 'Não foi possível confirmar o link. Ele pode ter expirado — entre ou peça um novo.',
  emailConfirmed: 'E-mail confirmado. Bem-vindo.',
} as const

function isNetworkError(error: { status?: number, message?: string } | null | undefined): boolean {
  if (!error) return false
  if (error.status === 0 || error.status === undefined) return /fetch|network|Failed to fetch/i.test(error.message ?? '')
  return error.status >= 500
}

export function useAuthActions() {
  const supabase = useSupabaseClient()

  const origin = () => (import.meta.client ? window.location.origin : '')

  async function signIn(email: string, password: string): Promise<AuthResult> {
    const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password })
    if (!error) return { ok: true }
    if (isNetworkError(error)) return { ok: false, message: AUTH_COPY.loginNetwork }
    const unconfirmed = /not confirmed/i.test(error.message ?? '')
    return { ok: false, message: AUTH_COPY.invalidCredentials, hint: unconfirmed ? AUTH_COPY.unconfirmedHint : undefined }
  }

  async function signUp(email: string, password: string): Promise<AuthResult> {
    const { error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: { emailRedirectTo: `${origin()}/confirm` },
    })
    // E-mail já existente: o Supabase devolve um usuário "fake" sem erro → mesma mensagem genérica.
    if (!error) return { ok: true, message: AUTH_COPY.signupSent(email.trim()) }
    if (isNetworkError(error)) return { ok: false, message: AUTH_COPY.signupNetwork }
    // Erros de validação (senha fraca etc.) são os únicos que mostramos literalmente? Não: genérico + hint.
    return { ok: false, message: AUTH_COPY.signupNetwork, hint: error.message }
  }

  async function resendConfirmation(email: string): Promise<AuthResult> {
    await supabase.auth.resend({ type: 'signup', email: email.trim(), options: { emailRedirectTo: `${origin()}/confirm` } })
    // Resposta idêntica exista ou não a conta.
    return { ok: true, message: AUTH_COPY.resendSent }
  }

  async function forgotPassword(email: string): Promise<AuthResult> {
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), { redirectTo: `${origin()}/reset-password` })
    if (error && isNetworkError(error)) return { ok: false, message: AUTH_COPY.forgotNetwork }
    return { ok: true, message: AUTH_COPY.forgotSent }
  }

  async function updatePassword(password: string): Promise<AuthResult> {
    const { error } = await supabase.auth.updateUser({ password })
    if (error) return { ok: false, message: AUTH_COPY.passwordUpdateFailed }
    return { ok: true, message: AUTH_COPY.passwordUpdated }
  }

  async function signOut(): Promise<void> {
    await supabase.auth.signOut()
    clearNuxtData()
    await navigateTo('/login')
  }

  return { signIn, signUp, resendConfirmation, forgotPassword, updatePassword, signOut }
}
