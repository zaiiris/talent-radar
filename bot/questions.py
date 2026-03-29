import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
MODELS = ["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.0-pro"]

FIRST_QUESTION = "💡 *Вопрос 1*\n\nПочему ты хочешь участвовать в inVision U? Расскажи честно и своими словами — что тебя привело сюда?"

def call_ai(prompt):
    for model_name in MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Модель {model_name}: {e}")
    return None

def get_next_question(history, name):
    history_text = "\n".join([f"Вопрос: {h['q']}\nОтвет: {h['a']}" for h in history if h['a']])
    prompt = f"""Ты — умный интервьюер программы inVision U. Отвечай ТОЛЬКО на русском языке.
Кандидат: {name}
История: {history_text}
Задай ОДИН следующий адаптивный вопрос для оценки лидерства, роста, мотивации и аутентичности.
Максимум 2-3 предложения. Добавь эмодзи. Укажи номер вопроса ({len(history)+1} из ~6).
Напиши только текст вопроса:"""
    result = call_ai(prompt)
    if result:
        return result
    fallback = [
        "🚀 *Вопрос 2*\n\nОпиши момент когда ты взял(а) на себя ответственность за что-то важное.",
        "🌱 *Вопрос 3*\n\nКак ты изменился(ась) за последние 1-2 года?",
        "🌍 *Вопрос 4*\n\nКакую проблему в своём городе считаешь самой важной?",
        "✨ *Вопрос 5*\n\nЕсли бы у тебя были все ресурсы — что бы ты изменил(а)?",
        "💭 *Вопрос 6*\n\nЧто для тебя значит быть лидером?",
    ]
    idx = min(len(history) - 1, len(fallback) - 1)
    return fallback[idx]

def should_end_interview(history):
    if len(history) < 4:
        return False
    if len(history) >= 6:
        return True
    all_answers = " ".join([h['a'] for h in history if h['a']])
    return len(all_answers.split()) >= 200
