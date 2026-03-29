from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from questions import get_next_question, should_end_interview, FIRST_QUESTION
from adaptive import analyze_candidate, save_candidate
from states import NAME, AGE, CITY, SCHOOL, INTERVIEW

async def start(update, context):
    context.user_data.clear()
    context.user_data["telegram_id"] = update.effective_user.id
    context.user_data["telegram_username"] = update.effective_user.username or ""
    context.user_data["interview_history"] = []
    await update.message.reply_text(
        "🎓 *Добро пожаловать в inVision U!*\n\n"
        "Это официальная система подачи заявок на участие в программе. "
        "Я проведу тебя через анкету — это займёт около 5 минут.\n\n"
        "Для отмены напиши /cancel\n\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Как тебя зовут? (Имя и Фамилия)",
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update, context):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("📅 Сколько тебе лет?")
    return AGE

async def get_age(update, context):
    age_text = update.message.text.strip()
    if not age_text.isdigit() or not (10 <= int(age_text) <= 35):
        await update.message.reply_text("⚠️ Введи корректный возраст (от 10 до 35).")
        return AGE
    context.user_data["age"] = age_text
    await update.message.reply_text("🏙 Из какого ты города?")
    return CITY

async def get_city(update, context):
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text("🏫 В какой школе или университете ты учишься и в каком классе или курсе?")
    return SCHOOL

async def get_school(update, context):
    context.user_data["school"] = update.message.text.strip()
    await update.message.reply_text(
        "Отлично! Теперь начнём интервью.\n\n" + FIRST_QUESTION,
        parse_mode="Markdown"
    )
    context.user_data["interview_history"].append({"q": FIRST_QUESTION, "a": ""})
    return INTERVIEW

async def handle_interview(update, context):
    answer = update.message.text.strip()
    history = context.user_data["interview_history"]
    if history and history[-1]["a"] == "":
        history[-1]["a"] = answer
    else:
        history.append({"q": "", "a": answer})

    if should_end_interview(history):
        await update.message.reply_text("⏳ Обрабатываю твою анкету...", reply_markup=ReplyKeyboardRemove())
        analysis = analyze_candidate(context.user_data)
        save_candidate(context.user_data, analysis)
        name = context.user_data.get("name", "")
        await update.message.reply_text(
            f"🎉 *{name}, твоя анкета принята и сохранена!*\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 Комиссия проведёт финальную оценку.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "_Финальное решение принимает приёмная комиссия inVision U._\n\n"
            "Желаем удачи! 🌟",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    next_q = get_next_question([h for h in history if h["a"]], context.user_data["name"])
    await update.message.reply_text(next_q, parse_mode="Markdown")
    history.append({"q": next_q, "a": ""})
    return INTERVIEW

async def cancel(update, context):
    await update.message.reply_text("❌ Анкета отменена. Напиши /start чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
