<script setup lang="ts">
import { maskBrPhoneInput } from '~/utils/phone'

/**
 * Preferências (Design.md §12.2): seções abertas separadas por macroespaço e
 * hairlines. Só os campos são superfícies — nenhuma seção recebe card.
 */
useHead({ title: 'Preferências · CRYPTO FORECASTING' })

const prefs = usePreferences()
const { form, fieldErrors } = prefs

const topics = [
  { key: 'forecast_gap' as const, label: 'Maiores gaps entre preço real e projeção', desc: 'Quando a previsão do modelo descolar mais de 3 % do preço' },
  { key: 'volume_movers' as const, label: 'Ativos com maior movimentação de volume diário', desc: 'Volume 24h muito acima da média de 7 dias' },
  { key: 'volatility' as const, label: 'Maior volatilidade diária de preço', desc: 'ATR relativo no topo do ranking dos 20 ativos' },
  { key: 'model_runs' as const, label: 'Novas rodadas do modelo', desc: 'Quando previsões e métricas forem recalculadas' },
]

function onPhoneInput() {
  form.phone = maskBrPhoneInput(form.phone)
}
</script>

<template>
  <div class="cf-gutter cf-shell pt-10 pb-16 md:pt-12 md:pb-24">
    <div>
      <h1 class="cf-h1 uppercase">
        Preferências
      </h1>
      <p class="mt-2.5 text-[15px] text-muted">
        Seus dados e o que você quer receber deste painel.
      </p>
    </div>

    <div
      v-if="prefs.status.value === 'pending' && !prefs.data.value"
      class="mt-16 space-y-6"
      role="status"
      aria-busy="true"
    >
      <span class="sr-only">Carregando as preferências…</span>
      <USkeleton class="h-5 w-48" />
      <USkeleton class="h-11 w-full max-w-[420px]" />
      <USkeleton class="h-11 w-full max-w-[420px]" />
      <USkeleton class="h-11 w-full max-w-[300px]" />
    </div>

    <ErrorState
      v-else-if="prefs.status.value === 'error' && !prefs.data.value"
      title="Não foi possível carregar as preferências"
      description="A API não respondeu. Tente de novo em alguns segundos."
      :retrying="false"
      @retry="prefs.refresh()"
    />

    <template v-else>
      <!-- Dados pessoais -->
      <section
        class="cf-hairline-b cf-section-tight grid gap-8 lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)] lg:gap-16"
        aria-labelledby="prefs-dados"
      >
        <div>
          <h2
            id="prefs-dados"
            class="cf-h2"
          >
            Dados pessoais
          </h2>
          <p class="mt-3 text-[14px] text-muted">
            Como o painel chama você e por onde podemos avisar.
          </p>
        </div>

        <div class="max-w-[460px] space-y-6">
          <UFormField
            label="Nome"
            size="lg"
            :error="fieldErrors.displayName ?? undefined"
          >
            <UInput
              v-model="form.displayName"
              autocomplete="name"
              :maxlength="120"
              placeholder="Como você quer ser chamado"
              class="w-full"
            />
          </UFormField>

          <UFormField
            label="E-mail"
            size="lg"
            help="O e-mail vem da sua conta e não muda por aqui."
          >
            <UInput
              :model-value="prefs.email.value ?? ''"
              readonly
              autocomplete="email"
              icon="i-lucide-mail"
              class="w-full"
              :ui="{ base: 'read-only:text-muted' }"
            />
          </UFormField>

          <UFormField
            label="Telefone celular"
            size="lg"
            help="O telefone só será usado para alertas por SMS ou WhatsApp, quando você ativar."
            :error="fieldErrors.phone ?? undefined"
          >
            <UInput
              v-model="form.phone"
              type="tel"
              autocomplete="tel"
              inputmode="tel"
              icon="i-lucide-phone"
              placeholder="(11) 91234-5678"
              class="w-full"
              @input="onPhoneInput"
            />
          </UFormField>
        </div>
      </section>

      <!-- Acessibilidade -->
      <section
        class="cf-hairline-b cf-section-tight grid gap-8 lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)] lg:gap-16"
        aria-labelledby="prefs-a11y"
      >
        <div>
          <h2
            id="prefs-a11y"
            class="cf-h2"
          >
            Acessibilidade
          </h2>
          <p class="mt-3 text-[14px] text-muted">
            Ajustes de leitura do gráfico.
          </p>
        </div>

        <div class="max-w-[460px]">
          <USwitch
            v-model="form.filledCandles"
            label="Velas de alta preenchidas"
            description="O padrão desenha a alta vazada, com contorno gelo. Preencher o corpo aumenta a área de cor."
          />
        </div>
      </section>

      <!-- Notificações -->
      <section
        class="cf-section-tight grid gap-8 lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)] lg:gap-16"
        aria-labelledby="prefs-notificacoes"
      >
        <div>
          <h2
            id="prefs-notificacoes"
            class="cf-h2"
          >
            Notificações
          </h2>
          <p class="mt-3 text-[14px] text-muted">
            Resumo diário com os tópicos que você escolher. Os alertas seguem o ritmo
            do pipeline (1x/dia). Nada é tempo real.
          </p>
        </div>

        <div class="max-w-[560px]">
          <USwitch
            v-model="form.notificationsEnabled"
            label="Receber o resumo diário"
          />

          <fieldset
            class="mt-7"
            :disabled="!form.notificationsEnabled"
            :class="form.notificationsEnabled ? '' : 'opacity-50'"
          >
            <legend class="eyebrow text-dimmed">
              Tópicos do resumo
            </legend>
            <div
              v-for="topic in topics"
              :key="topic.key"
              class="cf-rule py-4"
            >
              <UCheckbox
                v-model="form.topics[topic.key]"
                :label="topic.label"
                :description="topic.desc"
                :disabled="!form.notificationsEnabled"
              />
            </div>
          </fieldset>

          <div class="mt-8">
            <h3 class="eyebrow text-dimmed">
              Canal de envio
            </h3>
            <div class="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2">
              <span class="inline-flex items-center gap-2 text-[14px] text-ai">
                <UIcon
                  name="i-lucide-mail"
                  class="size-4"
                  aria-hidden="true"
                />E-mail
              </span>
              <span
                class="inline-flex items-center gap-2 text-[14px] text-dimmed"
                aria-disabled="true"
              >
                <UIcon
                  name="i-lucide-smartphone"
                  class="size-4"
                  aria-hidden="true"
                />SMS
                <span class="num text-[11px]">Em breve</span>
              </span>
              <span
                class="inline-flex items-center gap-2 text-[14px] text-dimmed"
                aria-disabled="true"
              >
                <UIcon
                  name="i-lucide-message-circle"
                  class="size-4"
                  aria-hidden="true"
                />WhatsApp
                <span class="num text-[11px]">Em breve</span>
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Ações -->
      <div class="cf-hairline-t flex flex-wrap items-center gap-x-4 gap-y-3 pt-6">
        <UButton
          size="lg"
          :loading="prefs.saving.value"
          :disabled="!prefs.dirty.value"
          label="Salvar alterações"
          @click="prefs.save()"
        />
        <UButton
          color="neutral"
          variant="ghost"
          size="lg"
          label="Descartar"
          :disabled="!prefs.dirty.value || prefs.saving.value"
          @click="prefs.refresh()"
        />
        <p
          class="text-[13px] text-dimmed"
          role="status"
        >
          {{ prefs.dirty.value ? 'Há alterações não salvas.' : 'Tudo salvo.' }}
        </p>
      </div>
    </template>
  </div>
</template>
