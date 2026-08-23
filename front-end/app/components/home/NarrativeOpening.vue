<script setup lang="ts">
import type { DailyReading } from '~/types/api'
import type { AsyncStatus } from '~/utils/async-state'
import type { FreshnessState } from '~/composables/useFreshness'
import { splitReading } from '~/utils/insights'
import { formatUtc } from '~/utils/format'
import MarketDeltaLens from './MarketDeltaLens.vue'

/**
 * Abertura narrativa do Início (Design.md §9.1). Ordem obrigatória:
 * saudação → título contextual → último acesso → lente de mudança → LEITURA DO DIA →
 * manchete → explicação → snapshot.
 *
 * "Leitura do dia" é texto aberto: nunca recebe card.
 */
const props = defineProps<{
  firstName: string
  heading: string
  lastSeenIso: string | null
  reading: DailyReading | null
  readingStatus: AsyncStatus
  snapshotState: FreshnessState
  snapshotLabel: string
}>()

const emit = defineEmits<{ (e: 'retry'): void }>()

const reduced = useReducedMotion()

const parts = computed(() => splitReading(props.reading?.text))
const view = computed(() => {
  if (props.reading) return 'ready' as const
  if (props.readingStatus === 'pending' || props.readingStatus === 'idle') return 'loading' as const
  return 'empty' as const
})
</script>

<template>
  <section
    class="cf-stage cf-gutter cf-shell relative flex flex-col justify-center pt-10 pb-16 md:pt-14 md:pb-24"
    aria-labelledby="home-heading"
  >
    <HomeHeroLandscape />

    <!-- 1 · saudação · 2 · título contextual · 3 · último acesso -->
    <div class="max-w-[62ch]">
      <p
        v-reveal="{ delay: 0, y: 16 }"
        class="eyebrow text-[var(--cf-electric)]"
      >
        BEM-VINDO NOVAMENTE, {{ firstName.toUpperCase() }}
      </p>
      <h1
        id="home-heading"
        v-reveal="{ delay: 90, y: 20 }"
        class="mt-3 text-[20px] leading-[1.25] font-medium text-hi md:text-[24px]"
      >
        {{ props.heading }}
      </h1>
      <p
        v-if="props.lastSeenIso"
        v-reveal="{ delay: 160, y: 16 }"
        class="num mt-2.5 text-[13px] text-dimmed"
      >
        Último acesso em {{ formatUtc(props.lastSeenIso) }}
      </p>
    </div>

    <!-- 4 · lente de mudança · 5-8 · leitura do dia -->
    <div class="mt-12 grid gap-6 md:mt-16 lg:grid-cols-[minmax(0,300px)_minmax(0,1fr)] lg:gap-16 xl:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
      <div
        class="lg:self-start"
        :class="reduced ? '' : 'lg:sticky lg:top-[calc(var(--cf-header-h)+40px)]'"
      >
        <MarketDeltaLens v-reveal="{ delay: 240, y: 32 }" />
      </div>

      <div class="min-w-0">
        <p
          v-reveal="{ delay: 320, y: 18 }"
          class="eyebrow text-[var(--cf-electric)]"
        >
          LEITURA DO DIA
        </p>

        <!-- Loading: mantém a geometria final, sem shimmer contínuo -->
        <div
          v-if="view === 'loading'"
          class="mt-5 space-y-4"
          role="status"
          aria-busy="true"
        >
          <USkeleton class="h-[52px] w-[88%] rounded-md md:h-[68px]" />
          <USkeleton class="h-[52px] w-[64%] rounded-md md:h-[68px]" />
          <div class="mt-8 space-y-2.5">
            <USkeleton class="h-4 w-full max-w-[52ch]" />
            <USkeleton class="h-4 w-full max-w-[46ch]" />
            <USkeleton class="h-4 w-full max-w-[38ch]" />
          </div>
          <span class="sr-only">Carregando a leitura do dia…</span>
        </div>

        <!-- Vazio/erro: motivo provável + próxima ação, sem número inventado -->
        <div
          v-else-if="view === 'empty'"
          class="mt-5 max-w-[56ch]"
          role="status"
        >
          <p class="cf-h2">
            A leitura do dia ainda não saiu.
          </p>
          <p class="cf-body mt-4">
            O texto é gerado uma vez por dia, depois da coleta das 00:05 UTC. Os rankings
            abaixo continuam disponíveis com os dados do último snapshot.
          </p>
          <UButton
            class="mt-5"
            color="neutral"
            variant="outline"
            icon="i-lucide-refresh-cw"
            label="Tentar novamente"
            @click="emit('retry')"
          />
        </div>

        <template v-else-if="props.reading">
          <h2
            v-if="parts?.headline"
            v-reveal="{ delay: 400, y: 28 }"
            class="cf-display mt-5 uppercase"
          >
            {{ parts.headline }}
          </h2>
          <p
            v-if="parts?.body"
            v-reveal="{ delay: 480, y: 22 }"
            class="cf-body mt-7"
          >
            {{ parts.body }}
          </p>

          <div
            v-reveal="{ delay: 560, y: 16 }"
            class="mt-9 flex flex-wrap items-center gap-x-5 gap-y-2"
          >
            <SnapshotBadge
              prefix="SNAPSHOT"
              :state="props.snapshotState"
              :label="props.snapshotLabel"
            />
            <span class="num text-[11px] text-dimmed">
              leitura gerada {{ formatUtc(props.reading.generated_at) }}
            </span>
          </div>
          <p class="mt-4 max-w-[62ch] text-[13px] text-dimmed">
            {{ props.reading.disclaimer }}
          </p>
        </template>
      </div>
    </div>
  </section>
</template>
