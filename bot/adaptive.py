import json
import os
from datetime import datetime
from questions import call_ai

RESULTS_FILE = "candidates.json"

def analyze_candidate(data):
    history = data.get("interview_history", [])
    answers_text = "\n".join([f"В: {h['q']}\nО: {h['a']}" for h in history if h['a']])
    prompt = f"""Ты — AI-система TalentRadar для отбора кандидатов inVision U.
Кандидат: {data['name']}, {data['age']} лет, {data['city']}, {data.get('school','')}
Интервью: {answers_text}
Оцени по 4 критериям (0-100): leadership, trajectory, motivation, authenticity
Total = leadership*0.3 + trajectory*0.25 + motivation*0.3 + authenticity*0.15
Отвечай ТОЛЬКО JSON:
{{"scores":{{"leadership":<0-100>,"trajectory":<0-100>,"motivation":<0-100>,"authenticity":<0-100>}},"total":<итог>,"strengths":["...","..."],"growth_areas":["..."],"recommendation":"Рекомендован или На рассмотрение или Не рекомендован","summary":"2-3 предложения","ai_text_detected":true/false}}"""
    result = call_ai(prompt)
    if result:
        try:
            if "```" in result:
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            return json.loads(result.strip())
        except:
            pass
    return {"scores":{"leadership":60,"trajectory":60,"motivation":65,"authenticity":70},"total":63,"strengths":["Прошёл все этапы"],"growth_areas":["Требует анализа"],"recommendation":"На рассмотрение","summary":"Ручная проверка рекомендована.","ai_text_detected":False}

def save_candidate(data, analysis):
    record = {
        "id": f"candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "personal": {
            "name": data["name"],
            "age": data["age"],
            "city": data["city"],
            "school": data.get("school",""),
            "telegram_id": data.get("telegram_id",""),
            "telegram_username": data.get("telegram_username","")
        },
        "interview": data.get("interview_history",[]),
        "talentrada_analysis": analysis
    }
    candidates = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE,"r",encoding="utf-8") as f:
            try:
                candidates = json.load(f)
            except:
                candidates = []
    candidates.append(record)
    with open(RESULTS_FILE,"w",encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
    print(f"Сохранён: {data['name']} | Score: {analysis.get('total')} | {analysis.get('recommendation')}")
