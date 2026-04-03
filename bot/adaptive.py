import uuid
import json
import os
from datetime import datetime

import google.generativeai as genai

from config import MODELS, RESULTS_FILE, logger
from questions import TEXTS


# ─────────────────────────────────────────────
# Базовый AI-вызов
# ─────────────────────────────────────────────

def call_ai(prompt: str) -> str:
    for model_name in MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Модель {model_name}: {e}")
    logger.error("AI failed completely — все модели недоступны")
    return None


# ─────────────────────────────────────────────
# Поведенческий анализ истории
# ─────────────────────────────────────────────

def build_history_context(history: list) -> dict:
    answered = [h for h in history if h.get("q") and h.get("a")]

    word_counts   = [len(h["a"].split()) for h in answered]
    avg_words     = sum(word_counts) / len(word_counts) if word_counts else 0
    evasion_count = sum(1 for w in word_counts if w < 8)

    def classify(n):
        if n < 20:  return "short"
        if n < 60:  return "medium"
        return "long"

    rhythm = [classify(w) for w in word_counts]
    skipped_or_empty = len(history) - len(answered)

    trend = "flat"
    if len(word_counts) >= 3:
        if word_counts[-1] > word_counts[0] * 1.3:
            trend = "growing"
        elif word_counts[-1] < word_counts[0] * 0.7:
            trend = "shrinking"

    return {
        "answered":         answered,
        "avg_words":        round(avg_words),
        "rhythm":           rhythm,
        "evasion_count":    evasion_count,
        "trend":            trend,
        "skipped_or_empty": skipped_or_empty,
        "q_num":            len(answered) + 1,
    }


# ─────────────────────────────────────────────
# Генерация следующего адаптивного вопроса
# ─────────────────────────────────────────────

def get_next_question(history: list, name: str, lang: str) -> str:
    ai_instruction = TEXTS[lang]["ai_instruction"]
    ctx = build_history_context(history)

    history_text = "\n".join([
        f"Q: {h.get('q', '')}\nA: {h.get('a', '')} [{len(h.get('a', '').split())} words]"
        for h in history
    ])

    behavior_block = (
        f"Behavioral signals:\n"
        f"- Average answer length: {ctx['avg_words']} words\n"
        f"- Answer rhythm: {' -> '.join(ctx['rhythm']) if ctx['rhythm'] else 'n/a'}\n"
        f"- Trend: {ctx['trend']} (answers getting {ctx['trend']})\n"
        f"- Evasive answers (<8 words): {ctx['evasion_count']}\n"
        f"- Unanswered/skipped entries: {ctx['skipped_or_empty']}"
    )

    prompt = (
        f"You are an interviewer for the inVision U youth leadership program.\n"
        f"{ai_instruction}\n\n"
        f"Candidate: {name}\n"
        f"Interview so far:\n{history_text}\n\n"
        f"{behavior_block}\n\n"
        f"Task: Generate the NEXT adaptive interview question based on BOTH "
        f"the content AND the behavioral signals above.\n\n"
        f"If answers are short or evasive — probe deeper, ask to elaborate.\n"
        f"If answers are growing and rich — explore a new dimension.\n"
        f"If candidate is repeating patterns — shift the angle.\n\n"
        f"Rules:\n"
        f"- ONE question only\n"
        f"- Build naturally on previous answers\n"
        f"- Add an emoji at the start\n"
        f"- Mention question number ({ctx['q_num']} of ~5)\n"
        f"- Max 2-3 sentences\n"
        f"- Write ONLY the question text, nothing else\n"
        f"- NO markdown formatting like ** or __"
    )

    result = call_ai(prompt)

    if result and len(result.strip()) > 10:
        result = result.replace("**", "").replace("__", "").replace("##", "").strip()
        return result

    fallback_list = TEXTS[lang]["fallback"]
    idx = min(ctx["q_num"] - 2, len(fallback_list) - 1)
    return fallback_list[max(0, idx)]


# ─────────────────────────────────────────────
# Логика завершения интервью
# ─────────────────────────────────────────────

def should_end(history: list) -> bool:
    answered = [h for h in history if h.get("a")]
    if len(answered) < 4:
        return False
    total_words = sum(len(h["a"].split()) for h in answered)
    if len(answered) >= 5 and total_words >= 120:
        return True
    if len(answered) >= 7:
        return True
    return False


# ─────────────────────────────────────────────
# Скоринг кандидата
# ─────────────────────────────────────────────

def analyze_candidate(data: dict) -> dict:
    lang    = data.get("lang", "ru")
    history = data.get("history", [])
    answers_text = "\n".join([
        f"Q: {h['q']}\nA: {h['a']}"
        for h in history if h.get("a")
    ])

    prompt = (
        f"You are the TalentRadar AI scoring system for inVision U.\n\n"
        f"Candidate: {data['name']}, age {data['age']}, "
        f"city {data['city']}, school {data.get('school', '')}\n"
        f"Language: {lang}\n\n"
        f"Interview transcript:\n{answers_text}\n\n"
        f"Score on 4 criteria (0-100):\n"
        f"- leadership:   leadership potential\n"
        f"- trajectory:   growth trajectory and dynamics\n"
        f"- motivation:   motivation and values authenticity\n"
        f"- authenticity: genuine voice, not AI-generated text\n\n"
        f"Formula: total = leadership*0.3 + trajectory*0.25 + motivation*0.3 + authenticity*0.15\n\n"
        f"Be strict. Most candidates: 40-65. Exceptional only: 80+.\n\n"
        f"AI-generated text — flag ONLY if candidate shows:\n"
        f"- overly structured answers (numbered lists, perfect paragraphs)\n"
        f"- generic phrases with no personal detail\n"
        f"- unnatural consistency and polish across all answers\n"
        f"- absence of hesitation, typos, or colloquial language\n"
        f"- repetitive sentence patterns\n\n"
        f"Respond ONLY with valid JSON:\n"
        f"{{\n"
        f'  "scores": {{\n'
        f'    "leadership": <0-100>,\n'
        f'    "trajectory": <0-100>,\n'
        f'    "motivation": <0-100>,\n'
        f'    "authenticity": <0-100>\n'
        f"  }},\n"
        f'  "explanations": {{\n'
        f'    "leadership": "why this score — 1 sentence",\n'
        f'    "trajectory": "why this score — 1 sentence",\n'
        f'    "motivation": "why this score — 1 sentence",\n'
        f'    "authenticity": "why this score — 1 sentence"\n'
        f"  }},\n"
        f'  "total": <calculated total>,\n'
        f'  "strengths": ["strength 1", "strength 2"],\n'
        f'  "growth_areas": ["area 1"],\n'
        f'  "recommendation": "Рекомендован" or "На рассмотрение" or "Не рекомендован",\n'
        f'  "summary": "2-3 sentences for the committee",\n'
        f'  "ai_text_detected": true or false,\n'
        f'  "ai_text_reason": "brief reason if detected, else null"\n'
        f"}}"
    )

    result = call_ai(prompt)
    if result:
        try:
            clean = result.strip()
            if "```" in clean:
                parts = clean.split("```")
                clean = parts[1] if len(parts) > 1 else parts[0]
            if clean.startswith("json"):
                clean = clean[4:]
            start = clean.find("{")
            end   = clean.rfind("}") + 1
            if start != -1 and end > start:
                clean = clean[start:end]
            return json.loads(clean.strip())
        except Exception as e:
            logger.error(f"JSON error: {e} | Raw: {result[:200]}")

    return {
        "scores": {"leadership": 60, "trajectory": 60, "motivation": 65, "authenticity": 70},
        "explanations": {
            "leadership":   "Could not evaluate — AI unavailable",
            "trajectory":   "Could not evaluate — AI unavailable",
            "motivation":   "Could not evaluate — AI unavailable",
            "authenticity": "Could not evaluate — AI unavailable"
        },
        "total": 63,
        "strengths":      ["Completed all stages", "Showed readiness to participate"],
        "growth_areas":   ["Requires detailed review by the committee"],
        "recommendation": "На рассмотрение",
        "summary":        "Application received. Manual review recommended.",
        "ai_text_detected": False,
        "ai_text_reason":   None
    }


# ─────────────────────────────────────────────
# Сохранение кандидата
# ─────────────────────────────────────────────

def save_candidate(data: dict, analysis: dict):
    record = {
        "id":        f"candidate_{uuid.uuid4().hex}",
        "timestamp": datetime.now().isoformat(),
        "language":  data.get("lang", "ru"),
        "personal": {
            "name":              data["name"],
            "age":               data["age"],
            "city":              data["city"],
            "school":            data.get("school", ""),
            "telegram_id":       data.get("telegram_id", ""),
            "telegram_username": data.get("telegram_username", "")
        },
        "interview":           data.get("history", []),
        "talentrada_analysis": analysis
    }

    candidates = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            try:
                candidates = json.load(f)
            except Exception:
                candidates = []

    candidates.append(record)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    logger.info(
        f"✅ Saved: {data['name']} | "
        f"Score: {analysis.get('total')} | "
        f"{analysis.get('recommendation')}"
    )
