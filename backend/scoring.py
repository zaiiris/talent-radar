"""
scoring.py
══════════════════════════════════════════════════════════════
ОТВЕЧАЕТ ЗА: Оркестрацию всех модулей и финальный балл.

ФОРМУЛА ИТОГОВОГО БАЛЛА:
  total = growth_trajectory * 0.30
        + leadership        * 0.30
        + authenticity      * 0.25
        + communication     * 0.15

★ КИЛЛЕР-ФИЧА: Predictive Potential Index (PPI)
  Система предсказывает балл кандидата через 18 месяцев.
  Основана на 4 факторах:
    1. Velocity   — скорость набора достижений в прошлом
    2. Momentum   — инерция: кто рос — продолжит расти
    3. Agility    — рефлексия + коммуникация = скорость обучения
    4. Youth      — молодость = больше времени на рост

  Результат:
    Сейчас: 68 баллов
    Через 18 мес: ~84 балла (+16) 🚀 Скрытый алмаз — инвестировать

ИСПОЛЬЗУЕТСЯ В: app.py -> endpoints /scoring/{id}
══════════════════════════════════════════════════════════════
"""

import asyncio
from typing import Dict, Any, List, Tuple
from datetime import datetime

from growth_analyzer import GrowthAnalyzer
from leadership_nlp import LeadershipNLPScorer
from ai_detector import AIDetector
from communication import CommunicationAnalyzer


# ══════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════

WEIGHTS = {
    "growth_trajectory": 0.30,
    "leadership":        0.30,
    "authenticity":      0.25,
    "communication":     0.15,
}

RECOMMENDATIONS = [
    (80, "strong_yes", "Приоритет в шортлист"),
    (65, "yes",        "Рекомендован"),
    (45, "maybe",      "На усмотрение комиссии"),
    (0,  "no",         "Не рекомендован"),
]


# ══════════════════════════════════════════════
# ГЛАВНЫЙ КЛАСС
# ══════════════════════════════════════════════

class ScoringEngine:
    """
    Оркестратор: запускает все 4 модуля параллельно,
    собирает финальный результат и строит PPI-прогноз.
    """

    def __init__(self):
        self.growth   = GrowthAnalyzer()
        self.leader   = LeadershipNLPScorer()
        self.detector = AIDetector()
        self.comm     = CommunicationAnalyzer()

    async def score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Полный скоринг кандидата.

        Args:
            candidate: словарь {name, age, essay, achievements, bot_answers}

        Returns:
            Полный результат со всеми компонентами, флагами и PPI.
        """
        age          = int(candidate.get("age", 20))
        essay        = candidate.get("essay", "") or ""
        achievements = candidate.get("achievements", []) or []
        bot_answers  = candidate.get("bot_answers", []) or []
        answers_text = self._join_answers(bot_answers)

        # ── Модули запускаем параллельно где возможно ──
        growth_result = self.growth.analyze(achievements, age=age)

        leadership_result, auth_result = await asyncio.gather(
            self.leader.score(essay=essay, bot_answers=answers_text),
            self.detector.analyze(essay=essay, bot_answers=answers_text),
        )

        comm_result = self.comm.analyze(essay=essay, bot_answers=answers_text)

        # ── Баллы по компонентам ──
        scores = {
            "growth_trajectory": growth_result["score"],
            "leadership":        leadership_result["score"],
            "authenticity":      auth_result["score"],
            "communication":     comm_result["score"],
        }

        total = round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS), 1)

        # ── Флаги и рекомендация ──
        red_flags, green_flags = self._collect_flags(scores, growth_result, auth_result, bot_answers)
        rec_key, rec_label = self._recommend(total)

        # ── ★ PPI — Predictive Potential Index ──
        ppi = self._calculate_ppi(
            current_total=total,
            age=age,
            growth_result=growth_result,
            comm_result=comm_result,
            leadership_result=leadership_result,
        )

        return {
            "total":          total,
            "recommendation": rec_key,
            "rec_label":      rec_label,
            "explanation":    self._build_explanation(total, scores, ppi),
            "red_flags":      red_flags,
            "green_flags":    green_flags,
            "ppi":            ppi,
            "scored_at":      datetime.utcnow().isoformat(),
            "weights_used":   WEIGHTS,

            "components": {
                "growth_trajectory": {
                    "score":       scores["growth_trajectory"],
                    "weight":      WEIGHTS["growth_trajectory"],
                    "weighted":    round(scores["growth_trajectory"] * WEIGHTS["growth_trajectory"], 1),
                    "explanation": growth_result.get("explanation", ""),
                    "timeline":    growth_result.get("timeline", []),
                    "slope":       growth_result.get("slope", 0),
                    "start_level": growth_result.get("start_level", 0),
                    "peak_level":  growth_result.get("peak_level", 0),
                    "details":     growth_result.get("details", {}),
                },
                "leadership": {
                    "score":       scores["leadership"],
                    "weight":      WEIGHTS["leadership"],
                    "weighted":    round(scores["leadership"] * WEIGHTS["leadership"], 1),
                    "explanation": leadership_result.get("explanation", ""),
                    "hits":        leadership_result.get("details", {}).get("hits", []),
                    "weaknesses":  leadership_result.get("details", {}).get("weaknesses", []),
                    "categories":  leadership_result.get("details", {}).get("categories", {}),
                },
                "authenticity": {
                    "score":          scores["authenticity"],
                    "weight":         WEIGHTS["authenticity"],
                    "weighted":       round(scores["authenticity"] * WEIGHTS["authenticity"], 1),
                    "explanation":    auth_result.get("explanation", ""),
                    "ai_probability": auth_result.get("ai_probability", 0),
                    "ai_flag":        auth_result.get("ai_flag", False),
                    "signals":        auth_result.get("signals", []),
                    "cross_validation": auth_result.get("details", {}).get("cross_validation", {}),
                },
                "communication": {
                    "score":      scores["communication"],
                    "weight":     WEIGHTS["communication"],
                    "weighted":   round(scores["communication"] * WEIGHTS["communication"], 1),
                    "explanation": comm_result.get("explanation", ""),
                    "strengths":  comm_result.get("details", {}).get("strengths", []),
                    "weaknesses": comm_result.get("details", {}).get("weaknesses", []),
                    "tone":       comm_result.get("details", {}).get("tone", {}),
                    "domain":     comm_result.get("details", {}).get("domain", {}),
                    "readability": comm_result.get("details", {}).get("readability", {}),
                    "metrics":    comm_result.get("details", {}).get("metrics", {}),
                },
            },
        }

    # ══════════════════════════════════════════
    # ★ KILLER FEATURE — PREDICTIVE POTENTIAL INDEX
    # ══════════════════════════════════════════

    def _calculate_ppi(
        self,
        current_total:     float,
        age:               int,
        growth_result:     Dict,
        comm_result:       Dict,
        leadership_result: Dict,
    ) -> Dict:
        """
        Прогнозируем балл кандидата через 18 месяцев.

        Четыре независимых фактора → итоговый прирост → predicted score.

        Физическая аналогия:
          current_total = позиция
          velocity_gain = скорость
          momentum      = ускорение
          agility       = манёвренность
          youth_mult    = запас хода
        """

        slope = growth_result.get("slope", 0.0)

        # ── Фактор 1: Velocity — скорость набора достижений ──
        # slope = уровней роста в год
        # За 1.5 года → slope * 1.5 * конверсия в баллы
        if slope >= 1.2:
            velocity_gain = 16.0
        elif slope >= 0.8:
            velocity_gain = 12.0
        elif slope >= 0.5:
            velocity_gain = 8.0
        elif slope >= 0.2:
            velocity_gain = 4.0
        elif slope >= 0:
            velocity_gain = 1.0
        else:
            velocity_gain = -5.0

        # ── Фактор 2: Momentum — инерция роста ──
        # Underdog-бонус говорит о том что рост уже был — значит продолжится
        underdog = growth_result.get("details", {}).get("underdog_bonus", 0)
        start    = growth_result.get("start_level", 0)
        peak     = growth_result.get("peak_level", 0)

        if underdog >= 12 or (start <= 1 and peak >= 3):
            momentum_gain = 7.0    # мощный рывок → продолжит
        elif underdog >= 6 or slope > 0.4:
            momentum_gain = 4.0
        elif slope > 0:
            momentum_gain = 1.5
        else:
            momentum_gain = 0.0

        # ── Фактор 3: Learning Agility — скорость обучения ──
        # Кто рефлексирует и хорошо коммуницирует — быстрее усваивает опыт
        comm_score = comm_result.get("score", 50)
        refl_raw   = (
            leadership_result
            .get("details", {})
            .get("categories", {})
            .get("reflection", {})
            .get("score", 0)
        )
        refl_pct = min(refl_raw / 24 * 100, 100)  # 24 = макс за рефлексию
        agility_index = (comm_score * 0.6 + refl_pct * 0.4)

        if agility_index >= 75:
            agility_gain = 8.0
        elif agility_index >= 55:
            agility_gain = 5.0
        elif agility_index >= 35:
            agility_gain = 2.5
        else:
            agility_gain = 0.5

        # ── Фактор 4: Youth Multiplier ──
        # Молодость = больше впереди; умножаем весь прогноз
        if age <= 17:
            youth_mult = 1.40
        elif age <= 19:
            youth_mult = 1.25
        elif age <= 21:
            youth_mult = 1.12
        elif age <= 24:
            youth_mult = 1.00
        elif age <= 27:
            youth_mult = 0.92
        else:
            youth_mult = 0.85

        # ── Итог ──
        raw_gain = (velocity_gain + momentum_gain + agility_gain) * youth_mult

        # Эффект насыщения: при высоком current_total сложнее расти
        # 100 баллов = потолок, логистическое замедление
        saturation = 1.0 - (current_total / 130.0)
        final_gain = round(max(raw_gain * saturation, -10.0), 1)

        predicted = round(min(current_total + final_gain, 100.0), 1)

        # ── Классификация траектории ──
        if final_gain >= 14:
            traj_label = "🚀 Стремительный рост"
            traj_class = "rocket"
        elif final_gain >= 8:
            traj_label = "📈 Уверенный рост"
            traj_class = "growing"
        elif final_gain >= 3:
            traj_label = "➡️  Стабильный уровень"
            traj_class = "stable"
        elif final_gain >= 0:
            traj_label = "➖ Плато"
            traj_class = "plateau"
        else:
            traj_label = "📉 Риск снижения"
            traj_class = "declining"

        # ── Инвестиционный вердикт ──
        if predicted >= 82 and current_total < 65:
            invest = "💎 Скрытый алмаз — взять прямо сейчас"
        elif predicted >= 82:
            invest = "⭐ Сильный кандидат с высоким потолком"
        elif predicted >= 70 and current_total < 55:
            invest = "🌱 Перспективный — стоит инвестировать"
        elif predicted >= 65:
            invest = "✅ Надёжный выбор"
        elif predicted < current_total - 5:
            invest = "⚠️  Риск регресса без стимула"
        else:
            invest = "➖ Нейтральный прогноз"

        return {
            "current_score":   current_total,
            "predicted_score": predicted,
            "gain":            final_gain,
            "horizon_months":  18,

            "factors": {
                "velocity": {
                    "value": round(velocity_gain, 1),
                    "label": "Скорость набора достижений",
                    "slope": round(slope, 3),
                },
                "momentum": {
                    "value": round(momentum_gain, 1),
                    "label": "Инерция роста",
                    "underdog_bonus": round(underdog, 1),
                },
                "learning_agility": {
                    "value":         round(agility_gain, 1),
                    "label":         "Скорость обучения",
                    "agility_index": round(agility_index, 1),
                    "comm_contrib":  round(comm_score * 0.6, 1),
                    "refl_contrib":  round(refl_pct * 0.4, 1),
                },
                "youth_multiplier": {
                    "value": youth_mult,
                    "label": f"Коэффициент молодости (возраст {age})",
                },
            },

            "trajectory_label": traj_label,
            "trajectory_class": traj_class,
            "invest_label":     invest,
            "explanation": (
                f"Сейчас: {current_total} баллов → "
                f"Прогноз через 18 мес: {predicted} баллов "
                f"({'+' if final_gain >= 0 else ''}{final_gain}). "
                f"{traj_label}. {invest}."
            ),
        }

    # ══════════════════════════════════════════
    # ФЛАГИ
    # ══════════════════════════════════════════

    def _collect_flags(
        self,
        scores:      Dict,
        growth:      Dict,
        auth:        Dict,
        bot_answers: List,
    ) -> Tuple[List[str], List[str]]:
        red, green = [], []

        if auth.get("ai_flag"):
            red.append("⛔ Высокая вероятность AI-текста в эссе")
        if len(bot_answers) < 5:
            red.append("⚠️  Мало ответов в боте — картина неполная")
        if scores["growth_trajectory"] < 20:
            red.append("📉 Нет подтверждённых достижений или отрицательная динамика")
        if scores["leadership"] < 30:
            red.append("👤 Слабые сигналы лидерства — скорее исполнитель")
        if growth.get("slope", 0) < -0.2:
            red.append("📉 Снижение активности за последние годы")
        if scores["authenticity"] < 30:
            red.append("🤖 Текст почти полностью похож на AI-генерацию")

        if scores["growth_trajectory"] >= 70:
            green.append("📈 Сильная траектория роста")
        if growth.get("details", {}).get("underdog_bonus", 0) >= 10:
            green.append("🔥 Рывок с нижних позиций — Underdog")
        if scores["leadership"] >= 75:
            green.append("👑 Высокий лидерский потенциал")
        if scores["authenticity"] >= 80:
            green.append("✅ Высокая аутентичность текста")
        if scores["communication"] >= 75:
            green.append("🗣️  Сильная коммуникация")
        if growth.get("slope", 0) >= 0.8:
            green.append("🚀 Высокая скорость роста достижений")

        return red, green

    # ══════════════════════════════════════════
    # РЕКОМЕНДАЦИЯ И ВСПОМОГАТЕЛЬНЫЕ
    # ══════════════════════════════════════════

    def _recommend(self, total: float) -> Tuple[str, str]:
        for threshold, key, label in RECOMMENDATIONS:
            if total >= threshold:
                return key, label
        return "no", "Не рекомендован"

    def _join_answers(self, bot_answers: List[Dict]) -> str:
        parts = []
        for a in bot_answers:
            q   = a.get("question_text", "")
            ans = a.get("answer_text", "")
            if ans:
                parts.append(f"В: {q}\nО: {ans}")
        return "\n\n".join(parts)

    def _build_explanation(self, total: float, scores: Dict, ppi: Dict) -> str:
        breakdown = " | ".join(
            f"{k.replace('_', ' ')}: {round(scores[k] * WEIGHTS[k], 1)}"
            for k in WEIGHTS
        )
        return (
            f"Итог {total}/100 ({breakdown}). "
            f"PPI → {ppi['predicted_score']} через 18 мес "
            f"({'+' if ppi['gain'] >= 0 else ''}{ppi['gain']}). "
            f"{ppi['invest_label']}."
        )
