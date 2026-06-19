import { useEffect, useState, useCallback } from 'react'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { api } from '@/lib/api'
import { AlertTriangle, Play, Square, RefreshCw, Trash2, Plus, Bot } from 'lucide-react'

interface AutoTradeConfig {
  id: string
  enabled: boolean
  mode: 'paper' | 'real'
  total_budget: number
  budget_per_trade: number
  max_positions: number
  signal_threshold: number
  stop_loss_pct: number
  take_profit_pct: number
  watch_codes: string[]
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

const defaultConfig: AutoTradeConfig = {
  id: '',
  enabled: false,
  mode: 'paper',
  total_budget: 1000000,
  budget_per_trade: 100000,
  max_positions: 5,
  signal_threshold: 70,
  stop_loss_pct: 5.0,
  take_profit_pct: 10.0,
  watch_codes: [],
}

export function AutoTradePanel() {
  const [config, setConfig] = useState<AutoTradeConfig>(defaultConfig)
  const [logs, setLogs] = useState<AutoTradeLog[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [runResult, setRunResult] = useState<string | null>(null)

  const fetchConfig = useCallback(async () => {
    try {
      const res = await api.get('/auto-trade/config')
      setConfig(res.data)
    } catch (e) {
      setError('설정을 불러오지 못했습니다.')
    }
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const res = await api.get('/auto-trade/logs?limit=30')
      setLogs(res.data.logs || [])
    } catch (_e) {
      // ignore
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    Promise.all([fetchConfig(), fetchLogs()]).finally(() => {
      if (!cancelled) setLoading(false)
    })
    return () => { cancelled = true }
  }, [fetchConfig, fetchLogs])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const res = await api.put('/auto-trade/config', {
        enabled: config.enabled,
        mode: config.mode,
        total_budget: config.total_budget,
        budget_per_trade: config.budget_per_trade,
        max_positions: config.max_positions,
        signal_threshold: config.signal_threshold,
        stop_loss_pct: config.stop_loss_pct,
        take_profit_pct: config.take_profit_pct,
        watch_codes: config.watch_codes,
      })
      setConfig(res.data)
    } catch (e: any) {
      setError(e.response?.data?.detail || '저장 실패')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleEnable = async (enabled: boolean) => {
    if (enabled && config.mode === 'real') {
      const ok = window.confirm('실거래 모드로 자동매매를 활성화합니다. 계속하시겠습니까?')
      if (!ok) return
    }
    const updated = { ...config, enabled }
    setConfig(updated)
    try {
      const res = await api.put('/auto-trade/config', { enabled })
      setConfig(res.data)
    } catch (e: any) {
      setConfig(config)
      setError(e.response?.data?.detail || '저장 실패')
    }
  }

  const handleRunNow = async () => {
    setRunning(true)
    setRunResult(null)
    setError(null)
    try {
      const res = await api.post('/auto-trade/run')
      if (res.data.skipped) {
        setRunResult(`건너뜀: ${res.data.reason}`)
      } else {
        setRunResult(`완료: ${res.data.executed}건 실행`)
        await fetchLogs()
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || '실행 실패')
    } finally {
      setRunning(false)
    }
  }

  const handleKillSwitch = async () => {
    const ok = window.confirm('자동매매를 즉시 중지합니다. 계속하시겠습니까?')
    if (!ok) return
    try {
      await api.post('/auto-trade/stop')
      setConfig(prev => ({ ...prev, enabled: false }))
    } catch (e: any) {
      setError(e.response?.data?.detail || '중지 실패')
    }
  }

  const addWatchCode = () => {
    const code = newCode.trim()
    if (!/^\d{6}$/.test(code)) {
      setError('6자리 종목 코드를 입력해주세요 (예: 005930)')
      return
    }
    if (config.watch_codes.includes(code)) {
      setError('이미 추가된 종목입니다.')
      return
    }
    if (config.watch_codes.length >= 20) {
      setError('최대 20개까지 추가 가능합니다.')
      return
    }
    setConfig(prev => ({ ...prev, watch_codes: [...prev.watch_codes, code] }))
    setNewCode('')
    setError(null)
  }

  const removeWatchCode = (code: string) => {
    setConfig(prev => ({ ...prev, watch_codes: prev.watch_codes.filter(c => c !== code) }))
  }

  const actionColor = (action: string) => {
    if (action === 'BUY') return 'text-green-400'
    if (action === 'SELL') return 'text-red-400'
    return 'text-yellow-400'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        불러오는 중...
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold">AI 자동매매</h2>
          <Badge variant={config.enabled ? 'default' : 'outline'} className="text-xs">
            {config.enabled ? '활성' : '비활성'}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {config.mode === 'paper' ? '모의투자' : '실거래'}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            checked={config.enabled}
            onCheckedChange={handleToggleEnable}
          />
          <span className="text-sm text-muted-foreground">
            {config.enabled ? '실행 중' : '중지됨'}
          </span>
        </div>
      </div>

      {/* 경고 배너 */}
      {config.mode === 'real' && (
        <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">
            실거래 모드입니다. 실제 자금이 사용됩니다. 신중하게 설정하세요.
          </p>
        </div>
      )}

      {error && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {runResult && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-sm text-green-400">
          {runResult}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 왼쪽: 설정 */}
        <div className="space-y-4">
          <div className="bg-card border border-border rounded-lg p-4 space-y-4">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">기본 설정</h3>

            {/* 모드 */}
            <div className="space-y-1">
              <Label className="text-xs">거래 모드</Label>
              <div className="flex gap-2">
                {(['paper', 'real'] as const).map(m => (
                  <button
                    key={m}
                    onClick={() => setConfig(prev => ({ ...prev, mode: m }))}
                    className={`px-3 py-1.5 text-xs rounded border transition-colors ${
                      config.mode === m
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'border-border text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {m === 'paper' ? '모의투자' : '실거래'}
                  </button>
                ))}
              </div>
            </div>

            {/* 총 예산 */}
            <div className="space-y-1">
              <Label className="text-xs">총 예산 (원)</Label>
              <Input
                type="number"
                value={config.total_budget}
                onChange={e => setConfig(prev => ({ ...prev, total_budget: Number(e.target.value) }))}
                min={10000}
                step={10000}
                className="h-8 text-sm"
              />
              <p className="text-xs text-muted-foreground">자동매매에 사용할 총 금액</p>
            </div>

            {/* 1회 거래 금액 */}
            <div className="space-y-1">
              <Label className="text-xs">1회 매수 금액 (원)</Label>
              <Input
                type="number"
                value={config.budget_per_trade}
                onChange={e => setConfig(prev => ({ ...prev, budget_per_trade: Number(e.target.value) }))}
                min={10000}
                step={10000}
                className="h-8 text-sm"
              />
            </div>

            {/* 최대 보유 종목 수 */}
            <div className="space-y-1">
              <Label className="text-xs">최대 보유 종목 수: {config.max_positions}개</Label>
              <Slider
                value={[config.max_positions]}
                onValueChange={([v]) => setConfig(prev => ({ ...prev, max_positions: v }))}
                min={1}
                max={20}
                step={1}
                className="mt-2"
              />
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4 space-y-4">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">AI 신호 설정</h3>

            {/* 신호 임계값 */}
            <div className="space-y-1">
              <Label className="text-xs">
                최소 매수 점수: <span className="text-primary font-medium">{config.signal_threshold}점</span>
              </Label>
              <Slider
                value={[config.signal_threshold]}
                onValueChange={([v]) => setConfig(prev => ({ ...prev, signal_threshold: v }))}
                min={50}
                max={95}
                step={5}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground">이 점수 이상일 때만 매수합니다 (높을수록 보수적)</p>
            </div>

            {/* 손절 */}
            <div className="space-y-1">
              <Label className="text-xs">
                손절 기준: <span className="text-red-400 font-medium">-{config.stop_loss_pct}%</span>
              </Label>
              <Slider
                value={[config.stop_loss_pct]}
                onValueChange={([v]) => setConfig(prev => ({ ...prev, stop_loss_pct: v }))}
                min={1}
                max={30}
                step={0.5}
                className="mt-2"
              />
            </div>

            {/* 익절 */}
            <div className="space-y-1">
              <Label className="text-xs">
                익절 기준: <span className="text-green-400 font-medium">+{config.take_profit_pct}%</span>
              </Label>
              <Slider
                value={[config.take_profit_pct]}
                onValueChange={([v]) => setConfig(prev => ({ ...prev, take_profit_pct: v }))}
                min={1}
                max={100}
                step={0.5}
                className="mt-2"
              />
            </div>
          </div>

          {/* 관심 종목 */}
          <div className="bg-card border border-border rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              관심 종목 ({config.watch_codes.length}개)
            </h3>
            <div className="flex gap-2">
              <Input
                placeholder="종목코드 (예: 005930)"
                value={newCode}
                onChange={e => setNewCode(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addWatchCode()}
                maxLength={6}
                className="h-8 text-sm"
              />
              <Button size="sm" variant="outline" onClick={addWatchCode} className="h-8 px-2">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {config.watch_codes.map(code => (
                <div
                  key={code}
                  className="flex items-center gap-1 bg-secondary rounded px-2 py-1 text-xs"
                >
                  <span>{code}</span>
                  <button onClick={() => removeWatchCode(code)} className="text-muted-foreground hover:text-destructive">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
              {config.watch_codes.length === 0 && (
                <p className="text-xs text-muted-foreground">종목을 추가하면 자동매매 대상이 됩니다</p>
              )}
            </div>
          </div>

          {/* 버튼 영역 */}
          <div className="flex gap-2">
            <Button onClick={handleSave} disabled={saving} className="flex-1">
              {saving ? '저장 중...' : '설정 저장'}
            </Button>
            <Button variant="outline" onClick={handleRunNow} disabled={running} className="flex-1">
              {running ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  실행 중...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  지금 실행
                </>
              )}
            </Button>
          </div>

          {config.enabled && (
            <Button
              variant="destructive"
              onClick={handleKillSwitch}
              className="w-full"
            >
              <Square className="w-4 h-4 mr-2" />
              긴급 정지
            </Button>
          )}
        </div>

        {/* 오른쪽: 거래 기록 */}
        <div className="bg-card border border-border rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">거래 기록</h3>
            <button
              onClick={fetchLogs}
              className="text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              아직 자동매매 기록이 없습니다
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {logs.map(log => (
                <div key={log.id} className="border border-border rounded-lg p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${actionColor(log.action)}`}>
                        {log.action}
                      </span>
                      <span className="font-medium">
                        {log.stock_name || log.stock_code}
                      </span>
                      <span className="text-muted-foreground">{log.stock_code}</span>
                    </div>
                    <Badge variant="outline" className="text-xs py-0">
                      {log.mode === 'paper' ? '모의' : '실거래'}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <span>{log.quantity.toLocaleString()}주</span>
                    <span>@{log.price.toLocaleString()}원</span>
                    <span className="font-medium text-foreground">
                      {(log.total_amount / 10000).toFixed(1)}만원
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">{log.reason}</span>
                    <span className="text-muted-foreground">
                      {log.created_at ? new Date(log.created_at).toLocaleString('ko-KR', {
                        month: '2-digit', day: '2-digit',
                        hour: '2-digit', minute: '2-digit',
                      }) : ''}
                    </span>
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
