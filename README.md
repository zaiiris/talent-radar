<div align="center">

# 🎯 TalentRadar

### AI-система первичного отбора кандидатов для inVision U
**Decentrathon 5.0 · Трек: AI inDrive**

---

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)
![Claude API](https://img.shields.io/badge/Claude-AI%20Core-D97757?style=flat-square&logo=anthropic&logoColor=white)
![React](https://img.shields.io/badge/React-Dashboard-61DAFB?style=flat-square&logo=react&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-lightgray?style=flat-square)

</div>

---

## 💡 О проекте

**TalentRadar** — интеллектуальная система поддержки отбора кандидатов в inVision U.

Большинство систем скрининга видят **заявку**, а не **человека**. TalentRadar работает иначе: система раскрывает кандидата через адаптивный диалог, оценивает не текущий уровень, а **вектор роста**, и даёт комиссии прозрачное объяснение каждого балла — без чёрного ящика.

> ИИ **не принимает** финальных решений. Он поддерживает комиссию — человек остаётся в контуре.

---

## ✨ Ключевые возможности

| | Функция | Описание |
|---|---|---|
| 🤖 | **Адаптивный бот-интервьюер** | Telegram-бот подстраивает каждый вопрос под предыдущий ответ. Нельзя заготовить шаблонные ответы заранее |
| 📈 | **Growth Trajectory Score** | Оцениваем не срез «кто ты сейчас», а динамику роста. Вектор важнее точки |
| 🔍 | **AI-детектор подлинности** | Сравниваем стиль эссе с живыми ответами в боте. ChatGPT-текст не пройдёт незамеченным |
| 📊 | **Explainable Dashboard** | Каждый балл разложен на факторы. Комиссия видит логику, а не цифру |
| 🛡️ | **Human-in-the-loop** | Финальное решение — всегда за комиссией. ИИ ранжирует, человек решает |

---

## 🔄 Как работает система

```
Кандидат → Telegram-бот → Адаптивное интервью (7–10 вопросов)
                                    ↓
                         Анализ по 4 измерениям (Claude API)
                                    ↓
              Дашборд комиссии → Ранжированный список → Shortlist
```

---

## 🧠 Модель оценки

Итоговый балл — взвешенная сумма четырёх компонентов:

| Измерение | Что оцениваем | Вес |
|---|---|---|
| 🧭 Лидерский потенциал | Инициатива, принятие решений, командная роль | 35% |
| 📈 Траектория роста | Динамика развития по временным меткам анкеты | 30% |
| ✅ Аутентичность | Согласованность эссе с живыми ответами в боте | 20% |
| 💬 Ясность мышления | Структура и глубина ответов в интервью | 15% |

Веса настраиваются в `backend/scoring.py`.

**Пример вывода:** `83 балла → лидерский потенциал +34 / рост +28 / аутентичность +21`

---

## 🛠 Стек технологий

| Слой | Технология |
|---|---|
| AI-ядро | Anthropic Claude API (NLP, скоринг, детекция ИИ-текста) |
| Bot | Python + python-telegram-bot (FSM адаптивный диалог) |
| Backend | FastAPI + scoring engine |
| Frontend | React — дашборд для комиссии |
| Deploy | Railway (автодеплой из GitHub) |

---

## 📁 Структура проекта

```
talent-radar/
├── bot/               # Telegram-бот: адаптивное интервью
│   ├── main.py
│   └── requirements.txt
├── backend/           # FastAPI-сервер + движок оценки
│   ├── app.py
│   └── scoring.py
├── frontend/          # Дашборд для комиссии (React)
├── docs/              # Архитектурные схемы
├── .env.example       # Шаблон переменных окружения
└── README.md
```

---

## 🚀 Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/zaiiris/talent-radar.git
cd talent-radar
```

### 2. Настрой переменные окружения

```bash
cp .env.example .env
```

```env
# .env
TELEGRAM_TOKEN=твой_токен_от_BotFather
ANTHROPIC_API_KEY=твой_ключ_с_console.anthropic.com
```

### 3. Запусти бота

```bash
cd bot
pip install -r requirements.txt
python main.py
```

`✅ Бот запущен!` — открывай Telegram и пиши `/start`

### 4. Запусти бэкенд

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

---

## ⚠️ Ограничения и этика

- Система **не использует** демографические, расовые или социально-экономические данные
- Персональные данные кандидатов не хранятся — обрабатываются только в рамках сессии
- ИИ работает исключительно как инструмент поддержки комиссии
- Детекция ИИ-текста — вспомогательный сигнал, не основание для отказа

---

## 👥 Команда

| Имя | Роль |
|---|---|
| Абдугаппаров Зияда | Frontend — дашборд для комиссии |
| Алибай Адиля | Backend — API, scoring engine |
| Бауржан Карина | Bot development — адаптивный Telegram-бот |
| Тургунбаева Жасмина | README & документация |

---

## 📄 Лицензия

MIT — используй свободно.

---

<div align="center">
  <sub>Создано с ❤️ на Decentrathon 5.0 · 2025</sub>
</div>
> Создано с ❤️ на Zerde Hackathon 2025

---

## 📄 Лицензия

MIT — используй свободно.
