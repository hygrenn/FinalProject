import type { Candle, MACDPoint } from '@/types'

function ema(values: number[], period: number): number[] {
  const k = 2 / (period + 1)
  const result: number[] = []
  let emaPrev = values.slice(0, period).reduce((a, b) => a + b, 0) / period
  result.push(emaPrev)
  for (let i = period; i < values.length; i++) {
    emaPrev = values[i] * k + emaPrev * (1 - k)
    result.push(emaPrev)
  }
  return result
}

export function calculateRSI(
  candles: Candle[],
  period = 14
): { time: string | number; value: number }[] {
  if (candles.length <= period) return []

  const result: { time: string | number; value: number }[] = []
  const closes = candles.map((c) => c.close)

  let avgGain = 0
  let avgLoss = 0

  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1]
    if (diff > 0) avgGain += diff
    else avgLoss += Math.abs(diff)
  }
  avgGain /= period
  avgLoss /= period

  for (let i = period; i < candles.length; i++) {
    if (i > period) {
      const diff = closes[i] - closes[i - 1]
      const gain = diff > 0 ? diff : 0
      const loss = diff < 0 ? Math.abs(diff) : 0
      avgGain = (avgGain * (period - 1) + gain) / period
      avgLoss = (avgLoss * (period - 1) + loss) / period
    }
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    result.push({ time: candles[i].time, value: Math.round((100 - 100 / (1 + rs)) * 100) / 100 })
  }

  return result
}

export function calculateMACD(candles: Candle[]): MACDPoint[] {
  if (candles.length < 27) return []

  const closes = candles.map((c) => c.close)
  const ema12 = ema(closes, 12)
  const ema26 = ema(closes, 26)

  const macdLine: number[] = []
  const macdTimes: (string | number)[] = []
  // ema26[i] = EMA26 at time (i+25), ema12[i+14] = EMA12 at time (i+25)
  const macdOffset = ema12.length - ema26.length  // = 14

  for (let i = 0; i < ema26.length; i++) {
    macdLine.push(ema12[i + macdOffset] - ema26[i])
    macdTimes.push(candles[i + 25].time)
  }

  if (macdLine.length < 9) return []

  const signalLine = ema(macdLine, 9)
  const sigOffset = macdLine.length - signalLine.length

  return signalLine.map((sig, i) => {
    const macdVal = macdLine[i + sigOffset]
    return {
      time: macdTimes[i + sigOffset],
      macd: Math.round(macdVal * 100) / 100,
      signal: Math.round(sig * 100) / 100,
      histogram: Math.round((macdVal - sig) * 100) / 100,
    }
  })
}
