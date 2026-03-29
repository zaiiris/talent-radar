# TalentRadar - Система интеллектуального отбора кандидатов

>  Видим потенциал там, где другие видят анкету.

Платформа для приёмной комиссии **inVision U** - инновационного университета с 100% грантами от inDrive, Казахстан. Система автоматизирует первичный отбор кандидатов через адаптивный Telegram-бот, NLP-анализ и прозрачный дашборд для комиссии.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Hackathon](https://img.shields.io/badge/Decentrathon-5.0-orange)

---

## Что делает система

- **Адаптивное интервью** - Telegram-бот подстраивает вопросы под каждого кандидата
- **Оценка траектории роста** - система смотрит на динамику, а не только на текущий уровень
- **Детектор ИИ-текста** - определяет, написал ли кандидат эссе сам или использовал ChatGPT
- **Прозрачный дашборд** - комиссия видит не просто баллы, а объяснение каждой оценки
- **Human-in-the-loop** - финальное решение всегда остаётся за комиссией

---

## Структура проекта

```
talent-radar/
├── bot/
│   ├── main.py
│   ├── handlers.py
│   ├── questions.py
│   ├── adaptive.py
│   └── requirements.txt
├── backend/
│   ├── app.py
│   ├── scoring.py
│   ├── nlp_analysis.py
│   ├── ai_detector.py
│   ├── models.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── dashboard.js
│   ├── candidate.js
│   ├── radar-chart.js
│   └── styles.css
├── docs/
│   ├── README.md
│   ├── SCORING.md
│   └── API.md
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Технологии

| Часть проекта | Технологии |
|---|---|
| Telegram-бот | Python, python-telegram-bot |
| Backend / API | Python, FastAPI |
| ИИ-анализ | Anthropic Claude API |
| Frontend | HTML, CSS, JavaScript |

---

## Система оценки

Каждый кандидат получает балл от 0 до 100 по формуле:

```
Итоговый балл = (Лидерство × 0.34) + (Рост × 0.28) + (Аутентичность × 0.21) + (Релевантность × 0.17)
```

| Компонент | Вес |
|---|---|
| Лидерский потенциал | 34% |
| Траектория роста | 28% |
| Аутентичность | 21% |
| Релевантность | 17% |

Подробнее — в [SCORING.md](SCORING.md)

---

## Быстрый старт

```bash
# 1. Клонируй репозиторий
git clone https://github.com/zaiiris/talent-radar.git
cd talent-radar

# 2. Настрой переменные окружения
cp .env.example .env

# 3. Установи зависимости
pip install -r requirements.txt

# 4. Запусти бота
python bot/main.py
```

---

## Ограничения

- ИИ не принимает финальных решений — только поддерживает комиссию
- Система не использует демографические данные как критерий оценки
- Все данные обрабатываются локально, не передаются третьим сторонам

---

## Команда

| Имя |
|---|
| Абдугаппарова Зияда |
| Алибай Адиля |
| Бауржан Карина |
| Тургунбаева Жасмина |

---

## Лицензия

MIT License — Decentrathon 5.0, 2026
