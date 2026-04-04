"""
communication.py
══════════════════════════════════════════════════════════════
ОТВЕЧАЕТ ЗА: Оценку качества коммуникации кандидата.

ЧТО ДЕЛАЕТ:
  Анализирует КАК человек говорит, а не ЧТО он говорит.
  Сильный коммуникатор = ценный сотрудник и лидер.

  8 МЕТРИК (без внешних ML-библиотек, только re + math):

  1. ЛЕКСИЧЕСКОЕ БОГАТСТВО   — словарный запас (RTTR)
  2. РИТМ ПРЕДЛОЖЕНИЙ        — разнообразие длин (не как AI)
  3. ЛОГИЧЕСКИЕ КОННЕКТОРЫ   — структурированность мысли
  4. КОНКРЕТНОСТЬ            — числа, даты, названия
  5. ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ — личные переживания, рефлексия
  6. АКТИВНЫЙ ЗАЛОГ          — "я сделал" vs "было сделано"
  7. ВОПРОСЫ И ДИАЛОГ        — живость речи
  8. СТОП-СЛОВА ШТРАФ        — слова-паразиты и канцелярит

  + НОВЫЕ ФИЧИ:
  9.  ТОНАЛЬНОСТЬ            — позитив vs негатив vs нейтраль
  10. ИНДЕКС ЧИТАЕМОСТИ      — адаптированный Flesch для русского
  11. УНИКАЛЬНЫЕ МЕТАФОРЫ    — образность мышления
  12. ПРОФЕССИОНАЛЬНЫЙ ЖАРГОН — признак экспертизы в области

ИСПОЛЬЗУЕТСЯ В: scoring.py → компонент communication
══════════════════════════════════════════════════════════════
"""

import re
import math
import statistics
from typing import Dict, List, Tuple, Optional


# ══════════════════════════════════════════════
# СЛОВАРИ И ПАТТЕРНЫ
# ══════════════════════════════════════════════

# Логические коннекторы по категориям (за разнообразие — бонус)
CONNECTORS: Dict[str, List[str]] = {
    "причина":     ["поэтому", "потому что", "так как", "поскольку", "ведь", "из-за"],
    "следствие":   ["следовательно", "в результате", "таким образом", "значит", "итого"],
    "уступка":     ["однако", "тем не менее", "несмотря на", "хотя", "но при этом"],
    "добавление":  ["кроме того", "помимо этого", "также", "вдобавок", "ещё и"],
    "пример":      ["например", "в частности", "скажем", "допустим", "как-то раз"],
    "уточнение":   ["то есть", "иными словами", "точнее", "а именно", "иначе говоря"],
    "контраст":    ["с одной стороны", "с другой стороны", "в отличие от", "зато"],
    "временной":   ["сначала", "затем", "после этого", "в итоге", "наконец"],
}

# Слова-паразиты и канцелярит (штраф)
FILLER_WORDS: List[Tuple[str, int]] = [
    # (паттерн, штраф)
    (r'\bкак бы\b',            3),
    (r'\bну\b',                2),
    (r'\bкороче\b',            2),
    (r'\bтипа\b',              3),
    (r'\bвот\b',               1),
    (r'\bэто самое\b',         3),
    (r'\bв общем-то\b',        2),
    (r'\bна самом деле\b',     1),
    (r'\bсобственно говоря\b', 2),
    (r'\bтак сказать\b',       2),
    # Канцелярит
    (r'\bосуществляет\w*\b',   3),
    (r'\bпроизвод\w+ работ\b', 3),
    (r'\bв целях\b',           2),
    (r'\bв части\b',           2),
    (r'\bявляется\b',          1),
]

# Активный залог — сигналы деятельности
ACTIVE_VOICE_PATTERNS = [
    r'\bя\s+(создал|сделал|написал|придумал|запустил|организовал|провёл|решил|выбрал|изменил)\b',
    r'\bя\s+(создала|сделала|написала|придумала|запустила|организовала|провела|решила|выбрала|изменила)\b',
    r'\bмы\s+(создали|сделали|запустили|разработали|реализовали|выиграли|достигли)\b',
]

# Пассивный залог — сигнал безличности
PASSIVE_VOICE_PATTERNS = [
    r'\b(было|была|были)\s+(сделано|создано|разработано|реализовано|принято|утверждено)\b',
    r'\b(осуществлялась|проводилась|выполнялась)\b',
    r'\b(мне было|мне поручили|меня попросили|нас направили)\b',
]

# Эмоциональный интеллект — личные переживания
EMOTIONAL_PATTERNS = [
    r'\b(почувствовал|почувствовала|ощутил|ощутила)\b',
    r'\b(был(о)? (страшно|волнительно|неловко|стыдно|гордо|радостно))\b',
    r'\b(меня (беспокоит|волнует|радует|вдохновляет|злит|удивляет))\b',
    r'\b(я (рад|горжусь|сожалею|удивился|удивилась|расстроился|расстроилась))\b',
    r'\b(это (важно|ценно|значимо) для меня\b)',
    r'\b(мне (нравится|не нравится|важно|интересно|сложно|легко))\b',
]

# Конкретность — числа и факты
SPECIFICITY_PATTERNS = [
    (r'\b\d+\s*%',                   "процент"),
    (r'\b\d+\s*(человек|участников|пользователей|студентов)', "людей"),
    (r'\b(20\d{2}|19\d{2})\b',       "год"),
    (r'\b\d+\s*(дней|недель|месяцев|часов|лет)', "период"),
    (r'«[^»]{2,40}»',                "название"),
    (r'\b[А-Я][а-я]+(ск(ий|ая|ое)|стан|город)\b', "место"),
    (r'\b\d+[\.,]\d+\b',             "точная цифра"),
    (r'\b(первый|второй|третий|1-й|2-й|3-й)\b', "порядок"),
]

# Метафоры и образность (НОВАЯ ФИЧА)
METAPHOR_PATTERNS = [
    r'\b(как (маяк|якорь|мост|фундамент|двигатель|ключ|зеркало))\b',
    r'\b(дверь (открылась|закрылась|к чему-то))\b',
    r'\b(точка (роста|опоры|невозврата|отсчёта|кипения))\b',
    r'\b(путь|дорога|маршрут)\s+(к|в|на)\b',
    r'\b(сломал(а)? стереотип|разрушил(а)? барьер|вышел из зоны комфорта)\b',
    r'\b(зажёг|зажгла|зажгли)\s+\w+',
]

# Профессиональный словарь по областям (НОВАЯ ФИЧА)
DOMAIN_VOCABULARIES: Dict[str, List[str]] = {
    "tech": [
        "алгоритм", "архитектура", "backend", "frontend", "api", "mvp",
        "agile", "scrum", "devops", "deploy", "gitlab", "github",
        "фреймворк", "библиотека", "база данных", "микросервис",
    ],
    "science": [
        "гипотеза", "эксперимент", "методология", "корреляция", "выборка",
        "валидация", "публикация", "рецензия", "грант", "лаборатория",
    ],
    "business": [
        "стратегия", "метрика", "kpi", "монетизация", "pivot", "unit-экономика",
        "traction", "инвестор", "стартап", "рынок", "конкурент", "юнит",
    ],
    "social": [
        "волонтёр", "нко", "социальный проект", "благотворительность",
        "сообщество", "инклюзия", "доступность", "акселератор",
    ],
}

# Позитивная vs негативная тональность (НОВАЯ ФИЧА)
POSITIVE_WORDS = [
    "достиг", "достигла", "победил", "победила", "вырос", "выросла",
    "улучшил", "улучшила", "горжусь", "рад", "рада", "вдохновляет",
    "люблю", "нравится", "отлично", "успешно", "эффективно",
    "создал", "создала", "запустил", "запустила", "помог", "помогла",
]
NEGATIVE_WORDS = [
    "провалил", "провалила", "неудача", "ошибка", "не получилось",
    "сложно", "тяжело", "трудно", "не смог", "не смогла", "потерял",
    "разочаровал", "страшно", "боялся", "боялась", "сомневался",
]


# ══════════════════════════════════════════════
# ГЛАВНЫЙ КЛАСС
# ══════════════════════════════════════════════

class CommunicationAnalyzer:
    """
    Анализирует качество коммуникации кандидата.

    Использование:
        analyzer = CommunicationAnalyzer()
        result = analyzer.analyze(essay="...", bot_answers="...")
    """

    def analyze(self, essay: str = "", bot_answers: str = "") -> Dict:
        """
        Полный анализ коммуникации.

        Args:
            essay:       мотивационное эссе
            bot_answers: ответы из Telegram-бота

        Returns:
            {
              "score": 0-100,
              "explanation": "...",
              "details": {
                "metrics": { каждая метрика с баллом },
                "strengths": [...],
                "weaknesses": [...],
                "tone": {...},
                "readability": {...},
                "domain": {...},
              }
            }
        """
        full_text = f"{essay}\n{bot_answers}".strip()

        if not full_text or len(full_text) < 30:
            return self._empty_result("Недостаточно текста для анализа")

        # ── 8 основных метрик ──
        m_lexical     = self._metric_lexical_richness(full_text)
        m_rhythm      = self._metric_sentence_rhythm(full_text)
        m_connectors  = self._metric_connectors(full_text)
        m_specificity = self._metric_specificity(full_text)
        m_emotional   = self._metric_emotional_intelligence(full_text)
        m_voice       = self._metric_active_voice(full_text)
        m_dialogue    = self._metric_dialogue_liveliness(full_text)
        m_fillers     = self._metric_filler_penalty(full_text)

        # ── 4 дополнительные фичи ──
        tone          = self._analyze_tone(full_text)
        readability   = self._analyze_readability(full_text)
        metaphors     = self._analyze_metaphors(full_text)
        domain        = self._analyze_domain(full_text)

        # ── Взвешенная сумма ──
        weighted_sum = (
            m_lexical["score"]     * 0.18 +
            m_rhythm["score"]      * 0.12 +
            m_connectors["score"]  * 0.16 +
            m_specificity["score"] * 0.18 +
            m_emotional["score"]   * 0.14 +
            m_voice["score"]       * 0.10 +
            m_dialogue["score"]    * 0.06 +
            m_fillers["score"]     * 0.06
        )

        # Бонусы от доп. фич (максимум +8)
        bonus = 0.0
        if metaphors["count"] >= 2:
            bonus += 3.0
        elif metaphors["count"] == 1:
            bonus += 1.5
        if domain["detected"]:
            bonus += min(len(domain["detected"]) * 1.5, 4.0)
        if tone["balance"] == "healthy":
            bonus += 1.0

        final_score = round(min(weighted_sum + bonus, 100.0), 1)

        # Сильные стороны и зоны роста
        metrics = {
            "lexical_richness":    m_lexical,
            "sentence_rhythm":     m_rhythm,
            "logical_connectors":  m_connectors,
            "specificity":         m_specificity,
            "emotional_intel":     m_emotional,
            "active_voice":        m_voice,
            "dialogue_liveliness": m_dialogue,
            "filler_penalty":      m_fillers,
        }
        strengths, weaknesses = self._collect_feedback(metrics, metaphors, domain, tone)
        explanation = self._build_explanation(final_score, metrics, strengths, weaknesses)

        return {
            "score": final_score,
            "explanation": explanation,
            "details": {
                "metrics":    {k: {"score": v["score"], "label": v["label"]} for k, v in metrics.items()},
                "strengths":  strengths,
                "weaknesses": weaknesses,
                "tone":       tone,
                "readability": readability,
                "metaphors":  metaphors,
                "domain":     domain,
            },
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 1 — ЛЕКСИЧЕСКОЕ БОГАТСТВО
    # ══════════════════════════════════════════

    def _metric_lexical_richness(self, text: str) -> Dict:
        """
        RTTR (Root Type-Token Ratio) — стабильная мера словарного запаса.
        Не зависит от длины текста в отличие от TTR.
        """
        words = self._tokenize(text)
        if not words:
            return {"score": 0.0, "label": "Лексическое богатство", "rttr": 0}

        unique = len(set(w.lower() for w in words))
        rttr = unique / math.sqrt(len(words))

        # Шкала: RTTR 3–4 = хорошо, 5+ = отлично
        if rttr >= 5.5:
            score = 100.0
        elif rttr >= 4.5:
            score = 85.0
        elif rttr >= 3.5:
            score = 70.0
        elif rttr >= 2.5:
            score = 50.0
        elif rttr >= 1.5:
            score = 30.0
        else:
            score = 10.0

        return {
            "score": score,
            "label": "Лексическое богатство",
            "rttr": round(rttr, 2),
            "unique_words": unique,
            "total_words": len(words),
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 2 — РИТМ ПРЕДЛОЖЕНИЙ
    # ══════════════════════════════════════════

    def _metric_sentence_rhythm(self, text: str) -> Dict:
        """
        Хороший ритм = разнообразие длин предложений.
        Короткие для удара. Длинные для объяснения. Средние для баланса.
        AI-текст монотонен, живой — нет.
        """
        sentences = self._split_sentences(text)
        if len(sentences) < 3:
            return {"score": 40.0, "label": "Ритм предложений", "cv": None}

        lengths = [len(s.split()) for s in sentences]
        mean = statistics.mean(lengths)
        stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev / mean if mean > 0 else 0

        # Оптимальная средняя длина 10–20 слов
        if 10 <= mean <= 20:
            length_score = 100
        elif 7 <= mean < 10 or 20 < mean <= 25:
            length_score = 75
        else:
            length_score = 45

        # Разнообразие (CV 0.3–0.6 = живая речь)
        if 0.30 <= cv <= 0.60:
            variety_score = 100
        elif 0.20 <= cv < 0.30 or 0.60 < cv <= 0.80:
            variety_score = 70
        elif cv < 0.20:
            variety_score = 30   # слишком монотонно (AI)
        else:
            variety_score = 50   # слишком хаотично

        score = round(length_score * 0.5 + variety_score * 0.5, 1)

        return {
            "score": score,
            "label": "Ритм предложений",
            "cv": round(cv, 3),
            "mean_length": round(mean, 1),
            "variety_score": variety_score,
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 3 — ЛОГИЧЕСКИЕ КОННЕКТОРЫ
    # ══════════════════════════════════════════

    def _metric_connectors(self, text: str) -> Dict:
        """
        Оцениваем не просто наличие коннекторов, но и их РАЗНООБРАЗИЕ.
        Человек который использует причинные, уступительные И временные
        коннекторы думает структурированно.
        """
        text_lower = text.lower()
        words = self._tokenize(text)
        if not words:
            return {"score": 0.0, "label": "Логические коннекторы"}

        found_categories = set()
        found_words = []
        total_hits = 0

        for category, connector_list in CONNECTORS.items():
            for conn in connector_list:
                if conn in text_lower:
                    found_categories.add(category)
                    found_words.append(conn)
                    total_hits += text_lower.count(conn)

        # Плотность: сколько коннекторов на 100 слов
        density = total_hits / (len(words) / 100)

        # Оптимальная плотность 1–3 на 100 слов
        if 1.0 <= density <= 3.0:
            density_score = 100
        elif 0.5 <= density < 1.0 or 3.0 < density <= 4.5:
            density_score = 70
        elif density > 4.5:
            density_score = 40   # перебор → канцелярит
        else:
            density_score = 20   # нет связей между мыслями

        # Разнообразие категорий
        diversity_score = min(len(found_categories) * 15, 100)

        score = round(density_score * 0.5 + diversity_score * 0.5, 1)

        return {
            "score": score,
            "label": "Логические коннекторы",
            "categories_found": list(found_categories),
            "unique_connectors": len(set(found_words)),
            "density_per_100": round(density, 2),
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 4 — КОНКРЕТНОСТЬ
    # ══════════════════════════════════════════

    def _metric_specificity(self, text: str) -> Dict:
        """
        Конкретные числа, даты, названия, места = высокое доверие.
        "Многие студенты" vs "47 студентов из 3 школ Алматы".
        """
        found = {}
        total_hits = 0

        for pattern, label in SPECIFICITY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found[label] = len(matches)
                total_hits += len(matches)

        # Разнообразие типов конкретики
        type_diversity = len(found)

        if total_hits >= 8 and type_diversity >= 4:
            score = 100.0
        elif total_hits >= 5 and type_diversity >= 3:
            score = 80.0
        elif total_hits >= 3 and type_diversity >= 2:
            score = 60.0
        elif total_hits >= 1:
            score = 35.0
        else:
            score = 5.0

        return {
            "score": score,
            "label": "Конкретность",
            "total_markers": total_hits,
            "types_found": found,
            "type_diversity": type_diversity,
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 5 — ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ
    # ══════════════════════════════════════════

    def _metric_emotional_intelligence(self, text: str) -> Dict:
        """
        Кандидат который называет свои чувства и рефлексирует —
        эмоционально зрелый. Это важно для лидера и командного игрока.
        """
        text_lower = text.lower()
        emotional_hits = []

        for pattern in EMOTIONAL_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                emotional_hits.extend(matches)

        count = len(emotional_hits)

        # Не перебарщиваем: 2–5 эмоциональных маркеров = идеально
        if count >= 5:
            score = 95.0
        elif count >= 3:
            score = 80.0
        elif count == 2:
            score = 65.0
        elif count == 1:
            score = 40.0
        else:
            score = 10.0   # полное отсутствие эмоций → роботизированно

        return {
            "score": score,
            "label": "Эмоциональный интеллект",
            "emotional_markers": count,
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 6 — АКТИВНЫЙ ЗАЛОГ
    # ══════════════════════════════════════════

    def _metric_active_voice(self, text: str) -> Dict:
        """
        "Я создал проект" > "Проект был создан мной".
        Активный залог = деятельная позиция, ответственность.
        """
        text_lower = text.lower()
        active_hits = sum(
            len(re.findall(p, text_lower, re.IGNORECASE))
            for p in ACTIVE_VOICE_PATTERNS
        )
        passive_hits = sum(
            len(re.findall(p, text_lower, re.IGNORECASE))
            for p in PASSIVE_VOICE_PATTERNS
        )

        total = active_hits + passive_hits
        if total == 0:
            ratio = 0.5
        else:
            ratio = active_hits / total

        if ratio >= 0.80:
            score = 100.0
        elif ratio >= 0.65:
            score = 80.0
        elif ratio >= 0.50:
            score = 60.0
        elif ratio >= 0.35:
            score = 40.0
        else:
            score = 15.0

        return {
            "score": score,
            "label": "Активный залог",
            "active_hits": active_hits,
            "passive_hits": passive_hits,
            "active_ratio": round(ratio, 2),
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 7 — ЖИВОСТЬ ДИАЛОГА
    # ══════════════════════════════════════════

    def _metric_dialogue_liveliness(self, text: str) -> Dict:
        """
        Вопросы, обращения, прямая речь — признак живого мышления.
        Монолог без единого вопроса или обращения = монотонность.
        """
        rhetorical_q = len(re.findall(r'\?', text))
        direct_speech = len(re.findall(r'«[^»]+»|"[^"]+"', text))
        exclamations  = len(re.findall(r'!', text))
        dashes        = len(re.findall(r'—|–', text))   # живой пунктуационный ритм

        liveliness = rhetorical_q * 3 + direct_speech * 4 + exclamations * 1 + dashes * 1

        if liveliness >= 15:
            score = 100.0
        elif liveliness >= 9:
            score = 80.0
        elif liveliness >= 5:
            score = 60.0
        elif liveliness >= 2:
            score = 40.0
        else:
            score = 15.0

        return {
            "score": score,
            "label": "Живость речи",
            "questions": rhetorical_q,
            "direct_speech": direct_speech,
            "exclamations": exclamations,
            "dashes": dashes,
        }

    # ══════════════════════════════════════════
    # МЕТРИКА 8 — ШТРАФ ЗА ПАРАЗИТЫ
    # ══════════════════════════════════════════

    def _metric_filler_penalty(self, text: str) -> Dict:
        """
        Слова-паразиты и канцелярит снижают доверие к кандидату.
        Начинаем с 100 и вычитаем.
        """
        text_lower = text.lower()
        words = self._tokenize(text)
        total_penalty = 0
        found_fillers = []

        for pattern, penalty in FILLER_WORDS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                found_fillers.append((pattern.strip(r'\b'), len(matches)))
                # Штраф масштабируется: много вхождений = больше штраф
                total_penalty += penalty * min(len(matches), 4)

        # Нормализуем по длине текста
        if words:
            normalized_penalty = (total_penalty / len(words)) * 100
        else:
            normalized_penalty = total_penalty

        score = round(max(100.0 - normalized_penalty * 3, 0.0), 1)

        return {
            "score": score,
            "label": "Чистота речи",
            "total_penalty": total_penalty,
            "fillers_found": found_fillers,
        }

    # ══════════════════════════════════════════
    # НОВАЯ ФИЧА 1 — ТОНАЛЬНОСТЬ
    # ══════════════════════════════════════════

    def _analyze_tone(self, text: str) -> Dict:
        """
        Анализирует баланс позитивного и негативного.

        "Healthy" = есть и позитив и признание трудностей.
        Только позитив = неискренность (AI-эффект).
        Только негатив = тревожный сигнал.
        """
        text_lower = text.lower()
        words = self._tokenize(text_lower)

        pos_count = sum(words.count(w) for w in POSITIVE_WORDS)
        neg_count = sum(words.count(w) for w in NEGATIVE_WORDS)
        total = pos_count + neg_count

        if total == 0:
            balance = "neutral"
            ratio = 0.5
        else:
            ratio = pos_count / total
            if 0.55 <= ratio <= 0.85:
                balance = "healthy"     # больше позитива, но есть и трудности
            elif ratio > 0.85:
                balance = "overly_positive"  # подозрительно идеально
            elif ratio < 0.30:
                balance = "negative"         # тревожный знак
            else:
                balance = "neutral"

        tone_labels = {
            "healthy":          "✅ Здоровый баланс позитива и реализма",
            "overly_positive":  "⚠️  Слишком позитивно — возможна неискренность",
            "negative":         "⚠️  Преобладает негатив",
            "neutral":          "➖ Нейтральная тональность",
        }

        return {
            "balance": balance,
            "label": tone_labels.get(balance, ""),
            "positive_count": pos_count,
            "negative_count": neg_count,
            "positive_ratio": round(ratio, 2),
        }

    # ══════════════════════════════════════════
    # НОВАЯ ФИЧА 2 — ИНДЕКС ЧИТАЕМОСТИ
    # ══════════════════════════════════════════

    def _analyze_readability(self, text: str) -> Dict:
        """
        Адаптация индекса Flesch для русского текста.
        Оценивает насколько легко читать текст кандидата.

        Формула адаптирована для кириллицы:
        206.835 - 1.015*(слов/предложений) - 84.6*(слогов/слов)
        """
        sentences = self._split_sentences(text)
        words     = self._tokenize(text)

        if not words or not sentences:
            return {"score": None, "label": "Недостаточно данных"}

        avg_sent_len = len(words) / len(sentences)
        # Приблизительный подсчёт слогов через гласные
        syllable_count = sum(self._count_syllables(w) for w in words)
        avg_syllables = syllable_count / len(words)

        flesch = 206.835 - 1.015 * avg_sent_len - 84.6 * avg_syllables

        # Интерпретация для русского
        if flesch >= 70:
            level = "Легко читается"
            icon = "✅"
        elif flesch >= 50:
            level = "Стандартный уровень"
            icon = "➖"
        elif flesch >= 30:
            level = "Сложноватый текст"
            icon = "⚠️"
        else:
            level = "Очень сложный текст"
            icon = "⛔"

        return {
            "flesch_score": round(flesch, 1),
            "level": level,
            "icon": icon,
            "avg_sentence_len": round(avg_sent_len, 1),
            "avg_syllables_per_word": round(avg_syllables, 2),
        }

    # ══════════════════════════════════════════
    # НОВАЯ ФИЧА 3 — МЕТАФОРЫ И ОБРАЗНОСТЬ
    # ══════════════════════════════════════════

    def _analyze_metaphors(self, text: str) -> Dict:
        """
        Метафоры и образные выражения — признак нестандартного мышления.
        Редкий кандидат пишет образно. Это выделяет.
        """
        text_lower = text.lower()
        found = []

        for pattern in METAPHOR_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                found.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])

        # Дополнительно ищем оригинальные сравнения через "как"
        similes = re.findall(r'\bкак\s+[а-яё]+(?:\s+[а-яё]+)?\b', text_lower)
        # Фильтруем банальные сравнения
        banal = {"как правило", "как будто", "как-то раз", "как бы", "как все"}
        unique_similes = [s for s in similes if s not in banal]

        total = len(found) + len(unique_similes)

        return {
            "count": total,
            "metaphors": found[:5],
            "similes": unique_similes[:5],
            "label": (
                "✅ Образное мышление" if total >= 2 else
                "➖ Есть образность" if total == 1 else
                "Без метафор"
            ),
        }

    # ══════════════════════════════════════════
    # НОВАЯ ФИЧА 4 — ПРОФЕССИОНАЛЬНЫЙ СЛОВАРЬ
    # ══════════════════════════════════════════

    def _analyze_domain(self, text: str) -> Dict:
        """
        Определяем область экспертизы кандидата по специальным словам.
        Кандидат который говорит на языке своей области — эксперт.
        """
        text_lower = text.lower()
        detected = {}

        for domain, vocab in DOMAIN_VOCABULARIES.items():
            hits = [w for w in vocab if w in text_lower]
            if len(hits) >= 2:  # минимум 2 слова = признак домена
                detected[domain] = hits

        domain_labels = {
            "tech": "💻 IT / Технологии",
            "science": "🔬 Наука / Исследования",
            "business": "📊 Бизнес / Стартапы",
            "social": "🤝 Социальные проекты",
        }

        return {
            "detected": {
                domain_labels.get(k, k): v
                for k, v in detected.items()
            },
            "primary": (
                domain_labels.get(max(detected, key=lambda d: len(detected[d])), "")
                if detected else None
            ),
            "label": (
                f"Экспертиза: {', '.join(domain_labels.get(k, k) for k in detected)}"
                if detected else "Область не определена"
            ),
        }

    # ══════════════════════════════════════════
    # ВСПОМОГАТЕЛЬНЫЕ
    # ══════════════════════════════════════════

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[а-яёА-ЯЁa-zA-Z]{2,}\b', text)

    def _split_sentences(self, text: str) -> List[str]:
        return [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 6]

    def _count_syllables(self, word: str) -> int:
        """Считаем слоги через гласные (приблизительно)."""
        vowels = "аеёиоуыэюяaeiou"
        count = sum(1 for ch in word.lower() if ch in vowels)
        return max(count, 1)

    def _collect_feedback(
        self,
        metrics: Dict,
        metaphors: Dict,
        domain: Dict,
        tone: Dict,
    ) -> Tuple[List[str], List[str]]:
        strengths, weaknesses = [], []

        # Сильные стороны
        if metrics["lexical_richness"]["score"] >= 75:
            strengths.append("Богатый словарный запас")
        if metrics["logical_connectors"]["score"] >= 70:
            strengths.append(f"Структурированная речь ({len(metrics['logical_connectors'].get('categories_found', []))} типов связей)")
        if metrics["specificity"]["score"] >= 70:
            strengths.append("Говорит конкретно: числа, факты, даты")
        if metrics["emotional_intel"]["score"] >= 65:
            strengths.append("Называет и осознаёт свои чувства")
        if metrics["active_voice"]["score"] >= 75:
            strengths.append("Активная позиция в речи (деятельный залог)")
        if metaphors["count"] >= 2:
            strengths.append("Образное нестандартное мышление")
        if domain["detected"]:
            strengths.append(domain["label"])
        if tone["balance"] == "healthy":
            strengths.append("Здоровый баланс позитива и реализма")

        # Зоны роста
        if metrics["lexical_richness"]["score"] < 40:
            weaknesses.append("Бедный словарный запас — много повторов")
        if metrics["sentence_rhythm"]["score"] < 40:
            weaknesses.append("Монотонный ритм предложений")
        if metrics["logical_connectors"]["score"] < 35:
            weaknesses.append("Мало логических связей между мыслями")
        if metrics["specificity"]["score"] < 35:
            weaknesses.append("Слишком общие формулировки без конкретики")
        if metrics["emotional_intel"]["score"] < 30:
            weaknesses.append("Нет эмоциональной глубины — текст роботизированный")
        if metrics["filler_penalty"]["score"] < 55:
            weaknesses.append(f"Слова-паразиты: {', '.join(f[0] for f in metrics['filler_penalty'].get('fillers_found', [])[:3])}")
        if tone["balance"] == "overly_positive":
            weaknesses.append("Чрезмерный позитив — может выглядеть неискренне")

        return strengths, weaknesses

    def _build_explanation(self, score: float, metrics: Dict, strengths: List[str], weaknesses: List[str]) -> str:
        level = (
            "Отличная коммуникация"      if score >= 80 else
            "Хорошая коммуникация"       if score >= 65 else
            "Средний уровень"            if score >= 45 else
            "Слабая коммуникация"
        )
        top_m = sorted(metrics.items(), key=lambda x: x[1]["score"], reverse=True)
        best_labels = [v["label"] for _, v in top_m[:2]]

        result = f"{level} ({score}/100). Сильные стороны: {', '.join(best_labels)}."
        if weaknesses:
            result += f" Зоны роста: {weaknesses[0]}."
        return result

    def _empty_result(self, reason: str) -> Dict:
        return {
            "score": 0.0,
            "explanation": reason,
            "details": {"metrics": {}, "strengths": [], "weaknesses": []},
        }
