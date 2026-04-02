<p align="center">
  <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&q=80" width="100%" alt="TalentRadar banner"/>
</p>

<h1 align="center">🎯 TalentRadar</h1>

<p align="center">
  <b>AI-система оценки кандидатов — находим потенциал, а не фильтруем резюме</b><br/>
  Создано на Zerde Hackathon 2025
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Claude_API-D97757?style=for-the-badge&logo=anthropic&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-gray?style=for-the-badge"/>
</p>

---

## 💡 О проекте

Большинство систем отбора ранжируют заявки по ключевым словам. **TalentRadar** работает иначе:

> Мы не фильтруем — мы **раскрываем** человека.

Система проводит адаптивное интервью через Telegram, оценивает **вектор роста** кандидата и выдаёт комиссии прозрачный, объяснимый результат — не чёрный ящик.

---

## ✨ Ключевые возможности

<table>
<tr>
<td width="50%">

### 🤖 Адаптивный бот-интервьюер
Telegram-бот анализирует каждый ответ и подбирает следующий вопрос индивидуально. Никаких заготовленных шаблонов — живой диалог.

</td>
<td width="50%">

### 📈 Оценка траектории роста
Система смотрит не на то, кем ты являешься сейчас, а **куда ты движешься**. Победитель олимпиады, который три года назад был троечником — сильный сигнал.

</td>
</tr>
<tr>
<td width="50%">

### 🔍 AI-детектор подлинности
Сравниваем эссе кандидата с его ответами в боте. Если эссе написал ChatGPT — система это заметит.

</td>
<td width="50%">

### 📊 Прозрачный дашборд
Каждый балл раскладывается по факторам: «83 балла, потому что: лидерский потенциал +34, рост +28, аутентичность +21». Комиссия видит логику.

</td>
</tr>
</table>

---

## 🔄 Как это работает

```
Кандидат открывает Telegram-бот
  → Проходит адаптивное интервью (7–10 вопросов)
  → ИИ оценивает по 4 измерениям
  → Комиссия открывает дашборд с ранжированным списком
  → Формирует shortlist одним кликом
```

<p align="center">
  <img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80" width="80%" alt="dashboard analytics"/>
</p>

---

## 🧠 Модель оценки

Каждый кандидат оценивается по **4 измерениям**:

| # | Измерение | Что оцениваем |
|---|-----------|----------------|
| 1 | 🧭 Лидерский потенциал | Инициатива, стиль принятия решений, поведение в команде |
| 2 | 📈 Траектория роста | Скорость развития по временным меткам в анкете |
| 3 | ✅ Аутентичность | Согласованность эссе и ответов в боте |
| 4 | 💬 Ясность мышления | Структура и глубина ответов в интервью |

Итоговый балл — взвешенная сумма. Веса настраиваются в `backend/scoring.py`.

---

## 🛠 Технологии

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Telegram-26A5E4?style=flat-square&logo=telegram&logoColor=white"/>
  <img src="https://img.shields.io/badge/Anthropic-D97757?style=flat-square&logo=anthropic&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black"/>
  <img src="https://img.shields.io/badge/Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white"/>
</p>

---

## 📁 Структура проекта

```
talent-radar/
├── bot/            # Telegram-бот с адаптивной логикой интервью
├── backend/        # FastAPI-сервер и движок оценки
├── frontend/       # Дашборд для комиссии (React)
├── docs/           # Архитектурные схемы и решения
├── .env.example    # Шаблон переменных окружения
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
# Вставь свои ключи в .env
```

`.env.example`:
```
TELEGRAM_TOKEN=твой_токен_от_botfather
ANTHROPIC_API_KEY=твой_ключ_anthropic
```

### 3. Установи зависимости и запусти бота

```bash
cd bot
pip install -r requirements.txt
python main.py
```

Если видишь `✅ Бот запущен!` — всё работает. Открывай Telegram и пиши `/start`.

---

## 👥 Команда

| Имя | Роль |
|-----|------|
| — | — |

> Создано с ❤️ на Zerde Hackathon 2025

---

## 📄 Лицензия

MIT — используй свободно.
