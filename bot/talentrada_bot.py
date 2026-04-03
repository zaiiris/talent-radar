import uuid
import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import google.generativeai as genai

# =============================================
TELEGRAM_TOKEN = "8607632393:AAHHjpT_qv66HerNzQHarFT51TGIoqVr_wU"
GEMINI_API_KEY = "AIzaSyD1qDLyDIFDSeibWPsSAOWnh_y3XH9-bbo"
RESULTS_FILE   = "candidates.json"
# =============================================

genai.configure(api_key=GEMINI_API_KEY)
MODELS = ["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.0-pro"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(NAME, AGE, CITY, SCHOOL, INTERVIEW) = range(5)

# ─────────────────────────────────────────────
# Тексты на 3 языках
# ─────────────────────────────────────────────
TEXTS = {
    "ru": {
        "welcome": (
            "🎓 *Добро пожаловать в inVision U!*\n\n"
            "Это официальная система подачи заявок на участие в программе. "
            "Я проведу тебя через анкету — это займёт около 5 минут.\n\n"
            "Для отмены напиши /cancel\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "Как тебя зовут? (Имя и Фамилия)"
        ),
        "age":       "📅 Сколько тебе лет?",
        "age_error": "⚠️ Введи корректный возраст (от 10 до 35).",
        "city":      "🏙 Из какого ты города?",
        "school":    "🏫 В какой школе или университете ты учишься и в каком классе или курсе?",
        "start_interview": "Отлично! Теперь начнём интервью.\n\n",
        "processing": "⏳ Обрабатываю твою анкету...",
        "done": (
            "🎉 *{name}, твоя анкета принята и сохранена!*\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 Комиссия проведёт финальную оценку.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "_Финальное решение принимает приёмная комиссия inVision U._\n\n"
            "Желаем удачи! 🌟"
        ),
        "cancelled": "❌ Анкета отменена. Напиши /start чтобы начать заново.",
        "first_q": (
            "💡 *Вопрос 1 из ~5*\n\n"
            "Почему ты хочешь участвовать в inVision U? "
            "Расскажи честно и своими словами — что тебя привело сюда?"
        ),
        "fallback": [
            "🚀 *Вопрос 2*\n\nОпиши момент когда ты взял(а) на себя ответственность за что-то важное. Что произошло?",
            "🌱 *Вопрос 3*\n\nКак ты изменился(ась) за последние 1-2 года?",
            "🌍 *Вопрос 4*\n\nКакую проблему в своём городе считаешь самой важной?",
            "✨ *Вопрос 5*\n\nЕсли бы у тебя были все ресурсы — что бы ты изменил(а)?",
            "💭 *Вопрос 6*\n\nЧто для тебя значит быть лидером?",
        ],
        "ai_instruction": "Отвечай ТОЛЬКО на русском языке.",
    },
    "kz": {
        "welcome": (
            "🎓 *inVision U-ға қош келдің!*\n\n"
            "Бұл бағдарламаға өтінім беру жүйесі. "
            "Мен сені анкета арқылы жетелеймін — бұл шамамен 5 минут алады.\n\n"
            "Тоқтату үшін /cancel жаз\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "Атың-жөнің кім? (Толық аты-жөні)"
        ),
        "age":       "📅 Жасың нешеде?",
        "age_error": "⚠️ Дұрыс жасты енгіз (10-35 арасында).",
        "city":      "🏙 Қай қаладансың?",
        "school":    "🏫 Қай мектепте немесе университетте оқисың және қай сыныпта немесе курста?",
        "start_interview": "Керемет! Енді сұхбат басталады.\n\n",
        "processing": "⏳ Анкетаңды өңдеп жатырмын...",
        "done": (
            "🎉 *{name}, анкетаң қабылданды және сақталды!*\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 Комиссия түпкілікті бағалауды жүргізеді.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "_Түпкілікті шешімді inVision U қабылдау комиссиясы қабылдайды._\n\n"
            "Сәттілік тілейміз! 🌟"
        ),
        "cancelled": "❌ Анкета тоқтатылды. Қайта бастау үшін /start жаз.",
        "first_q": (
            "💡 *1-сұрақ (~5-тен)*\n\n"
            "Неге inVision U-ға қатысқың келеді? Шынайы және өз сөзіңмен айт."
        ),
        "fallback": [
            "🚀 *2-сұрақ*\n\nМаңызды нәрсеге жауапкершілік алған сәтіңді сипатта.",
            "🌱 *3-сұрақ*\n\nСоңғы 1-2 жылда қалай өзгердің?",
            "🌍 *4-сұрақ*\n\nҚалаңдағы ең маңызды мәселе қандай?",
            "✨ *5-сұрақ*\n\nБарлық ресурстарың болса — нені өзгертер едің?",
            "💭 *6-сұрақ*\n\nСен үшін көшбасшы болу деген не?",
        ],
        "ai_instruction": "Тек қазақ тілінде жауап бер.",
    },
    "en": {
        "welcome": (
            "🎓 *Welcome to inVision U!*\n\n"
            "This is the official application system for the program. "
            "I'll guide you through the form — it takes about 5 minutes.\n\n"
            "To cancel, type /cancel\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "What's your full name?"
        ),
        "age":       "📅 How old are you?",
        "age_error": "⚠️ Please enter a valid age (between 10 and 35).",
        "city":      "🏙 What city are you from?",
        "school":    "🏫 What school or university do you attend and what grade or year are you in?",
        "start_interview": "Great! Let's start the interview.\n\n",
        "processing": "⏳ Processing your application...",
        "done": (
            "🎉 *{name}, your application has been received and saved!*\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 The committee will conduct a final evaluation.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "_The final decision is made by the inVision U admissions committee._\n\n"
            "We wish you the best of luck! 🌟"
        ),
        "cancelled": "❌ Application cancelled. Type /start to begin again.",
        "first_q": (
            "💡 *Question 1 of ~5*\n\n"
            "Why do you want to participate in inVision U? "
            "Tell us honestly in your own words."
        ),
        "fallback": [
            "🚀 *Question 2*\n\nDescribe a moment when you took responsibility for something important.",
            "🌱 *Question 3*\n\nHow have you changed over the last 1-2 years?",
            "🌍 *Question 4*\n\nWhat problem in your city do you consider most important?",
            "✨ *Question 5*\n\nIf you had all the resources — what would you change?",
            "💭 *Question 6*\n\nWhat does being a leader mean to you?",
        ],
        "ai_instruction": "Respond ONLY in English.",
    }
}


# ─────────────────────────────────────────────
# Вспомогательные функции
# ─────────────────────────────────────────────

def detect_language(text: str) -> str:
    kz_chars = set("әіңғүұқөһ")
    text_lower = text.lower()
    if sum(1 for c in text_lower if c in kz_chars) > 0:
        return "kz"
    ru_chars = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    en_chars = set("abcdefghijklmnopqrstuvwxyz")
    ru_count = sum(1 for c in text_lower if c in ru_chars)
    en_count = sum(1 for c in text_lower if c in en_chars)
    if en_count > ru_count * 1.5:
        return "en"
    return "ru"


def get_t(context, key):
    lang = context.user_data.get("lang", "ru")
    return TEXTS[lang][key]


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
    """
    Принимает ПОЛНЫЙ history — включая записи без ответа.
    Извлекает engagement-сигналы для AI.
    """
    answered = [h for h in history if h.get("q") and h.get("a")]

    word_counts   = [len(h["a"].split()) for h in answered]
    avg_words     = sum(word_counts) / len(word_counts) if word_counts else 0
    evasion_count = sum(1 for w in word_counts if w < 8)

    def classify(n):
        if n < 20:  return "short"
        if n < 60:  return "medium"
        return "long"

    rhythm = [classify(w) for w in word_counts]

    # ФИХ 1: skipped_or_empty — engagement signal
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
# Генерация следующего вопроса
# ─────────────────────────────────────────────

def get_next_question(history: list, name: str, lang: str) -> str:
    """
    ФИХ 1: history_text строится из полного history (h.get вместо фильтра).
    AI видит сбитый flow, пустые Q и A — это реальные поведенческие сигналы.
    """
    ai_instruction = TEXTS[lang]["ai_instruction"]
    ctx = build_history_context(history)

    # ФИХ 1: итерируем по ПОЛНОМУ history, не только по answered
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
# ФИХ 3 + ФИХ 4: Скоринг с explanations + усиленный AI-detection
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
        # ФИХ 4: чёткие критерии AI-detection
        f"AI-generated text — flag ONLY if candidate shows:\n"
        f"- overly structured answers (numbered lists, perfect paragraphs)\n"
        f"- generic phrases with no personal detail\n"
        f"- unnatural consistency and polish across all answers\n"
        f"- absence of hesitation, typos, or colloquial language\n"
        f"- repetitive sentence patterns\n\n"
        # ФИХ 3: explanations в JSON
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
# Сохранение результата
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


# ─────────────────────────────────────────────
# Telegram-хэндлеры
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["telegram_id"]       = update.effective_user.id
    context.user_data["telegram_username"] = update.effective_user.username or ""
    context.user_data["history"]           = []
    context.user_data["lang"]              = "ru"
    await update.message.reply_text(
        TEXTS["ru"]["welcome"],
        parse_mode="Markdown"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    lang = detect_language(text)
    context.user_data["lang"] = lang
    context.user_data["name"] = text
    await update.message.reply_text(get_t(context, "age"))
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age_text = update.message.text.strip()
    if not age_text.isdigit() or not (10 <= int(age_text) <= 35):
        await update.message.reply_text(get_t(context, "age_error"))
        return AGE
    context.user_data["age"] = age_text
    await update.message.reply_text(get_t(context, "city"))
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text(get_t(context, "school"))
    return SCHOOL


async def get_school(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["school"] = update.message.text.strip()
    first_q = get_t(context, "first_q")
    await update.message.reply_text(
        get_t(context, "start_interview") + first_q,
        parse_mode="Markdown"
    )
    context.user_data["history"].append({"q": first_q, "a": ""})
    return INTERVIEW


async def handle_interview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text.strip()

    if not answer:
        lang = context.user_data.get("lang", "ru")
        await update.message.reply_text(
            {"ru": "⚠️ Пожалуйста, напиши свой ответ.",
             "kz": "⚠️ Жауабыңды жаз.",
             "en": "⚠️ Please write your answer."}.get(lang, "⚠️ Please write your answer.")
        )
        return INTERVIEW

    history = context.user_data["history"]

    # ФИХ 2: убрали else — больше нет мусорных {"q": "", "a": answer}
    if history and history[-1]["a"] == "":
        history[-1]["a"] = answer

    if should_end(context.user_data["history"]):
        await update.message.reply_text(
            get_t(context, "processing"),
            reply_markup=ReplyKeyboardRemove()
        )
        analysis = analyze_candidate(context.user_data)
        save_candidate(context.user_data, analysis)
        name = context.user_data.get("name", "")
        await update.message.reply_text(
            get_t(context, "done").format(name=name),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    lang = context.user_data.get("lang", "ru")

    # Передаём ПОЛНЫЙ history — AI видит весь ритм интервью
    next_q = get_next_question(
        context.user_data["history"],
        context.user_data["name"],
        lang
    )
    await update.message.reply_text(next_q)
    context.user_data["history"].append({"q": next_q, "a": ""})
    return INTERVIEW


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        get_t(context, "cancelled"),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITY:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            SCHOOL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_school)],
            INTERVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_interview)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    logger.info("TalentRadar бот запущен! 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
