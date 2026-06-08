export class MockWebSocket {
  url: string
  readyState: number = 0
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null

  private _interval: ReturnType<typeof setInterval> | null = null
  private _basePrice: number = 73400

  constructor(url: string) {
    this.url = url
    const match = url.match(/\/(\d{6})$/)
    if (match) {
      const prices: Record<string, number> = {
        '005930': 73400,
        '000660': 185000,
        '035420': 210000,
        '035720': 42100,
        '051910': 320000,
      }
      this._basePrice = prices[match[1]] ?? 73400
    }

    setTimeout(() => {
      if (this.readyState === 3) return
      this.readyState = 1
      this.onopen?.()
      this._startInterval()
    }, 0)
  }

  private _startInterval() {
    this._interval = setInterval(() => {
      const change = (Math.random() - 0.5) * this._basePrice * 0.006
      this._basePrice = Math.round(this._basePrice + change)
      const change_pct = Math.round((change / (this._basePrice - change)) * 10000) / 100
      this.onmessage?.({
        data: JSON.stringify({ price: this._basePrice, change_pct }),
      })
    }, 2000)
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  send(_data: string): void {}

  close(): void {
    if (this._interval) {
      clearInterval(this._interval)
      this._interval = null
    }
    this.readyState = 3
    this.onclose?.()
  }
}
