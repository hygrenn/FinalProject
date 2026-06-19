import { useEffect, useState, useCallback } from 'react'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import api from '@/lib/api'
import { Bot, Play, Square, RefreshCw, TrendingUp, TrendingDown, ChevronDown, ChevronUp } from 'lucide-react'

interface AutoTradeConfig {
  id: string
  enabled: boolean
  mode: 'paper' | 'real'
  total_budget: number
  stop_loss_pct: number
  take_profit_pct: number
}

interface AutoTradeLog {
  id: string
  stock_code: string
  stock_name: string
  action: string
  quantity: number
  price: number
  total_amount: number
  reason: string
  signal_score: number
  mode: string
  created_at: string
}

function formatKRW(n: number) {
  if (n >= 100000000) return `${(n / 100000000).toFixed(1)}억원`
  if (n >= 10000) return `${Math.floor(n / 10000)}만원`
  return `${n.toLocaleString()}원`
}

export function AutoTradePanel() {
  const [config, setConfig] = useState<AutoTradeConfig>({
    id: '', enabled: false, mode: 'paper',
    total_budget: 1000000, stop_loss_pct: 5, take_profit_pct: 10,
  })
  const [logs, setLogs] = useState<AutoTradeLog[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [runResult, setRunResult] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const fetchConfig = useCallback(async () => {
    const res = await api.get('/auto-trade/config')
    setConfig(res.data)
  }, [])

  const fetchLogs = useCallback(async () => {
    const res = await api.get('/auto-trade/logs?limit=50')
    setLogs(res.data.logs || [])
  }, [])

  useEffect(() => {
    let cancelled = false
    Promise.all([fetchConfig(), fetchLogs()])
      .catch(() => setError('데이터를 불러오지 못했습니다.'))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [fetchConfig, fetchLogs])

  const handleToggle = async (enabled: boolean) => {
    if (enabled && config.mode === 'real') {
      if (!window.confirm('실거래 모드입니다. 실제 자금이 사용됩니다. 계속하시겠습니까?')) return
    }
    setError(null)
    try {
      const res = await api.put('/auto-trade/config', { enabled })
      setConfig(res.data)
    } catch (e: any) {
      setError(e.response?.data?.detail || '변경 실패')
    }
  }

  const handleSaveBudget = async () => {
    setSaving(true)
    setError(null)
    try {
      const res = await api.put('/auto-trade/config', {
        total_budget: config.total_budget,
        stop_loss_pct: config.stop_loss_pct,
        take_profit_pct: config.take_profit_pct,
        mode: config.mode,
      })
      setConfig(res.data)
    } catch (e: any) {
      setError(e.response?.data?.detail || '저장 실패')
    } finally {
      setSaving(false)
    }
  }

  const handleRunNow = async () => {
    setRunning(true)
    setRunResult(null)
    setError(null)
    try {
      const res = await api.post('/auto-trade/run')
      if (res.data.skipped) {
        setError('자동매매를 먼저 활성화해 주세요.')
      } else {
        const n = res.data.executed
        setRunResult(n > 0 ? `${n}건 실행 완료` : '현재 조건에 맞는 매매 없음')
        await fetchLogs()
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || '실행 실패')
    } finally {
      setRunning(false)
    }
  }

  const handleStop = async () => {
    if (!window.confirm('자동매매를 즉시 중지합니다. 보유 포지션은 그대로 유지됩니다.')) return
    try {
      await api.post('/auto-trade/stop')
      setConfig(prev => ({ ...prev, enabled: false }))
    } catch (e: any) {
      setError(e.response?.data?.detail || '중지 실패')
    }
  }

  const totalBuy = logs.filter(l => l.action === 'BUY').reduce((s, l) => s + l.total_amount, 0)
  const totalSell = logs.filter(l => l.action === 'SELL').reduce((s, l) => s + l.total_amount, 0)
  const invested = totalBuy - totalSell

  if (loading) return (
    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">불러오는 중...</div>
  )

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto p-4 space-y-3">

        {/* 메인 카드 */}
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          {/* 상태 헤더 */}
          <div className={`px-5 py-4 ${config.enabled ? 'bg-green-500/10 border-b border-green-500/20' : 'border-b border-border'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center ${config.enabled ? 'bg-green-500/20' : 'bg-muted'}`}>
                  <Bot className={`w-4 h-4 ${config.enabled ? 'text-green-400' : 'text-muted-foreground'}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">AI 자동매매</span>
                    <Badge variant={config.enabled ? 'default' : 'outline'} className="text-xs py-0">
                      {config.enabled ? '● 실행 중' : '중지됨'}
                    </Badge>
                    <Badge variant="outline" className="text-xs py-0">{config.mode === 'paper' ? '모의' : '실거래'}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {config.enabled
                      ? `${formatKRW(config.total_budget)} 운용 중 · AI가 전종목 스크리닝`
                      : 'AI에게 예산을 맡기면 자동으로 매매합니다'}
                  </p>
                </div>
              </div>
              <Switch checked={config.enabled} onCheckedChange={handleToggle} />
            </div>
          </div>

          {/* 예산 입력 */}
          <div className="px-5 py-4 space-y-3">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="text-xs text-muted-foreground block mb-1">AI에게 맡길 금액</label>
                <div className="relative">
                  <Input
                    type="number"
                    value={config.total_budget}
                    onChange={e => setConfig(prev => ({ ...prev, total_budget: Number(e.target.value) }))}
                    min={10000} step={100000}
                    className="h-10 text-sm pr-8"
                    placeholder="1000000"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">원</span>
                </div>
              </div>
              <Button onClick={handleSaveBudget} disabled={saving} className="mt-5 h-10 px-4">
                {saving ? '저장...' : '설정'}
              </Button>
            </div>

            {/* 고급 설정 토글 */}
            <button
              onClick={() => setShowAdvanced(v => !v)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              안전장치 설정
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-3 gap-3 pt-1">
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">거래 모드</label>
                  <div className="flex gap-1">
                    {(['paper', 'real'] as const).map(m => (
                      <button key={m} onClick={() => setConfig(prev => ({ ...prev, mode: m }))}
                        className={`flex-1 py-1 text-xs rounded border transition-colors ${config.mode === m ? 'bg-primary text-primary-foreground border-primary' : 'border-border text-muted-foreground'}`}>
                        {m === 'paper' ? '모의' : '실거래'}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">손절 기준</label>
                  <div className="relative">
                    <Input type="number" value={config.stop_loss_pct}
                      onChange={e => setConfig(prev => ({ ...prev, stop_loss_pct: Number(e.target.value) }))}
                      min={1} max={30} step={0.5} className="h-8 text-xs pr-6" />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-red-400">%</span>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">익절 기준</label>
                  <div className="relative">
                    <Input type="number" value={config.take_profit_pct}
                      onChange={e => setConfig(prev => ({ ...prev, take_profit_pct: Number(e.target.value) }))}
                      min={1} max={100} step={0.5} className="h-8 text-xs pr-6" />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-green-400">%</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 액션 버튼 */}
          <div className="px-5 pb-4 flex gap-2">
            <Button variant="outline" onClick={handleRunNow} disabled={running} className="flex-1 h-9">
              {running ? <><RefreshCw className="w-3.5 h-3.5 mr-2 animate-spin" />분석 중...</> : <><Play className="w-3.5 h-3.5 mr-2" />지금 실행</>}
            </Button>
            {config.enabled && (
              <Button variant="destructive" onClick={handleStop} className="h-9 px-4">
                <Square className="w-3.5 h-3.5 mr-1.5" />긴급 정지
              </Button>
            )}
          </div>
        </div>

        {/* 알림 */}
        {error && <div className="bg-destructive/10 border border-destructive/30 rounded-lg px-4 py-2.5 text-sm text-destructive">{error}</div>}
        {runResult && <div className="bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-2.5 text-sm text-green-400">✅ {runResult}</div>}

        {/* 운용 현황 */}
        {logs.length > 0 && (
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: '총 매수', value: formatKRW(totalBuy), color: 'text-foreground' },
              { label: '총 매도', value: formatKRW(totalSell), color: 'text-foreground' },
              { label: '현재 투자', value: formatKRW(Math.max(0, invested)), color: invested > 0 ? 'text-primary' : 'text-muted-foreground' },
            ].map(item => (
              <div key={item.label} className="bg-card border border-border rounded-lg p-3 text-center">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className={`text-sm font-semibold mt-1 ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* 거래 기록 */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium">거래 기록</h3>
            <button onClick={fetchLogs} className="text-muted-foreground hover:text-foreground">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {logs.length === 0 ? (
            <div className="flex flex-col items-center py-10 text-muted-foreground">
              <Bot className="w-8 h-8 mb-2 opacity-20" />
              <p className="text-sm">아직 거래 기록이 없습니다</p>
              <p className="text-xs mt-1 opacity-70">금액 설정 후 "지금 실행"을 눌러보세요</p>
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map(log => (
                <div key={log.id} className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-muted/30 transition-colors">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${log.action === 'BUY' ? 'bg-green-500/15' : 'bg-red-500/15'}`}>
                    {log.action === 'BUY'
                      ? <TrendingUp className="w-3 h-3 text-green-400" />
                      : <TrendingDown className="w-3 h-3 text-red-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium">{log.stock_name || log.stock_code}</span>
                    <span className="text-xs text-muted-foreground ml-2">{log.reason}</span>
                  </div>
                  <div className="text-right shrink-0">
                    <p className={`text-sm font-medium ${log.action === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                      {log.action === 'BUY' ? '-' : '+'}{formatKRW(log.total_amount)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {log.created_at ? new Date(log.created_at).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
