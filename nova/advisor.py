from __future__ import annotations

from .ml import Prediction


class Advisor:
    """Recommendation-only layer. It has no reference to broker/rule mutators."""

    def explain(self, ticker: str, p: Prediction, easy: bool = True) -> str:
        up = p.up_probability
        if up >= 0.65:
            direction = "상승 쪽 신호가 비교적 강합니다"
        elif up >= 0.55:
            direction = "상승 쪽이 조금 우세합니다"
        elif up <= 0.35:
            direction = "하락 쪽 신호가 비교적 강합니다"
        elif up <= 0.45:
            direction = "하락 쪽이 조금 우세합니다"
        else:
            direction = "상승·하락 신호가 비슷합니다"

        confidence = p.model_score * 100
        if confidence >= 70:
            conf_text = "데이터 품질과 모델 일치도를 포함한 신뢰도가 비교적 높습니다"
        elif confidence >= 45:
            conf_text = "신뢰도는 중간 수준입니다"
        else:
            conf_text = "모델 간 의견이나 데이터 조건 때문에 불확실성이 큽니다"

        stock_text = (
            f"종목 전용 모델 {p.stock_probability * 100:.1f}%"
            if p.stock_probability is not None else "종목 전용 모델 미사용"
        )
        global_text = (
            f"시장 모델 {p.global_probability * 100:.1f}%"
            if p.global_probability is not None else "시장 모델 미사용"
        )

        if easy:
            return (
                f"{ticker}의 향후 {p.horizon_days}거래일 분석에서는 {direction}. "
                f"종합 상승 확률 추정치는 {up * 100:.1f}%이며 참고 가격 범위는 "
                f"{p.expected_low_price:,.0f} ~ {p.expected_high_price:,.0f}입니다. {conf_text}.\n\n"
                f"이번 분석은 {stock_text}, {global_text}을 함께 비교했습니다. "
                f"데이터 상태는 {p.data_tier}, 품질 점수는 {p.data_quality * 100:.0f}/100입니다.\n\n"
                "예측은 과거 패턴을 이용한 모의분석이며 실제 수익을 보장하지 않습니다. "
                "AI 권고는 주문이나 자동매매 규칙을 직접 수정할 권한이 없습니다."
            )

        f = p.feature_values
        lines = [
            "Model: Global + Stock RandomForest ensemble",
            f"Horizon: {p.horizon_days} trading days",
            f"Final UP: {p.up_probability * 100:.2f}% / DOWN: {p.down_probability * 100:.2f}%",
            f"Stock model: {p.stock_probability * 100:.2f}%" if p.stock_probability is not None else "Stock model: DISABLED",
            f"Global model: {p.global_probability * 100:.2f}%" if p.global_probability is not None else "Global model: UNAVAILABLE",
            f"Confidence: {p.model_score * 100:.1f}/100",
            f"Model agreement: {p.model_agreement * 100:.1f}/100",
            f"Data quality: {p.data_quality * 100:.1f}/100 · tier {p.data_tier}",
            f"Held-out accuracy: {p.test_accuracy * 100:.2f}%",
            f"Brier score: {p.brier_score:.4f}",
            f"Stock samples: {p.stock_samples}",
            f"Global samples: {p.global_samples}",
            f"RSI14: {f['rsi14'] * 100:.1f}",
            f"5D return: {f['ret5'] * 100:.2f}%",
            f"20D return: {f['ret20'] * 100:.2f}%",
            f"20D volatility: {f['vol20'] * 100:.2f}%",
            f"Volume ratio: {f['volume_ratio']:.2f}x",
            f"MACD/price: {f['macd_rel'] * 100:.3f}%",
            "",
            "Confidence inputs:",
            *[f"- {x}" for x in p.confidence_reasons],
            "",
            "ADVISORY ONLY: AI 계층은 Broker/Rule Engine 참조를 갖지 않아 주문 실행이나 규칙 수정이 불가능합니다.",
        ]
        return "\n".join(lines)

    def rule_advice(self, p: Prediction, current_price: float) -> str:
        up = p.up_probability
        if p.model_score < 0.40:
            return "권고: 현재 신뢰도가 낮습니다. 자동매매 가격 규칙을 이 분석 하나만으로 변경하지 않는 편이 안전합니다. 설정은 자동 변경되지 않습니다."
        if up >= 0.68:
            return "권고: 상승 신호가 강한 편입니다. 가까운 전량 매도 규칙이 있다면 분할매도 대안을 직접 비교해볼 수 있습니다. NOVA는 규칙을 자동 변경하지 않습니다."
        if up <= 0.32:
            return "권고: 하락 신호가 강한 편입니다. 신규 매수 규칙과 손실 제한 수준을 직접 재검토할 수 있습니다. NOVA는 규칙을 자동 변경하지 않습니다."
        return "권고: 종합 신호가 한쪽으로 충분히 강하지 않아 기존 규칙을 성급히 바꿀 근거가 약합니다."
