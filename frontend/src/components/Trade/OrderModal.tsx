import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Stock } from '@/types'
import { cn } from '@/lib/utils'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

interface OrderModalProps {
  open: boolean
  onClose: () => void
  stock: Stock
  orderType: 'BUY' | 'SELL'
}

export function OrderModal({ open, onClose, stock, orderType }: OrderModalProps) {
  const [priceType, setPriceType] = useState<'MARKET' | 'LIMIT'>('LIMIT')
  const [quantity, setQuantity] = useState('1')
  const [price, setPrice] = useState(String(stock.price ?? 0))
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const user = useAuthStore((s) => s.user)

  const isBuy = orderType === 'BUY'
  const total = Number(quantity) * Number(price)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitted(true)
    try {
      await api.post('/trades/order', {
        stock_code: stock.code,
        order_type: orderType,
        price_type: priceType,
        quantity: Number(quantity),
        price: priceType === 'LIMIT' ? Number(price) : undefined,
        mode: user?.mode ?? 'paper',
      })
      setTimeout(() => { setSubmitted(false); onClose() }, 1500)
    } catch (err: unknown) {
      setSubmitted(false)
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? '주문 처리 중 오류가 발생했습니다')
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className={cn(isBuy ? 'text-green-400' : 'text-red-400')}>
            <span>{stock.name}</span>
            {' '}
            <span>{isBuy ? '매수' : '매도'}</span>
          </DialogTitle>
        </DialogHeader>

        {submitted ? (
          <div className="text-center py-6">
            <div className={cn('text-2xl font-bold mb-2', isBuy ? 'text-green-400' : 'text-red-400')}>
              {isBuy ? '매수 완료' : '매도 완료'}
            </div>
            <div className="text-sm text-muted-foreground">주문이 접수되었습니다</div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex gap-2">
              {(['LIMIT', 'MARKET'] as const).map((type) => (
                <Button
                  key={type}
                  type="button"
                  variant={priceType === type ? 'default' : 'outline'}
                  size="sm"
                  className="flex-1"
                  onClick={() => setPriceType(type)}
                >
                  {type === 'LIMIT' ? '지정가' : '시장가'}
                </Button>
              ))}
            </div>

            {priceType === 'LIMIT' && (
              <div>
                <label className="text-xs text-muted-foreground">주문가격</label>
                <Input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="mt-1"
                />
              </div>
            )}

            <div>
              <label className="text-xs text-muted-foreground">수량</label>
              <Input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="mt-1"
              />
            </div>

            {priceType === 'LIMIT' && (
              <div className="text-sm text-right text-muted-foreground">
                주문금액: <span className="text-foreground font-medium">{total.toLocaleString()}원</span>
              </div>
            )}

            {error && (
              <div className="text-xs text-red-400">{error}</div>
            )}

            <div className="flex gap-2 pt-1">
              <Button type="button" variant="outline" className="flex-1" onClick={onClose}>취소</Button>
              <Button
                type="submit"
                className={cn('flex-1', isBuy ? 'bg-green-500 hover:bg-green-600' : 'bg-red-500 hover:bg-red-600')}
              >
                주문
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
