// frontend/src/lib/recommendReasons.ts
// AI 추천 근거 칩 생성 helper — pure function, no side effects

export interface ReasonInput {
  signal: 'BUY' | 'HOLD' | 'SELL'
  signal_score: number
  tech_score: number | null
  lstm_score: number | null
  lstm_available: boolean
}

export interface ReasonChip {
  label: string
  color: 'green' | 'yellow' | 'red' | 'gray' | 'blue'
}

/**
 * 추천 종목의 signal/score 필드를 기반으로 근거 칩 2~3개를 생성한다.
 * 백엔드 변경 없이 프론트 응답 필드만 사용한다.
 */
export function buildReasonChips(input: ReasonInput): ReasonChip[] {
  // 1. 신호 근거 — BUY/SELL은 항상 맨 앞 슬롯 선점 (잘리지 않도록)
  const signalChip: ReasonChip | null =
    input.signal === 'BUY'
      ? { label: '매수 후보', color: 'green' }
      : input.signal === 'SELL'
        ? { label: '주의 후보', color: 'red' }
        : null

  const rest: ReasonChip[] = []

  // 2. AI 종합 점수 근거
  if (input.signal_score >= 70) {
    rest.push({ label: 'AI 점수 우수', color: 'green' })
  } else if (input.signal_score >= 50) {
    rest.push({ label: 'AI 점수 양호', color: 'yellow' })
  }

  // 3. 기술 점수 근거
  if (input.tech_score != null) {
    if (input.tech_score >= 70) {
      rest.push({ label: '기술 점수 강세', color: 'green' })
    } else if (input.tech_score <= 35) {
      rest.push({ label: '기술 점수 약세', color: 'red' })
    }
  }

  // 4. LSTM 근거
  if (!input.lstm_available) {
    rest.push({ label: 'LSTM 미사용', color: 'gray' })
  } else if (input.lstm_score != null) {
    if (input.lstm_score >= 60) {
      rest.push({ label: 'LSTM 긍정', color: 'blue' })
    } else if (input.lstm_score <= 40) {
      rest.push({ label: 'LSTM 부정', color: 'red' })
    }
  }

  // BUY/SELL: signal 칩 + 나머지 2개 (최대 3개)
  // HOLD: rest 칩만 사용, 없으면 중립 fallback
  let chips: ReasonChip[]
  if (signalChip) {
    chips = [signalChip, ...rest.slice(0, 2)]
  } else {
    chips = rest
  }

  // 최소 1개 보장 — HOLD이면서 모든 score가 중간 구간일 때 fallback
  if (chips.length === 0) {
    chips.push({ label: '중립', color: 'gray' })
  }

  // 최대 3개만 반환
  return chips.slice(0, 3)
}
