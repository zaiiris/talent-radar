"""
growth_analyzer.py
══════════════════════════════════════════════════════════════
ОТВЕЧАЕТ ЗА: Анализ траектории роста кандидата во времени.

ЧТО ДЕЛАЕТ:
  1. Берёт список достижений кандидата (строки текста)
  2. Определяет год каждого достижения (regex)
  3. Определяет уровень каждого достижения (паттерны слов)
  4. Строит линию роста через линейную регрессию
  5. Считает итоговый балл 0–100

КЛЮЧЕВАЯ ИДЕЯ:
  Кандидат который вырос с уровня 1 до уровня 3 за 2 года
  получает БОЛЬШЕ баллов чем тот кто всегда был на уровне 3.
  "Вектор важнее точки."

ИСПОЛЬЗУЕТСЯ В: scoring.py → метод score()
══════════════════════════════════════════════════════════════
"""

import re
import math
from typing import List, Dict, Tuple, Optional


# ──────────────────────────────────────────────
# ПАТТЕРНЫ УРОВНЕЙ ДОСТИЖЕНИЙ
# Чем выше число — тем круче достижение
# ──────────────────────────────────────────────

LEVEL_PATTERNS: List[Tuple[int, List[str]]] = [
    # Уровень 4 — Международный топ
    (4, [
        r'\bмеждународн\w*\s+(победитель|чемпион|призёр|1\s*место)\b',
        r'\binternational\s+(winner|champion|first)\b',
        r'\bworld\s+(champion|winner|finalist)\b',
        r'\bгрант\s+(президента|правительства|болашак)\b',
        r'\bболашак\b',
        r'\bнобел\w*\b',
        r'\bпатент\b',
    ]),

    # Уровень 3 — Победитель / первое место / публикация
    (3, [
        r'\b(победитель|чемпион|1\s*место|первое\s*место)\b',
        r'\b(winner|champion|1st\s*place|gold\s*medal)\b',
        r'\bгрант\b',
        r'\bстипендия\b',
        r'\bпубликаци\w*\b',
        r'\bисследовани\w*\b',
        r'\bнаучна\w*\s+работ\w*\b',
        r'\bfirst\s+place\b',
    ]),

    # Уровень 2 — Призёр / финалист / диплом
    (2, [
        r'\b(призёр|призер|2\s*место|3\s*место|второе\s*место|третье\s*место)\b',
        r'\b(финалист|полуфиналист)\b',
        r'\b(диплом\s*(i|ii|iii|1|2|3)\s*степени)\b',
        r'\b(серебр\w*|бронз\w*)\b',
        r'\b(finalist|semifinalist|runner.?up|2nd|3rd)\b',
        r'\bhonor\w*\s+mention\b',
    ]),

    # Уровень 1 — Участник / прошёл отбор
    (1, [
        r'\b(участник|участница|участие)\b',
        r'\b(participant|attendee|member)\b',
        r'\b(прошёл|прошла)\s+(отбор|конкурс|кастинг)\b',
        r'\b(олимпиад\w*|конкурс\w*|хакатон\w*|форум\w*)\b',  # упоминание без уровня
        r'\b(стажировк\w*|практик\w*)\b',
        r'\b(волонтёр|волонтер|доброволец)\b',
        r'\b(internship|volunteer)\b',
    ]),
]

# Бонусы поверх уровня (суммируются)
BONUS_PATTERNS: List[Tuple[float, str, str]] = [
    # (бонус_балл, описание, regex)
    (0.8, "международный масштаб",  r'\b(международн\w*|international|global|worldwide)\b'),
    (0.6, "лидерская роль",         r'\b(руководитель|лидер|капитан|организатор|основатель)\b'),
    (0.6, "грант / финансирование", r'\b(грант|стипендия|финансирован\w*|fellowship|grant)\b'),
    (0.5, "научная деятельность",   r'\b(исследовани\w*|публикаци\w*|научн\w*|research)\b'),
    (0.4, "победа в команде",       r'\b(команд\w*\s+(победил|выиграл|заняла))\b'),
]

# Стоп-паттерны — снижают уровень на 0.5
WEAK_PATTERNS = [
    r'\b(планирую|собираюсь|хочу\s+попробовать)\b',   # намерения, не факты
    r'\b(не\s+прошёл|не\s+прошла|не\s+попал)\b',      # неудача без роста
]


# ──────────────────────────────────────────────
# ГЛАВНЫЙ КЛАСС
# ──────────────────────────────────────────────

class GrowthAnalyzer:
    """
    Анализирует траекторию роста кандидата по его достижениям.

    Использование:
        analyzer = GrowthAnalyzer()
        result = analyzer.analyze(achievements=["Победитель олимпиады 2024", ...], age=20)
    """

    def analyze(self, achievements: List[str], age: int = 20) -> Dict:
        """
        Главный метод. Возвращает словарь с баллом и объяснением.

        Args:
            achievements: список строк с достижениями
            age: возраст кандидата (для бонуса молодости)

        Returns:
            {
              "score": 0–100,
              "explanation": "...",
              "details": { ... },
              "timeline": [ {year, level, text}, ... ],
              "slope": float,
              "start_level": int,
              "peak_level": int,
            }
        """
        if not achievements:
            return self._empty_result("Достижения не указаны")

        # 1. Парсим каждое достижение → (год, уровень, текст)
        timeline = self._build_timeline(achievements)

        if not timeline:
            return self._empty_result("Не удалось определить уровень достижений")

        # 2. Считаем базовый балл через регрессию
        slope, slope_score = self._regression_score(timeline)

        # 3. Бонус за рывок "с низкого на высокий"
        underdog_bonus = self._underdog_bonus(timeline)

        # 4. Бонус молодости
        youth_bonus = self._youth_bonus(age, timeline)

        # 5. Бонус за количество и разнообразие
        volume_score = self._volume_score(achievements)

        # 6. Собираем итог
        raw = slope_score + underdog_bonus + youth_bonus + volume_score
        score = round(min(raw, 100.0), 1)

        # 7. Формируем объяснение
        start = timeline[0]["level"] if timeline else 0
        peak = max(t["level"] for t in timeline)
        explanation = self._build_explanation(slope, slope_score, underdog_bonus, youth_bonus, start, peak)

        return {
            "score": score,
            "explanation": explanation,
            "details": {
                "slope": round(slope, 3),
                "slope_score": round(slope_score, 1),
                "underdog_bonus": round(underdog_bonus, 1),
                "youth_bonus": round(youth_bonus, 1),
                "volume_score": round(volume_score, 1),
                "achievements_parsed": len(timeline),
                "achievements_total": len(achievements),
            },
            "timeline": timeline,
            "slope": round(slope, 3),
            "start_level": start,
            "peak_level": peak,
        }

    # ──────────────────────────────────────────
    # 1. ПОСТРОЕНИЕ ТАЙМЛАЙНА
    # ──────────────────────────────────────────

    def _build_timeline(self, achievements: List[str]) -> List[Dict]:
        """
        Для каждого достижения определяем год и уровень.
        Возвращаем отсортированный по году список.
        """
        timeline = []
        current_year = 2025  # fallback если год не найден

        for text in achievements:
            year = self._extract_year(text, fallback=current_year)
            level = self._extract_level(text)

            if level == 0:
                continue  # не смогли определить уровень — пропускаем

            # Бонусы поверх базового уровня
            bonus = self._calc_bonuses(text)
            effective_level = level + bonus

            # Штраф за слабые паттерны
            for pattern in WEAK_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    effective_level -= 0.5

            timeline.append({
                "year": year,
                "level": round(max(effective_level, 0.5), 2),
                "base_level": level,
                "bonus": round(bonus, 2),
                "text": text,
            })

        # Сортируем по году
        timeline.sort(key=lambda x: x["year"])
        return timeline

    def _extract_year(self, text: str, fallback: int = 2024) -> int:
        """Извлекаем год из строки. Если нет — возвращаем fallback."""
        match = re.search(r'\b(20\d{2}|19\d{2})\b', text)
        if match:
            return int(match.group(1))
        return fallback

    def _extract_level(self, text: str) -> int:
        """
        Определяем базовый уровень достижения (1–4).
        Проверяем паттерны от высшего к низшему — первое совпадение выигрывает.
        """
        text_lower = text.lower()
        for level, patterns in LEVEL_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return level
        return 0  # не распознано

    def _calc_bonuses(self, text: str) -> float:
        """Суммируем бонусы за дополнительные маркеры."""
        total_bonus = 0.0
        for bonus_val, _, pattern in BONUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                total_bonus += bonus_val
        return min(total_bonus, 2.0)  # максимум +2 к уровню

    # ──────────────────────────────────────────
    # 2. ЛИНЕЙНАЯ РЕГРЕССИЯ → SLOPE SCORE
    # ──────────────────────────────────────────

    def _regression_score(self, timeline: List[Dict]) -> Tuple[float, float]:
        """
        Строим линейную регрессию (год → уровень).
        slope > 0 = рост, slope < 0 = спад, slope ≈ 0 = плато.

        Возвращаем (slope, score 0–60).
        """
        if len(timeline) == 1:
            # Одно достижение — смотрим только на уровень
            level = timeline[0]["level"]
            score = min(level / 4 * 40, 40)
            return 0.0, score

        years = [t["year"] for t in timeline]
        levels = [t["level"] for t in timeline]

        # Нормализуем годы чтобы избежать больших чисел
        min_year = min(years)
        xs = [y - min_year for y in years]
        ys = levels

        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n

        numerator = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        denominator = sum((xs[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0.0
        else:
            slope = numerator / denominator

        # Переводим slope в балл (0–60)
        # slope 1.0+ (рост на уровень в год) = 60 баллов
        # slope 0.5  = ~40 баллов
        # slope 0    = 20 баллов (нейтрально)
        # slope -0.5 = 5 баллов
        if slope >= 1.0:
            score = 60.0
        elif slope >= 0.5:
            score = 40 + (slope - 0.5) * 40
        elif slope >= 0:
            score = 20 + slope * 40
        elif slope >= -0.5:
            score = max(5, 20 + slope * 30)
        else:
            score = 5.0

        return slope, round(score, 1)

    # ──────────────────────────────────────────
    # 3. UNDERDOG БОНУС — рывок снизу вверх
    # ──────────────────────────────────────────

    def _underdog_bonus(self, timeline: List[Dict]) -> float:
        """
        Бонус за то что кандидат стартовал низко и вырос высоко.
        Это ваша ключевая фича из ТЗ.

        Примеры:
          Уровень 1 → 4 за 2 года = +20 баллов (максимум)
          Уровень 1 → 3 за 3 года = +14 баллов
          Уровень 3 → 4 за 5 лет  = +3 балла (рос, но с высокой базы)
        """
        if len(timeline) < 2:
            return 0.0

        start_level = timeline[0]["level"]
        peak_level = max(t["level"] for t in timeline)
        growth = peak_level - start_level

        if growth <= 0:
            return 0.0

        # Считаем годы между первым и пиковым достижением
        peak_year = max(t["year"] for t in timeline if t["level"] == peak_level)
        start_year = timeline[0]["year"]
        years_elapsed = max(peak_year - start_year, 1)

        # Чем ниже старт и быстрее рост — тем выше бонус
        low_start_multiplier = max(0, (3 - start_level) / 3)  # 1.0 если старт=0, 0 если старт=3
        speed_multiplier = min(2.0 / years_elapsed, 1.5)      # быстрее = лучше

        bonus = growth * 5 * low_start_multiplier * speed_multiplier
        return round(min(bonus, 20.0), 1)

    # ──────────────────────────────────────────
    # 4. БОНУС МОЛОДОСТИ
    # ──────────────────────────────────────────

    def _youth_bonus(self, age: int, timeline: List[Dict]) -> float:
        """
        Если кандидат молодой, а достижения высокие — это впечатляет больше.
        Максимум +10 баллов.
        """
        if not timeline:
            return 0.0
        peak = max(t["level"] for t in timeline)
        # Моложе 19 + высокий уровень = большой бонус
        if age <= 18 and peak >= 3:
            return 10.0
        elif age <= 20 and peak >= 2:
            return 6.0
        elif age <= 22 and peak >= 3:
            return 4.0
        return 0.0

    # ──────────────────────────────────────────
    # 5. ОБЪЁМ И РАЗНООБРАЗИЕ
    # ──────────────────────────────────────────

    def _volume_score(self, achievements: List[str]) -> float:
        """
        Дополнительные баллы за количество достижений.
        Максимум +10 баллов (чтобы не перекрывать главные сигналы).
        """
        n = len(achievements)
        if n >= 7:
            return 10.0
        elif n >= 5:
            return 7.0
        elif n >= 3:
            return 4.0
        elif n >= 1:
            return 2.0
        return 0.0

    # ──────────────────────────────────────────
    # ВСПОМОГАТЕЛЬНЫЕ
    # ──────────────────────────────────────────

    def _empty_result(self, reason: str) -> Dict:
        return {
            "score": 0.0,
            "explanation": reason,
            "details": {},
            "timeline": [],
            "slope": 0.0,
            "start_level": 0,
            "peak_level": 0,
        }

    def _build_explanation(
        self, slope: float, slope_score: float,
        underdog_bonus: float, youth_bonus: float,
        start: float, peak: float
    ) -> str:
        parts = []

        if slope > 0.5:
            parts.append(f"стремительный рост (наклон {round(slope, 2)})")
        elif slope > 0:
            parts.append(f"стабильный рост (наклон {round(slope, 2)})")
        elif slope == 0:
            parts.append("стабильный уровень без динамики")
        else:
            parts.append(f"снижение активности (наклон {round(slope, 2)})")

        if underdog_bonus > 0:
            parts.append(
                f"рывок с уровня {round(start,1)} до {round(peak,1)} "
                f"(+{round(underdog_bonus,1)} бонус)"
            )

        if youth_bonus > 0:
            parts.append(f"бонус молодости (+{round(youth_bonus,1)})")

        return "Траектория роста: " + "; ".join(parts) + "."