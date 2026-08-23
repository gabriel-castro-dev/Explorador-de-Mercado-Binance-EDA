import type { CanvasRenderingTarget2D } from 'fancy-canvas'
import type {
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesApi,
  ISeriesPrimitive,
  IChartApi,
  PrimitivePaneViewZOrder,
  SeriesAttachedParameter,
  Time,
  UTCTimestamp,
} from 'lightweight-charts'
import { BOLLINGER_BAND_FILL } from '~/utils/constants'

export interface BandPoint {
  time: UTCTimestamp
  upper: number
  lower: number
}

/**
 * Preenchimento de 5 % entre as bandas de Bollinger (Design.md §14.1).
 *
 * Lightweight Charts não preenche entre duas séries, então isto é um
 * `ISeriesPrimitive` anexado à série de candles: converte tempo→x pela time
 * scale e preço→y pela própria série, e desenha o polígono no espaço de mídia
 * (a borda não precisa de alinhamento pixel-perfect — é uma área, não um traço).
 *
 * Só desenha o que está visível; nos gaps de warm-up o polígono é interrompido,
 * nunca fechado no zero.
 */
class BandRenderer implements IPrimitivePaneRenderer {
  constructor(
    private readonly points: readonly BandPoint[],
    private readonly chart: IChartApi | null,
    private readonly series: ISeriesApi<'Candlestick'> | null,
  ) {}

  draw(target: CanvasRenderingTarget2D): void {
    const { chart, series, points } = this
    if (!chart || !series || points.length < 2) return

    const timeScale = chart.timeScale()
    // Segmentos contínuos: um gap de warm-up quebra o polígono em dois.
    const segments: { x: number, up: number, down: number }[][] = []
    let current: { x: number, up: number, down: number }[] = []

    for (const point of points) {
      const x = timeScale.timeToCoordinate(point.time as Time)
      const up = series.priceToCoordinate(point.upper)
      const down = series.priceToCoordinate(point.lower)
      if (x === null || up === null || down === null) {
        if (current.length > 1) segments.push(current)
        current = []
        continue
      }
      current.push({ x, up, down })
    }
    if (current.length > 1) segments.push(current)
    if (!segments.length) return

    target.useMediaCoordinateSpace(({ context }) => {
      context.save()
      context.fillStyle = BOLLINGER_BAND_FILL
      for (const segment of segments) {
        context.beginPath()
        const first = segment[0]
        if (!first) continue
        context.moveTo(first.x, first.up)
        for (let i = 1; i < segment.length; i++) {
          const p = segment[i]
          if (p) context.lineTo(p.x, p.up)
        }
        for (let i = segment.length - 1; i >= 0; i--) {
          const p = segment[i]
          if (p) context.lineTo(p.x, p.down)
        }
        context.closePath()
        context.fill()
      }
      context.restore()
    })
  }
}

export class BollingerBandPrimitive implements ISeriesPrimitive<Time> {
  private points: readonly BandPoint[] = []
  private chart: IChartApi | null = null
  private series: ISeriesApi<'Candlestick'> | null = null
  private requestUpdate?: () => void

  private readonly view: IPrimitivePaneView = {
    // Atrás das linhas e das velas: é iluminação de fundo, não moldura.
    zOrder: (): PrimitivePaneViewZOrder => 'bottom',
    renderer: () => new BandRenderer(this.points, this.chart, this.series),
  }

  attached(param: SeriesAttachedParameter<Time>): void {
    this.chart = param.chart as IChartApi
    this.series = param.series as ISeriesApi<'Candlestick'>
    this.requestUpdate = param.requestUpdate
  }

  detached(): void {
    this.chart = null
    this.series = null
    this.requestUpdate = undefined
  }

  setData(points: readonly BandPoint[]): void {
    this.points = points
    this.requestUpdate?.()
  }

  paneViews(): readonly IPrimitivePaneView[] {
    return [this.view]
  }
}
