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
  const chips: ReasonChip[] = []

  // 1. AI 종합 점수 근거
  if (input.signal_score >= 70) {
    chips.push({ label: 'AI 점수 우수', color: 'green' })
  } else if (input.signal_score >= 50) {
    chips.push({ label: 'AI 점수 양호', color: 'yellow' })
  }

  // 2. 기술 점수 근거
  if (input.tech_score != null) {
    if (input.tech_score >= 70) {
      chips.push({ label: '기술 점수 강세', color: 'green' })
    } else if (input.tech_score <= 35) {
      chips.push({ label: '기술 점수 약세', color: 'red' })
    }
  }

  // 3. LSTM 근거
  if (!input.lstm_available) {
    chips.push({ label: 'LSTM 미사용', color: 'gray' })
  } else if (input.lstm_score != null) {
    if (input.lstm_score >= 60) {
      chips.push({ label: 'LSTM 긍정', color: 'blue' })
    } else if (input.lstm_score <= 40) {
      chips.push({ label: 'LSTM 부정', color: 'red' })
    }
  }

  // 4. 신호 근거 — 칩이 부족할 때 보충 또는 명확화
  if (input.signal === 'BUY') {
    chips.push({ label: '매수 후보', color: 'green' })
  } else if (input.signal === 'SELL') {
    chips.push({ label: '주의 후보', color: 'red' })
  }

  // 최대 3개만 반환 (우선순위: 앞에서 삽입된 순서)
  return chips.slice(0, 3)
}
