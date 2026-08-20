/** Páginas de auth: usuário já logado vai para o dashboard (ux-spec §2). */
export default defineNuxtRouteMiddleware(() => {
  const session = useSupabaseSession()
  if (session.value) return navigateTo('/')
})
