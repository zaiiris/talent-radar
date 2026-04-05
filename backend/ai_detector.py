"""
ai_detector.py
══════════════════════════════════════════════════════════════
ОТВЕЧАЕТ ЗА: Определение — написал ли кандидат текст сам,
             или использовал ChatGPT / Claude / другой AI.

ЧТО ДЕЛАЕТ:
  Три независимых слоя детекции:

  СЛОЙ 1 — Лексические эвристики (без API, мгновенно)
    - Клише-фразы характерные для AI-текстов
    - Абстрактность: плотность "пустых" слов без смысла
    - Избыточная вежливость и самопрезентация
    - Отсутствие личных деталей (дат, имён, мест)

  СЛОЙ 2 — Статистика текста (без API, мгновенно)
    - Равномерность длин предложений (AI пишет ритмично)
    - Перплексия: AI-текст слишком "предсказуем"
    - Плотность переходных слов (AI злоупотребляет)
    - Типичная AI-структура (intro + body + conclusion)

  СЛОЙ 3 — Claude перепроверка (API, финальный арбитр)
    - Claude оценивает текст как независимый эксперт
    - Возвращает вероятность + конкретные признаки

  КРОСС-ВАЛИДАЦИЯ:
    - Сравниваем стиль эссе со стилем ответов в боте
    - Если стили резко расходятся: кандидат писал не сам

  ИТОГ:
    final_probability = layer1*0.25 + layer2*0.25 + claude*0.50
    ai_flag = True если final_probability > 0.65

ИСПОЛЬЗУЕТСЯ В: scoring.py -> компонент authenticity
══════════════════════════════════════════════════════════════
"""

import re
import os
import json
import math
import statistics
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import anthropic

load_dotenv()

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


# ══════════════════════════════════════════════
# СЛОЙ 1 — ЛЕКСИЧЕСКИЕ ЭВРИСТИКИ
# ══════════════════════════════════════════════

AI_CLICHES_RU: List[Tuple[str, str]] = [
    ("вводное клише",              r'\b(данный опыт позволил мне|это позволило мне осознать)\b'),
    ("саморазвитие-штамп",         r'\b(я стремлюсь к (постоянному|непрерывному) (развитию|совершенствованию))\b'),
    ("в рамках проекта",           r'\b(в рамках (данного|этого) проекта)\b'),
    ("подводя итог",               r'\b(подводя итог|в заключение (хочу|следует|можно)|вышеизложенное)\b'),
    ("хочу отметить",              r'\b(хотел бы (также |особо )?(отметить|подчеркнуть|обратить внимание))\b'),
    ("безусловно/несомненно",      r'\b(безусловно[,\s]|несомненно[,\s]|очевидно что)\b'),
    ("ценные навыки",              r'\b(ценные (навыки|знания|умения)|бесценный опыт)\b'),
    ("активная позиция",           r'\b(активная (жизненная )?позиция|проактивный подход)\b'),
    ("говоря об опыте",            r'\b(говоря о (своём|моём) опыте)\b'),
    ("данная возможность",         r'\b(данная возможность|эта возможность позволит мне)\b'),
    ("эффективное взаимодействие", r'\b(эффективное взаимодействие|конструктивный диалог)\b'),
    ("нацелен на результат",       r'\b(нацелен на результат|ориентирован на достижение)\b'),
    ("внести вклад",               r'\b(внести (свой |весомый )?вклад)\b'),
    ("AI-нумерация",               r'\b(во-первых[,\s].{5,80}во-вторых)\b'),
]

AI_CLICHES_EN: List[Tuple[str, str]] = [
    ("in conclusion",    r'\b(in conclusion[,\s]|to summarize[,\s]|to conclude[,\s])\b'),
    ("passionate about", r'\b(i am (deeply |truly |genuinely )?passionate about)\b'),
    ("journey",          r'\b(throughout my (journey|life|academic career))\b'),
    ("leveraging",       r'\b(leveraging my (skills|experience|expertise))\b'),
    ("committed to",     r'\b(i am (deeply |fully )?committed to)\b'),
    ("worth noting",     r'\b(it is (worth|important to) (noting|mention))\b'),
    ("holistic",         r'\b(holistic approach|well-rounded (individual|person))\b'),
]

ABSTRACT_WORDS = [
    "развитие", "потенциал", "возможности", "стремление", "цели", "ценности",
    "принципы", "видение", "миссия", "эффективность", "компетенции", "навыки",
    "опыт", "знания", "умения", "качества", "способности", "перспективы",
    "результаты", "задачи", "подход", "реализация", "успех", "достижения",
]

TRANSITION_WORDS = [
    "таким образом", "следовательно", "в результате", "кроме того",
    "помимо этого", "более того", "при этом", "тем не менее",
    "однако", "в то же время", "с одной стороны", "с другой стороны",
    "во-первых", "во-вторых", "в-третьих", "наконец",
]

PERSONAL_MARKERS = [
    r'\b(20\d{2}|19\d{2})\b',
    r'\xab.{3,40}\xbb',
    r'\b[А-Я][а-я]+ (университет|школа|лицей|колледж|академия)\b',
    r'\b(мой (друг|одноклассник|учитель|наставник|тренер))\b',
    r'\b(в (январе|феврале|марте|апреле|мае|июне|июле|августе|сентябре|октябре|ноябре|декабре))\b',
]


# ══════════════════════════════════════════════
# ГЛАВНЫЙ КЛАСС
# ══════════════════════════════════════════════

class AIDetector:
    """
    Трёхслойный детектор AI-текста.

    Использование:
        detector = AIDetector()
        result = await detector.analyze(essay="...", bot_answers="...")
    """

    AI_FLAG_THRESHOLD = 0.65

    async def analyze(self, essay: str = "", bot_answers: str = "") -> Dict:
        """
        Полный анализ аутентичности текста.

        Returns:
            {
              "ai_probability": 0.0-1.0,
              "ai_flag": bool,
              "score": 0-100,        <- балл аутентичности для scoring.py
              "explanation": "...",
              "signals": [...],
              "details": { layer1, layer2, layer3, cross_validation }
            }
        """
        text = essay.strip()

        if not text or len(text) < 60:
            return self._short_text_result()

        layer1 = self._layer1_lexical(text)
        layer2 = self._layer2_statistical(text)
        layer3 = await self._layer3_claude(text)
        cross  = self._cross_validate(essay, bot_answers)

        base_prob = (
            layer1["probability"] * 0.25
            + layer2["probability"] * 0.25
            + layer3["probability"] * 0.50
        )
        final_prob = round(max(0.0, min(base_prob + cross["adjustment"], 1.0)), 3)
        ai_flag = final_prob >= self.AI_FLAG_THRESHOLD
        score   = round((1 - final_prob) * 100, 1)

        all_signals = (
            layer1["signals"] + layer2["signals"]
            + layer3["signals"] + cross["signals"]
        )

        return {
            "ai_probability": final_prob,
            "ai_flag": ai_flag,
            "score": score,
            "explanation": self._build_explanation(final_prob, layer1, layer2, layer3, cross),
            "signals": all_signals,
            "details": {
                "layer1_lexical":     layer1,
                "layer2_statistical": layer2,
                "layer3_claude":      layer3,
                "cross_validation":   cross,
            },
        }

    # ──────────────────────────────────────────
    # СЛОЙ 1 — ЛЕКСИКА
    # ──────────────────────────────────────────

    def _layer1_lexical(self, text: str) -> Dict:
        text_lower = text.lower()
        signals = []
        prob = 0.0

        # Клише
        found_cliches = []
        for label, pattern in (AI_CLICHES_RU + AI_CLICHES_EN):
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_cliches.append(label)
                prob += 0.08
        if found_cliches:
            signals.append(f"AI-клише ({len(found_cliches)}): {', '.join(found_cliches[:4])}")

        # Плотность абстракций
        words = re.findall(r'\b[а-яёa-z]+\b', text_lower)
        abstract_density = 0.0
        if words:
            abstract_count = sum(words.count(w) for w in ABSTRACT_WORDS)
            abstract_density = abstract_count / len(words)
            if abstract_density > 0.10:
                prob += 0.20
                signals.append(f"Избыток абстракций: {round(abstract_density*100)}% слов")
            elif abstract_density > 0.07:
                prob += 0.10
                signals.append(f"Высокая абстрактность: {round(abstract_density*100)}% слов")

        # Переходные слова
        t_count = sum(1 for tw in TRANSITION_WORDS if tw in text_lower)
        if words:
            t_density = t_count / (len(words) / 100)
            if t_density > 3.0:
                prob += 0.15
                signals.append(f"Слишком много переходных слов ({t_count} шт)")
            elif t_density > 1.5:
                prob += 0.07

        # Личные детали
        personal_hits = sum(
            1 for p in PERSONAL_MARKERS
            if re.search(p, text, re.IGNORECASE)
        )
        if personal_hits == 0:
            prob += 0.12
            signals.append("Нет личных деталей: дат, имён, мест")
        elif personal_hits == 1:
            prob += 0.05

        # Идеализированная самопрезентация
        perfect = len(re.findall(
            r'\b(всегда|постоянно|неизменно)\s+(стремлюсь|стараюсь|работаю|развиваюсь)\b',
            text_lower
        ))
        if perfect >= 2:
            prob += 0.10
            signals.append("Идеализированная самопрезентация")

        return {
            "probability": round(min(prob, 1.0), 3),
            "signals": signals,
            "cliches_found": found_cliches,
            "abstract_density": round(abstract_density, 3),
            "personal_markers": personal_hits,
        }

    # ──────────────────────────────────────────
    # СЛОЙ 2 — СТАТИСТИКА
    # ──────────────────────────────────────────

    def _layer2_statistical(self, text: str) -> Dict:
        signals = []
        prob = 0.0

        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 8]
        if len(sentences) < 3:
            return {"probability": 0.0, "signals": ["Мало предложений для анализа"], "cv": None}

        lengths = [len(s.split()) for s in sentences]
        mean_len  = statistics.mean(lengths)
        stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev_len / mean_len if mean_len > 0 else 0

        # Коэффициент вариации длин (CV)
        if cv < 0.20:
            prob += 0.25
            signals.append(f"Слишком ровные предложения CV={round(cv,2)} — AI-паттерн")
        elif cv < 0.30:
            prob += 0.12
            signals.append(f"Умеренно равномерные предложения CV={round(cv,2)}")

        # "Золотая середина" длины — зона AI
        if 17 <= mean_len <= 23:
            prob += 0.10
            signals.append(f"Идеальная длина предложений {round(mean_len,1)} слов")

        # Одинаковые по размеру абзацы
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 20]
        if len(paragraphs) >= 3:
            para_lens = [len(p.split()) for p in paragraphs]
            para_mean = statistics.mean(para_lens)
            para_cv   = statistics.stdev(para_lens) / para_mean if para_mean > 0 else 1
            if para_cv < 0.25:
                prob += 0.15
                signals.append("Абзацы одинакового размера — шаблонная структура")

        # Повторяемость слов
        words = re.findall(r'\b[а-яёa-z]{4,}\b', text.lower())
        if words:
            freq = {}
            for w in words:
                freq[w] = freq.get(w, 0) + 1
            top5 = sorted(freq.values(), reverse=True)[:5]
            repeat_score = sum(top5) / len(words)
            if repeat_score > 0.18:
                prob += 0.10
                signals.append(f"Высокая повторяемость слов ({round(repeat_score*100)}%)")

        # Отсутствие живых пунктуационных "неровностей"
        informal = len(re.findall(r'(\.{2,}|—|–|!{2,}|\?{2,})', text))
        if informal == 0 and len(text) > 300:
            prob += 0.08
            signals.append("Идеально ровная пунктуация без живых неровностей")

        return {
            "probability": round(min(prob, 1.0), 3),
            "signals": signals,
            "cv_sentences": round(cv, 3),
            "mean_sentence_len": round(mean_len, 1),
            "paragraph_count": len(paragraphs),
        }

    # ──────────────────────────────────────────
    # СЛОЙ 3 — CLAUDE АРБИТР
    # ──────────────────────────────────────────

    async def _layer3_claude(self, text: str) -> Dict:
        prompt = f"""Ты — эксперт-лингвист. Определи: написал этот текст живой человек или AI (ChatGPT/Claude)?

Текст:
\"\"\"
{text[:2000]}
\"\"\"

ПРИЗНАКИ AI: клише ("данный опыт позволил"), идеальная структура intro-body-conclusion, нет конкретных дат и имён, равномерные предложения, избыток абстракций.

ПРИЗНАКИ ЖИВОГО: личные детали, неповторимые истории, живые интонации, иногда неидеальные формулировки, субъективные эмоции.

Верни ТОЛЬКО JSON без markdown:
{{
  "probability": <0.0-1.0, где 1.0=точно AI>,
  "confidence": <"high"|"medium"|"low">,
  "top_signals": ["<конкретный признак AI из текста>"],
  "human_signals": ["<что указывает на живого человека>"],
  "verdict": "<одно предложение>"
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
            return {
                "probability":    float(data.get("probability", 0.3)),
                "confidence":     data.get("confidence", "medium"),
                "signals":        data.get("top_signals", []),
                "human_signals":  data.get("human_signals", []),
                "verdict":        data.get("verdict", ""),
            }
        except Exception as e:
            return {
                "probability": 0.30,
                "confidence": "low",
                "signals": [f"Claude недоступен: {e}"],
                "human_signals": [],
                "verdict": "",
            }

    # ──────────────────────────────────────────
    # КРОСС-ВАЛИДАЦИЯ
    # ──────────────────────────────────────────

    def _cross_validate(self, essay: str, bot_answers: str) -> Dict:
        """
        Сравниваем стиль эссе и ответов бота.
        Если стили СИЛЬНО расходятся — эссе писал AI, ответы — человек.
        """
        if not essay or not bot_answers or len(bot_answers) < 50:
            return {"adjustment": 0.0, "signals": [], "similarity": None, "skipped": True}

        def features(text: str) -> Optional[Dict]:
            sents = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5]
            words = re.findall(r'\b[а-яёa-z]+\b', text.lower())
            if not words or not sents:
                return None
            return {
                "avg_sent":    len(words) / len(sents),
                "ttr":         len(set(words)) / len(words),
                "transitions": sum(1 for tw in TRANSITION_WORDS if tw in text.lower()) / (len(words)/100 + 0.001),
                "i_density":   words.count("я") / len(words),
            }

        fe = features(essay)
        fb = features(bot_answers)

        if not fe or not fb:
            return {"adjustment": 0.0, "signals": [], "similarity": None, "skipped": True}

        diffs = []
        for key in fe:
            base = max(abs(fe[key]), abs(fb[key]), 0.001)
            diffs.append(abs(fe[key] - fb[key]) / base)

        similarity = round(1 - min(sum(diffs)/len(diffs), 1.0), 3)
        signals = []
        adjustment = 0.0

        if similarity < 0.30:
            adjustment = +0.15
            signals.append(f"Стиль эссе и бота расходятся ({round(similarity*100)}% схожесть) — признак AI в эссе")
        elif similarity < 0.50:
            adjustment = +0.07
            signals.append(f"Умеренное расхождение стиля ({round(similarity*100)}% схожесть)")
        elif similarity > 0.75:
            adjustment = -0.07
            signals.append(f"Стиль совпадает ({round(similarity*100)}%) — признак аутентичности")

        return {
            "adjustment": round(adjustment, 3),
            "signals": signals,
            "similarity": similarity,
            "skipped": False,
        }

    # ──────────────────────────────────────────
    # ВСПОМОГАТЕЛЬНЫЕ
    # ──────────────────────────────────────────

    def _short_text_result(self) -> Dict:
        return {
            "ai_probability": 0.20,
            "ai_flag": False,
            "score": 80.0,
            "explanation": "Текст слишком короткий для анализа — нейтральная оценка.",
            "signals": ["Эссе очень короткое"],
            "details": {
                "layer1_lexical":     {"probability": 0.20, "signals": []},
                "layer2_statistical": {"probability": 0.20, "signals": []},
                "layer3_claude":      {"probability": 0.20, "signals": []},
                "cross_validation":   {"adjustment": 0.0,  "signals": [], "skipped": True},
            },
        }

    def _build_explanation(self, prob: float, l1: Dict, l2: Dict, l3: Dict, cross: Dict) -> str:
        verdict = (
            "ВЫСОКАЯ вероятность AI-текста"  if prob >= 0.75 else
            "Возможен AI-текст"              if prob >= 0.50 else
            "Небольшие признаки AI"          if prob >= 0.35 else
            "Текст выглядит аутентично"
        )
        flag = "⛔" if prob >= 0.65 else ("⚠️" if prob >= 0.35 else "✅")
        cross_note = ""
        if not cross.get("skipped") and cross.get("similarity") is not None:
            cross_note = f" | Кросс-вал схожесть: {round(cross['similarity']*100)}%"
        return (
            f"{flag} {verdict} ({round(prob*100)}%). "
            f"L1={round(l1['probability'],2)} "
            f"L2={round(l2['probability'],2)} "
            f"L3={round(l3['probability'],2)}"
            f"{cross_note}."
        )
