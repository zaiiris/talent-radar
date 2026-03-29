from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from handlers import start, get_name, get_age, get_city, get_school, handle_interview, cancel
from config import TELEGRAM_TOKEN
from states import NAME, AGE, CITY, SCHOOL, INTERVIEW

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            SCHOOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_school)],
            INTERVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_interview)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    print("TalentRadar бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
