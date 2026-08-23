<script setup lang="ts">
import { maskBrPhoneInput } from '~/utils/phone'

useHead({ title: 'Preferências · crypto forecasting' })

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

function discard() {
  prefs.refresh()
}
</script>

<template>
  <div class="mx-auto max-w-[1080px] space-y-4">
    <div>
      <h1 class="text-[24px] font-bold tracking-[-.01em] text-highlighted">
        Preferências
      </h1>
      <p class="mt-1.5 text-[13px] text-muted">
        Seus dados e o que você quer receber deste painel.
      </p>
    </div>

    <div
      v-if="prefs.status.value === 'pending' && !prefs.data.value"
      class="grid gap-4 lg:grid-cols-2"
    >
      <div
        v-for="i in 2"
        :key="i"
        class="glass space-y-3 p-6"
      >
        <USkeleton class="h-4 w-40" />
        <USkeleton class="h-9 w-full" />
        <USkeleton class="h-9 w-full" />
        <USkeleton class="h-9 w-2/3" />
      </div>
    </div>

    <ErrorState
      v-else-if="prefs.status.value === 'error' && !prefs.data.value"
      title="Não foi possível carregar as preferências"
      description="Tente novamente em instantes."
      :retrying="false"
      @retry="prefs.refresh()"
    />

    <div
      v-else
      class="grid items-start gap-4 lg:grid-cols-[1fr_1.2fr]"
    >
      <!-- Dados pessoais + acessibilidade -->
      <section
        class="glass flex flex-col gap-4 p-6"
        aria-label="Dados pessoais"
      >
        <div class="flex items-center gap-2.5">
          <UIcon
            name="i-lucide-user"
            class="size-[18px] text-primary"
          />
          <h2 class="text-[15px] font-bold text-highlighted">
            Dados pessoais
          </h2>
        </div>

        <UFormField
          label="Nome"
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

        <UFormField label="E-mail">
          <UInput
            :model-value="prefs.email.value ?? ''"
            disabled
            icon="i-lucide-mail"
            class="w-full"
            :ui="{ base: 'disabled:opacity-70' }"
          />
          <template #help>
            O e-mail vem da sua conta e não muda por aqui.
          </template>
        </UFormField>

        <UFormField
          label="Telefone celular"
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
          <template #help>
            O telefone só será usado para alertas por SMS ou WhatsApp, quando você ativar.
          </template>
        </UFormField>

        <div class="flex gap-2">
          <UButton
            :class="prefs.dirty.value ? 'btn-glow' : ''"
            :loading="prefs.saving.value"
            :disabled="!prefs.dirty.value"
            label="Salvar alterações"
            @click="prefs.save()"
          />
          <UButton
            color="neutral"
            variant="ghost"
            label="Descartar"
            :disabled="!prefs.dirty.value || prefs.saving.value"
            @click="discard"
          />
        </div>

        <div class="flex flex-col gap-2 border-t border-[var(--cf-border-muted)] pt-3">
          <h3 class="font-medium text-highlighted">
            Acessibilidade
          </h3>
          <USwitch
            v-model="form.filledCandles"
            label="Velas de alta preenchidas"
            description="Preenche o corpo das velas de alta (padrão: vazadas, estilo vidro)"
          />
        </div>
      </section>

      <!-- Notificações -->
      <section
        class="glass flex flex-col p-6"
        aria-label="Notificações"
      >
        <div class="flex items-center justify-between gap-3 border-b border-default pb-3.5">
          <span class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-bell"
              class="size-[18px] text-primary"
            />
            <span>
              <span class="block text-[15px] font-bold text-highlighted">Notificações</span>
              <span class="text-[12.5px] text-muted">Resumo diário com os tópicos que você escolher</span>
            </span>
          </span>
          <USwitch
            v-model="form.notificationsEnabled"
            aria-label="Ativar notificações"
          />
        </div>

        <fieldset
          class="pt-1"
          :disabled="!form.notificationsEnabled"
        >
          <legend class="sr-only">
            Tópicos do resumo diário
          </legend>
          <div
            v-for="topic in topics"
            :key="topic.key"
            class="border-b border-[var(--cf-border-muted)] py-3 transition-opacity"
            :class="form.notificationsEnabled ? '' : 'opacity-50'"
          >
            <UCheckbox
              v-model="form.topics[topic.key]"
              :label="topic.label"
              :description="topic.desc"
              :disabled="!form.notificationsEnabled"
            />
          </div>
        </fieldset>

        <div class="mt-auto flex flex-col gap-2.5 pt-4">
          <h3 class="font-medium text-highlighted">
            Canal de envio
          </h3>
          <div class="flex flex-wrap gap-2">
            <span class="inline-flex h-8 items-center gap-1.5 rounded-full border border-[var(--cf-electric)] bg-primary-soft px-3 text-[12px] text-ai">
              <UIcon
                name="i-lucide-mail"
                class="size-3.5"
              />E-mail
            </span>
            <span
              class="inline-flex h-8 items-center gap-1.5 rounded-full border border-default px-3 text-[12px] text-muted opacity-70"
              aria-disabled="true"
            >
              <UIcon
                name="i-lucide-smartphone"
                class="size-3.5"
              />SMS
              <span class="eyebrow rounded-full border border-default px-1.5 py-px text-[10px]">Em breve</span>
            </span>
            <span
              class="inline-flex h-8 items-center gap-1.5 rounded-full border border-default px-3 text-[12px] text-muted opacity-70"
              aria-disabled="true"
            >
              <UIcon
                name="i-lucide-message-circle"
                class="size-3.5"
              />WhatsApp
              <span class="eyebrow rounded-full border border-default px-1.5 py-px text-[10px]">Em breve</span>
            </span>
          </div>
          <p class="text-[12.5px] text-muted">
            Os alertas seguem o ritmo do pipeline (1x/dia). Nada é tempo real.
          </p>
        </div>
      </section>
    </div>
  </div>
</template>
