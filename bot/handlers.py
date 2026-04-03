from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from states import NAME, AGE, CITY, SCHOOL, INTERVIEW
from questions import TEXTS, get_t, detect_language
from adaptive import get_next_question, should_end, analyze_candidate, save_candidate


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
    lang   = context.user_data.get("lang", "ru")

    if not answer:
        await update.message.reply_text(
            {"ru": "⚠️ Пожалуйста, напиши свой ответ.",
             "kz": "⚠️ Жауабыңды жаз.",
             "en": "⚠️ Please write your answer."}.get(lang, "⚠️ Please write your answer.")
        )
        return INTERVIEW

    history = context.user_data["history"]
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
