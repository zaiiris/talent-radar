"""
ОТВЕЧАЕТ ЗА: Оценку лидерского потенциала кандидата.

ЧТО ДЕЛАЕТ:
  1. Анализирует текст эссе + ответов из бота через regex-паттерны
  2. Считает балл по 4 категориям:
       - Инициатива   (я создал, я запустил, моя идея...)
       - Влияние      (убедил, руководил командой из N...)
       - Результаты   (увеличили на X%, победили, достигли...)
       - Рефлексия    (понял, изменил подход, научился...)
  3. Штрафует за слабые сигналы (участвовал, помогал...)
  4. Финально перепроверяет через Claude API
  5. Итог = паттерны*0.45 + claude*0.55

КЛЮЧЕВАЯ ИДЕЯ:
  Отличаем ЛИДЕРА от ИСПОЛНИТЕЛЯ.
  "Я участвовал в команде" ≠ "Я организовал команду из 8 человек"

ИСПОЛЬЗУЕТСЯ В: scoring.py → метод score()
"""

import re
import os
import json
from typing import Dict, List, Tuple
import anthropic

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


# ══════════════════════════════════════════════
# ПАТТЕРНЫ — ЯДРО АЛГОРИТМА
# ══════════════════════════════════════════════

# ── Категория 1: ИНИЦИАТИВА (+8 за каждое совпадение, макс 32) ──
# Кандидат сам что-то начал, придумал, запустил
INITIATIVE_PATTERNS: List[Tuple[str, str]] = [
    ("создал / основал",      r'\bя\s+(создал|основал|запустил|открыл|учредил|основала|создала|запустила)\b'),
    ("организовал",           r'\bя\s+(организовал|организовала|провёл|провела|устроил|устроила)\b'),
    ("инициировал",           r'\b(по моей инициативе|я инициировал|я инициировала|моя инициатива)\b'),
    ("предложил идею",        r'\b(моя идея|я предложил|я предложила|я придумал|я придумала|я разработал|я разработала)\b'),
    ("взял ответственность",  r'\b(взял|взяла)\s+(на себя|ответственность|инициативу)\b'),
    ("первым сделал",         r'\b(первым|первой)\s+(предложил|реализовал|запустил|начал)\b'),
    ("основатель",            r'\b(основатель|сооснователь|co.?founder|founder)\b'),
]

# ── Категория 2: ВЛИЯНИЕ НА ЛЮДЕЙ (+10 за каждое, макс 40) ──
# Кандидат двигал других людей, руководил
INFLUENCE_PATTERNS: List[Tuple[str, str]] = [
    ("руководил командой",    r'\b(руководил|руководила|возглавил|возглавила|координировал|координировала)\b'),
    ("команда из N человек",  r'\b(команд[аеуы]\s+из\s+\d+|вёл\s+команду|управлял\s+командой)\b'),
    ("убедил / мотивировал",  r'\b(убедил|убедила|мотивировал|мотивировала|вдохновил|вдохновила)\s+(команду|людей|коллег|участников|одноклассников|студентов)\b'),
    ("под моим руководством", r'\b(под моим руководством|мне доверили|я возглавил|я возглавила)\b'),
    ("наставник / ментор",    r'\b(наставник|ментор|mentor|куратор|тренер команды)\b'),
    ("принял решение",        r'\b(принял|приняла)\s+(решение|ответственное решение|стратегическое решение)\b'),
    ("делегировал",           r'\b(делегировал|делегировала|распределил|распределила)\s+(задачи|обязанности|роли)\b'),
]

# ── Категория 3: КОНКРЕТНЫЕ РЕЗУЛЬТАТЫ (+7 за каждое, макс 28) ──
# Есть цифры, факты, измеримый итог
RESULT_PATTERNS: List[Tuple[str, str]] = [
    ("процент / рост",        r'\d+\s*%'),
    ("числовой результат",    r'\b(достигли|увеличили|сократили|подняли|снизили|вырастили)\b.*\d+'),
    ("N участников/людей",    r'\b\d+\s*(человек|участников|пользователей|студентов|школьников|команд)\b'),
    ("первое место / победа", r'\b(заняли|заняла|занял)\s+(первое|1)\s*место\b'),
    ("выиграли грант",        r'\b(выиграл|выиграла|получил|получила)\s+(грант|финансирование|стипендию|приз)\b'),
    ("запустили продукт",     r'\b(запустили|выпустили|реализовали|внедрили)\s+(проект|продукт|приложение|платформу|систему)\b'),
    ("конкретные сроки",      r'\b(за\s+\d+\s*(дней|недель|месяцев|месяца)|в\s+срок|досрочно)\b'),
]

# ── Категория 4: РЕФЛЕКСИЯ (+6 за каждое, макс 24) ──
# Кандидат анализирует опыт, делает выводы, меняет подход
REFLECTION_PATTERNS: List[Tuple[str, str]] = [
    ("понял / осознал",       r'\b(понял|поняла|осознал|осознала)\b'),
    ("научился / вынес",      r'\b(научился|научилась|вынес|вынесла)\s+(урок|опыт|понимание|вывод)\b'),
    ("изменил подход",        r'\b(изменил|изменила)\s+(подход|стратегию|взгляд|мнение|метод)\b'),
    ("в следующий раз",       r'\b(в следующий раз|теперь я знаю|этот опыт (показал|научил|дал))\b'),
    ("ошибка научила",        r'\b(ошибка|неудача|провал)\s+(научила|показала|помогла|дала понять)\b'),
    ("критическое мышление",  r'\b(проанализировал|проанализировала|оценил|оценила)\s+(ситуацию|результат|ошибки)\b'),
]

# ── ШТРАФЫ — исполнительские сигналы (-5 за каждое) ──
# Кандидат был частью, а не лидером
WEAK_PATTERNS: List[Tuple[str, str]] = [
    ("просто участвовал",     r'\b(просто\s+)?(участвовал|участвовала)\s+(в\s+)?(команде|проекте|мероприятии)\b'),
    ("помогал другим",        r'\b(помогал|помогала)\s+(команде|другим|коллегам|куратору|организаторам)\b'),
    ("был в составе",         r'\b(был|была)\s+(в\s+)?(составе|члене|членом)\s+(команды|группы)\b'),
    ("выполнял задания",      r'\b(выполнял|выполняла)\s+(задания|поручения|указания)\b'),
    ("нас направляли",        r'\b(нам\s+сказали|нас\s+направили|руководство\s+решило|куратор\s+сказал)\b'),
    ("мечты без действий",    r'\b(хотел бы|мечтаю|планирую когда.нибудь|надеюсь однажды)\b'),
    ("неуверенность",         r'\b(наверное|возможно|может быть|не уверен|не уверена)\b'),
]

# ── Максимумы по категориям ──
CATEGORY_MAX = {
    "initiative":  {"per_hit": 8,  "max": 32},
    "influence":   {"per_hit": 10, "max": 40},
    "results":     {"per_hit": 7,  "max": 28},
    "reflection":  {"per_hit": 6,  "max": 24},
    "weak":        {"per_hit": -5, "max": -25},  # штраф
}


# ══════════════════════════════════════════════
# ГЛАВНЫЙ КЛАСС
# ══════════════════════════════════════════════

class LeadershipNLPScorer:
    """
    Оценивает лидерский потенциал кандидата.

    Использование:
        scorer = LeadershipNLPScorer()
        result = await scorer.score(essay="...", bot_answers="...")
    """

    async def score(self, essay: str = "", bot_answers: str = "") -> Dict:
        """
        Главный метод. Возвращает словарь с баллом и объяснением.

        Args:
            essay:       текст мотивационного эссе
            bot_answers: все ответы из Telegram-бота, объединённые в одну строку

        Returns:
            {
              "score": 0–100,
              "explanation": "...",
              "details": {
                "pattern_score": ...,
                "claude_score": ...,
                "categories": { initiative, influence, results, reflection, penalties },
                "hits": [ {category, label, text_fragment}, ... ],
                "weaknesses": [ ... ],
              }
            }
        """
        full_text = f"{essay}\n{bot_answers}".strip()

        if not full_text or len(full_text) < 30:
            return self._empty_result("Недостаточно текста для анализа лидерства")

        # 1. Паттерн-анализ
        pattern_result = self._pattern_analysis(full_text)
        pattern_score = pattern_result["total_score"]

        # 2. Claude перепроверка
        claude_score, claude_explanation = await self._claude_check(essay, bot_answers)

        # 3. Финальный балл: 45% паттерны + 55% Claude
        final_score = round(
            min(pattern_score * 0.45 + claude_score * 0.55, 100.0), 1
        )

        explanation = self._build_explanation(
            final_score, pattern_result, claude_score, claude_explanation
        )

        return {
            "score": final_score,
            "explanation": explanation,
            "details": {
                "pattern_score": round(pattern_score, 1),
                "claude_score": round(claude_score, 1),
                "categories": pattern_result["categories"],
                "hits": pattern_result["hits"],
                "weaknesses": pattern_result["weaknesses"],
            },
        }

    # ──────────────────────────────────────────
    # 1. ПАТТЕРН-АНАЛИЗ
    # ──────────────────────────────────────────

    def _pattern_analysis(self, text: str) -> Dict:
        """
        Прогоняем текст через все паттерны.
        Считаем баллы по категориям.
        """
        text_lower = text.lower()
        categories = {}
        all_hits = []
        all_weaknesses = []

        # Инициатива
        init_hits, init_score = self._scan_category(
            text_lower, INITIATIVE_PATTERNS,
            CATEGORY_MAX["initiative"]["per_hit"],
            CATEGORY_MAX["initiative"]["max"],
        )
        categories["initiative"] = {"score": init_score, "hits": len(init_hits)}
        all_hits += [{"category": "initiative", **h} for h in init_hits]

        # Влияние
        infl_hits, infl_score = self._scan_category(
            text_lower, INFLUENCE_PATTERNS,
            CATEGORY_MAX["influence"]["per_hit"],
            CATEGORY_MAX["influence"]["max"],
        )
        categories["influence"] = {"score": infl_score, "hits": len(infl_hits)}
        all_hits += [{"category": "influence", **h} for h in infl_hits]

        # Результаты
        res_hits, res_score = self._scan_category(
            text_lower, RESULT_PATTERNS,
            CATEGORY_MAX["results"]["per_hit"],
            CATEGORY_MAX["results"]["max"],
        )
        categories["results"] = {"score": res_score, "hits": len(res_hits)}
        all_hits += [{"category": "results", **h} for h in res_hits]

        # Рефлексия
        refl_hits, refl_score = self._scan_category(
            text_lower, REFLECTION_PATTERNS,
            CATEGORY_MAX["reflection"]["per_hit"],
            CATEGORY_MAX["reflection"]["max"],
        )
        categories["reflection"] = {"score": refl_score, "hits": len(refl_hits)}
        all_hits += [{"category": "reflection", **h} for h in refl_hits]

        # Штрафы
        weak_hits, penalty = self._scan_category(
            text_lower, WEAK_PATTERNS,
            CATEGORY_MAX["weak"]["per_hit"],
            CATEGORY_MAX["weak"]["max"],
        )
        categories["penalties"] = {"score": penalty, "hits": len(weak_hits)}
        all_weaknesses = [{"category": "weak", **h} for h in weak_hits]

        # Сумма до 100
        raw = init_score + infl_score + res_score + refl_score + penalty
        total = round(max(0.0, min(raw, 100.0)), 1)

        return {
            "total_score": total,
            "categories": categories,
            "hits": all_hits,
            "weaknesses": all_weaknesses,
        }

    def _scan_category(
        self,
        text: str,
        patterns: List[Tuple[str, str]],
        per_hit: int,
        cap: int,
    ) -> Tuple[List[Dict], float]:
        """
        Ищем все совпадения в тексте по списку паттернов.
        Возвращаем список совпадений и итоговый балл категории.
        """
        hits = []
        seen_labels = set()

        for label, pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for m in matches:
                if label not in seen_labels:  # каждый паттерн считаем один раз
                    fragment = text[max(0, m.start()-20):m.end()+40].strip()
                    hits.append({"label": label, "fragment": f"...{fragment}..."})
                    seen_labels.add(label)
                    break

        score = len(hits) * per_hit
        if cap > 0:
            score = min(score, cap)
        else:
            score = max(score, cap)  # для штрафов (отрицательных)

        return hits, float(score)

    # ──────────────────────────────────────────
    # 2. CLAUDE ПЕРЕПРОВЕРКА
    # ──────────────────────────────────────────

    async def _claude_check(self, essay: str, bot_answers: str) -> Tuple[float, str]:
        """
        Claude читает текст и выставляет балл лидерства 0–100.
        Возвращает (score, explanation).
        """
        prompt = f"""Ты — эксперт-психолог по оценке молодых лидеров для программ развития таланта.

Оцени ЛИДЕРСКИЙ ПОТЕНЦИАЛ кандидата строго по тексту ниже.

Критерии оценки (от важного к менее важному):
1. Инициатива — сам(а) что-то начинал(а), не ждал(а) указаний
2. Влияние — двигал(а) людей, руководил(а), убеждал(а)
3. Результаты — есть конкретные измеримые итоги (цифры, факты)
4. Рефлексия — анализирует опыт, меняет подход после ошибок
5. Штраф — если только "участвовал", "помогал", "был в команде" — это исполнитель, не лидер

--- ЭССЕ ---
{essay[:1500] or "(не указано)"}

--- ОТВЕТЫ В БОТЕ ---
{bot_answers[:2000] or "(нет ответов)"}

Верни ТОЛЬКО JSON без markdown:
{{
  "score": <число 0-100>,
  "explanation": "<2-3 предложения: конкретно что нашёл и почему такой балл>",
  "strongest_signal": "<самый сильный лидерский сигнал из текста>",
  "biggest_gap": "<главная зона роста>"
}}"""

        try:
            resp = _client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            raw = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
            data = json.loads(raw)
            return float(data.get("score", 50)), data.get("explanation", "")
        except Exception as e:
            return 50.0, f"Claude-анализ недоступен: {e}"

    # ──────────────────────────────────────────
    # ВСПОМОГАТЕЛЬНЫЕ
    # ──────────────────────────────────────────

    def _empty_result(self, reason: str) -> Dict:
        return {
            "score": 0.0,
            "explanation": reason,
            "details": {
                "pattern_score": 0,
                "claude_score": 0,
                "categories": {},
                "hits": [],
                "weaknesses": [],
            },
        }

    def _build_explanation(
        self,
        final: float,
        pattern_result: Dict,
        claude_score: float,
        claude_explanation: str,
    ) -> str:
        cats = pattern_result.get("categories", {})
        parts = []

        init = cats.get("initiative", {}).get("score", 0)
        infl = cats.get("influence", {}).get("score", 0)
        res  = cats.get("results",   {}).get("score", 0)
        refl = cats.get("reflection",{}).get("score", 0)
        pen  = cats.get("penalties", {}).get("score", 0)

        if init > 0:
            parts.append(f"инициатива +{int(init)}")
        if infl > 0:
            parts.append(f"влияние +{int(infl)}")
        if res > 0:
            parts.append(f"результаты +{int(res)}")
        if refl > 0:
            parts.append(f"рефлексия +{int(refl)}")
        if pen < 0:
            parts.append(f"штраф исполнителя {int(pen)}")

        pattern_summary = " | ".join(parts) if parts else "сигналы не найдены"
        return (
            f"Лидерство {final}/100 (паттерны: {pattern_summary}). "
            f"Claude: {claude_explanation}"
        )