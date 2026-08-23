<script setup lang="ts">
import { useDocumentVisibility, useMediaQuery } from '@vueuse/core'
import { prefersSavedData } from '~/utils/motion'

/**
 * Ambiente das telas de autenticação (Design.md §8).
 *
 * `immersive` (/login) toca o loop do **Abstract Quantum Probability Torus** —
 * WebM primeiro, MP4 H.264 como fallback, poster WebP derivado do mesmo frame.
 * O arquivo `-original.mp4` é só preservação em docs/ e nunca chega ao navegador.
 *
 * `quiet` (cadastro, confirmação, recuperação, redefinição) usa o torus estático
 * e mais discreto — poster apenas, sem vídeo.
 *
 * O vídeo não carrega em mobile, `saveData` ou redução de movimento: nesses casos
 * o poster é o estado final, não um degradê. Se o autoplay falhar, o poster fica.
 */
const props = withDefaults(defineProps<{ variant?: 'immersive' | 'quiet' }>(), { variant: 'immersive' })

const POSTER = '/media/login/torus-poster.webp'
/** Centro geométrico do torus em ~38% x 51% do quadro (Design.md §8.2). */
const FOCUS = '38% 51%'

const reduced = useReducedMotion()
const isNarrow = useMediaQuery('(max-width: 1023px)')
const visibility = useDocumentVisibility()

const videoEl = ref<HTMLVideoElement | null>(null)
const mounted = ref(false)
const saveData = ref(false)
const autoplayFailed = ref(false)

onMounted(() => {
  mounted.value = true
  saveData.value = prefersSavedData()
})

/** Só monta o `<video>` quando ele realmente pode e deve tocar. */
const wantsVideo = computed(() =>
  props.variant === 'immersive'
  && mounted.value
  && !reduced.value
  && !isNarrow.value
  && !saveData.value
  && !autoplayFailed.value,
)

async function play() {
  const el = videoEl.value
  if (!el) return
  try {
    await el.play()
  } catch {
    // Autoplay bloqueado pelo navegador: mantém o poster, sem controles nem erro visível.
    autoplayFailed.value = true
  }
}

watch(videoEl, el => void (el && play()))

watch(visibility, (state) => {
  const el = videoEl.value
  if (!el) return
  if (state === 'hidden') el.pause()
  else if (wantsVideo.value) void play()
})

const veilOpacity = computed(() => (props.variant === 'immersive' ? 1 : 0.45))
</script>

<template>
  <div
    class="pointer-events-none absolute inset-0 overflow-hidden"
    aria-hidden="true"
  >
    <!-- Poster: estado final em mobile/saveData/redução de movimento e fallback de autoplay. -->
    <div
      class="absolute inset-0 bg-cover bg-no-repeat"
      :style="{
        backgroundImage: `url('${POSTER}')`,
        backgroundPosition: FOCUS,
        opacity: props.variant === 'immersive' ? 1 : 0.5,
      }"
    />

    <video
      v-if="wantsVideo"
      ref="videoEl"
      class="absolute inset-0 size-full object-cover"
      :style="{ objectPosition: FOCUS }"
      :poster="POSTER"
      autoplay
      muted
      loop
      playsinline
      preload="metadata"
      disablepictureinpicture
      tabindex="-1"
      aria-hidden="true"
    >
      <source
        src="/media/login/torus-loop.webm"
        type="video/webm"
      >
      <source
        src="/media/login/torus-loop.mp4"
        type="video/mp4"
      >
    </video>

    <!-- Profundidade mineral por cima do frame: mantém pretos e evita chapa preta. -->
    <div
      class="absolute inset-0"
      style="background: radial-gradient(1100px 650px at 38% 51%, transparent, rgba(5, 8, 17, 0.55) 78%), linear-gradient(145deg, rgba(5, 8, 17, 0.35) 0%, rgba(8, 20, 38, 0.2) 55%, rgba(10, 23, 33, 0.45) 100%)"
    />

    <!--
      Véu tonal localizado atrás do formulário (Design.md §8.1): garante AA no terço
      direito sem emoldurar os campos. No mobile o véu cobre a tela inteira.
    -->
    <div
      class="absolute inset-0 lg:hidden"
      style="background: linear-gradient(180deg, rgba(5, 8, 17, 0.55) 0%, rgba(5, 8, 17, 0.86) 46%, rgba(5, 8, 17, 0.94) 100%)"
    />
    <div
      class="absolute inset-y-0 right-0 hidden w-[62%] lg:block"
      :style="{
        opacity: veilOpacity,
        background: 'linear-gradient(90deg, rgba(5,8,17,0) 0%, rgba(5,8,17,.5) 34%, rgba(5,8,17,.86) 66%, rgba(5,8,17,.93) 100%)',
      }"
    />
  </div>
</template>
