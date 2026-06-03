import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Stock } from '@/types'
import { cn } from '@/lib/utils'

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

  const isBuy = orderType === 'BUY'
  const total = Number(quantity) * Number(price)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
    setTimeout(() => {
      setSubmitted(false)
      onClose()
    }, 1500)
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
            <div className="text-sm text-muted-foreground">모의거래 체결됨</div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            {/* 주문 타입 */}
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
