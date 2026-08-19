// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  {
    // Gerado por `pnpm api:types` — nunca editar/lintar à mão.
    ignores: ['app/types/openapi.d.ts', 'openapi/**'],
  },
)
