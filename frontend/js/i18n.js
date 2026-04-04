/* ══════════════════════════════════════════
   i18n.js — переводы на 3 языка
   Использование: t('key')
══════════════════════════════════════════ */

const TRANSLATIONS = {
  ru: {
    // Общее
    appName:        "TalentRadar",
    appSub:         "inVision U — Приёмная комиссия",
    darkTheme:      "🌙 Тёмная",
    lightTheme:     "☀️ Светлая",
    back:           "← Назад",
    loading:        "Загрузка...",

    // Логин
    loginTitle:     "Добро пожаловать",
    loginSub:       "Система отбора кандидатов inVision U",
    loginEmail:     "Email",
    loginPass:      "Пароль",
    loginBtn:       "Войти в систему",
    loginHint:      "Доступ только для членов приёмной комиссии",
    loginDemo:      "Демо: admin@invision.kz / demo1234",

    // Шапка дашборда
    season:         "Сезон 2025 · Алматы",

    // Статистика
    totalApps:      "Всего заявок",
    shortlistStat:  "Shortlist",
    underReview:    "На рассмотрении",
    avgScore:       "Средний балл",

    // Поиск / фильтры
    searchPlaceholder: "🔍  Поиск по имени...",
    filterAll:      "Все",
    filterShort:    "🟢 Shortlist",
    filterReview:   "🟡 На рассмотрении",
    filterDeclined: "🔴 Отказ",
    showing:        "Показано:",
    noResults:      "Никого не найдено",

    // Заголовки таблицы
    colCandidate:   "Кандидат",
    colScore:       "Балл",
    colLeadership:  "Лидерство",
    colGrowth:      "Рост",
    colMotivation:  "Мотивация",
    colStatus:      "Статус",
    colText:        "Текст",

    // Бейджи
    badgeShortlist: "🌟 Shortlist",
    badgeReview:    "🔍 На рассмотрении",
    badgeDeclined:  "✕ Отказ",
    badgeAI:        "🤖 ИИ-текст",
    badgeHuman:     "✍️ Живой",

    // Кандидат
    candProfile:    "📊 Профиль кандидата",
    candDetail:     "🎯 Детальная оценка",
    candAnswers:    "💬 Ответы из интервью",
    candLeadership: "Лидерский потенциал",
    candGrowth:     "Траектория роста",
    candMotivation: "Мотивация / ценности",
    candAuth:       "Аутентичность",
    candSummary:    "Вывод AI-системы:",
    btnShortlist:   "🌟 В Shortlist",
    btnDecline:     "✕ Отказать",
    btnShortlistPage: "📋 Shortlist",
    confirmDecline: "Отказать кандидату?",
    addedShortlist: "✅ Добавлен в Shortlist! Хочешь обоснование?",
    declinedMsg:    "Понял. Помечен как отказ.",
    ofScore:        "из 100",

    // AI чат
    aiTitle:        "🤖 AI-ассистент комиссии",
    aiSub:          "Claude · Спроси что угодно о кандидате",
    aiGreeting:     "Привет! Я проанализировал профиль кандидата и готов ответить на вопросы комиссии.",
    apiKeyLabel:    "🔑 Anthropic API Key:",
    apiKeyPlaceholder: "sk-ant-...",
    apiKeySave:     "OK",
    apiKeyHint:     "Введи ключ чтобы активировать AI-чат",
    apiKeyOk:       "✅ AI-чат активен!",
    apiKeyError:    "❌ Ключ должен начинаться с sk-ant-",
    chatPlaceholder:"Задай вопрос о кандидате...",
    chatSend:       "↑ Отправить",
    chatUser:       "Комиссия",
    chatConnError:  "Ошибка соединения. Проверь интернет и API ключ.",
    chatNoKey:      "⚠️ Введи Anthropic API Key выше чтобы активировать чат.",
    q1: "🎯 Подходит?",   q1full: "Почему этот кандидат подходит для inVision U?",
    q2: "⚠️ Риски",       q2full: "Какие риски есть у этого кандидата?",
    q3: "👑 Лидерство",   q3full: "Оцени лидерский потенциал подробно",
    q4: "✅ Решение",      q4full: "Дай финальную рекомендацию: зачислить или отказать?",

    // Shortlist
    shortlistTitle: "🌟 Shortlist",
    shortlistSub:   "Отобранные кандидаты · inVision U 2025",
    selectHint:     "Выбери 2 кандидата для сравнения",
    selectedHint:   "✅ Два выбраны — можно сравнивать!",
    selectedCount:  "Выбрано:",
    btnCompare:     "⚡ Сравнить",
    btnExport:      "📄 Экспорт PDF",
    btnEnrollAll:   "🎉 Зачислить всех!",
    btnEnroll:      "🎉 Зачислить!",
    outOf:          "из 100 баллов",
    compareTitle:   "⚡ Сравнение кандидатов",
    compareLeads:   "🏆 Лидирует",
    compareTie:     "🤝 Одинаковый балл — решение за комиссией",
    enrolledMsg:    "зачислен(а) в inVision U!",
    enrolledAllMsg: "Все кандидаты из Shortlist зачислены!",

    // Профиль
    profileTitle:   "Профиль администратора",
    profileName:    "Айгуль Назарова",
    profileRole:    "Председатель приёмной комиссии",
    profileEmail:   "a.nazarova@invision.kz",
    profileDept:    "inVision University · Алматы",
    profileSince:   "В системе с 2024",
    profileDecisions: "Решений принято",
    profileReviewed:  "Заявок просмотрено",
    profileAccepted:  "Принято",
    profileLogout:  "Выйти из системы",
    profileEdit:    "Редактировать профиль",
    recentActivity: "Последняя активность",
  },

  kz: {
    appName:        "TalentRadar",
    appSub:         "inVision U — Қабылдау комиссиясы",
    darkTheme:      "🌙 Күңгірт",
    lightTheme:     "☀️ Ашық",
    back:           "← Артқа",
    loading:        "Жүктелуде...",

    loginTitle:     "Қош келдіңіз",
    loginSub:       "inVision U үміткерлерді іріктеу жүйесі",
    loginEmail:     "Электрондық пошта",
    loginPass:      "Құпия сөз",
    loginBtn:       "Жүйеге кіру",
    loginHint:      "Тек қабылдау комиссиясының мүшелеріне арналған",
    loginDemo:      "Демо: admin@invision.kz / demo1234",

    season:         "2025 маусымы · Алматы",

    totalApps:      "Барлық өтінімдер",
    shortlistStat:  "Shortlist",
    underReview:    "Қарастырылуда",
    avgScore:       "Орташа балл",

    searchPlaceholder: "🔍  Атымен іздеу...",
    filterAll:      "Барлығы",
    filterShort:    "🟢 Shortlist",
    filterReview:   "🟡 Қарастырылуда",
    filterDeclined: "🔴 Бас тартылды",
    showing:        "Көрсетілді:",
    noResults:      "Ешкім табылмады",

    colCandidate:   "Үміткер",
    colScore:       "Балл",
    colLeadership:  "Көшбасшылық",
    colGrowth:      "Өсу",
    colMotivation:  "Мотивация",
    colStatus:      "Мәртебе",
    colText:        "Мәтін",

    badgeShortlist: "🌟 Shortlist",
    badgeReview:    "🔍 Қарастырылуда",
    badgeDeclined:  "✕ Бас тартылды",
    badgeAI:        "🤖 ЖИ мәтіні",
    badgeHuman:     "✍️ Тірі",

    candProfile:    "📊 Үміткер профилі",
    candDetail:     "🎯 Егжей-тегжейлі баға",
    candAnswers:    "💬 Сұхбат жауаптары",
    candLeadership: "Көшбасшылық әлеуеті",
    candGrowth:     "Өсу траекториясы",
    candMotivation: "Мотивация / құндылықтар",
    candAuth:       "Аутенттілік",
    candSummary:    "ЖИ жүйесінің қорытындысы:",
    btnShortlist:   "🌟 Shortlist-ке",
    btnDecline:     "✕ Бас тарту",
    btnShortlistPage: "📋 Shortlist",
    confirmDecline: "Үміткерге бас тарту?",
    addedShortlist: "✅ Shortlist-ке қосылды!",
    declinedMsg:    "Түсіндім. Бас тартылды деп белгіленді.",
    ofScore:        "100-ден",

    aiTitle:        "🤖 Комиссияның AI-көмекшісі",
    aiSub:          "Claude · Үміткер туралы кез келген сұрақ",
    aiGreeting:     "Сәлем! Мен үміткердің профилін талдап, комиссияның сұрақтарына жауап беруге дайынмын.",
    apiKeyLabel:    "🔑 Anthropic API Key:",
    apiKeyPlaceholder: "sk-ant-...",
    apiKeySave:     "OK",
    apiKeyHint:     "AI-чатты іске қосу үшін кілт енгізіңіз",
    apiKeyOk:       "✅ AI-чат белсенді!",
    apiKeyError:    "❌ Кілт sk-ant- деп басталуы керек",
    chatPlaceholder:"Үміткер туралы сұрақ қою...",
    chatSend:       "↑ Жіберу",
    chatUser:       "Комиссия",
    chatConnError:  "Байланыс қатесі. Интернет пен API кілтін тексеріңіз.",
    chatNoKey:      "⚠️ AI-чатты іске қосу үшін API кілтін енгізіңіз.",
    q1: "🎯 Сәйкес пе?",  q1full: "Бұл үміткер inVision U-ға неліктен сәйкес?",
    q2: "⚠️ Тәуекелдер", q2full: "Бұл үміткердің қандай тәуекелдері бар?",
    q3: "👑 Көшбасшылық",q3full: "Көшбасшылық әлеуетін егжей-тегжейлі бағалаңыз",
    q4: "✅ Шешім",       q4full: "Қорытынды ұсыныс беріңіз: қабылдау немесе бас тарту?",

    shortlistTitle: "🌟 Shortlist",
    shortlistSub:   "Іріктелген үміткерлер · inVision U 2025",
    selectHint:     "Салыстыру үшін 2 үміткер таңдаңыз",
    selectedHint:   "✅ Екеуі таңдалды — салыстыруға болады!",
    selectedCount:  "Таңдалды:",
    btnCompare:     "⚡ Салыстыру",
    btnExport:      "📄 PDF экспорт",
    btnEnrollAll:   "🎉 Барлығын қабылдау!",
    btnEnroll:      "🎉 Қабылдау!",
    outOf:          "100 баллдан",
    compareTitle:   "⚡ Үміткерлерді салыстыру",
    compareLeads:   "🏆 Жетекшілік",
    compareTie:     "🤝 Тең балл — шешімді комиссия қабылдайды",
    enrolledMsg:    "inVision U-ға қабылданды!",
    enrolledAllMsg: "Shortlist-тегі барлық үміткерлер қабылданды!",

    profileTitle:   "Әкімші профилі",
    profileName:    "Айгүл Назарова",
    profileRole:    "Қабылдау комиссиясының төрайымы",
    profileEmail:   "a.nazarova@invision.kz",
    profileDept:    "inVision University · Алматы",
    profileSince:   "2024 жылдан бері жүйеде",
    profileDecisions: "Қабылданған шешімдер",
    profileReviewed:  "Қаралған өтінімдер",
    profileAccepted:  "Қабылданды",
    profileLogout:  "Жүйеден шығу",
    profileEdit:    "Профильді өңдеу",
    recentActivity: "Соңғы белсенділік",
  },

  en: {
    appName:        "TalentRadar",
    appSub:         "inVision U — Admissions Committee",
    darkTheme:      "🌙 Dark",
    lightTheme:     "☀️ Light",
    back:           "← Back",
    loading:        "Loading...",

    loginTitle:     "Welcome back",
    loginSub:       "inVision U Candidate Selection System",
    loginEmail:     "Email",
    loginPass:      "Password",
    loginBtn:       "Sign in",
    loginHint:      "Access restricted to admissions committee members",
    loginDemo:      "Demo: admin@invision.kz / demo1234",

    season:         "Season 2025 · Almaty",

    totalApps:      "Total applications",
    shortlistStat:  "Shortlisted",
    underReview:    "Under review",
    avgScore:       "Average score",

    searchPlaceholder: "🔍  Search by name...",
    filterAll:      "All",
    filterShort:    "🟢 Shortlist",
    filterReview:   "🟡 Under review",
    filterDeclined: "🔴 Declined",
    showing:        "Showing:",
    noResults:      "No candidates found",

    colCandidate:   "Candidate",
    colScore:       "Score",
    colLeadership:  "Leadership",
    colGrowth:      "Growth",
    colMotivation:  "Motivation",
    colStatus:      "Status",
    colText:        "Text",

    badgeShortlist: "🌟 Shortlist",
    badgeReview:    "🔍 Under review",
    badgeDeclined:  "✕ Declined",
    badgeAI:        "🤖 AI text",
    badgeHuman:     "✍️ Human",

    candProfile:    "📊 Candidate profile",
    candDetail:     "🎯 Detailed scores",
    candAnswers:    "💬 Interview answers",
    candLeadership: "Leadership potential",
    candGrowth:     "Growth trajectory",
    candMotivation: "Motivation & values",
    candAuth:       "Authenticity",
    candSummary:    "AI system summary:",
    btnShortlist:   "🌟 Add to shortlist",
    btnDecline:     "✕ Decline",
    btnShortlistPage: "📋 Shortlist",
    confirmDecline: "Decline this candidate?",
    addedShortlist: "✅ Added to shortlist! Want a justification memo?",
    declinedMsg:    "Understood. Marked as declined.",
    ofScore:        "out of 100",

    aiTitle:        "🤖 AI Committee Assistant",
    aiSub:          "Claude · Ask anything about this candidate",
    aiGreeting:     "Hello! I've analysed this candidate's profile and I'm ready to answer the committee's questions.",
    apiKeyLabel:    "🔑 Anthropic API Key:",
    apiKeyPlaceholder: "sk-ant-...",
    apiKeySave:     "Save",
    apiKeyHint:     "Enter your key to activate the AI chat",
    apiKeyOk:       "✅ AI chat is active!",
    apiKeyError:    "❌ Key must start with sk-ant-",
    chatPlaceholder:"Ask a question about the candidate...",
    chatSend:       "↑ Send",
    chatUser:       "Committee",
    chatConnError:  "Connection error. Check your internet and API key.",
    chatNoKey:      "⚠️ Enter your Anthropic API Key above to activate the chat.",
    q1: "🎯 Good fit?",   q1full: "Why is this candidate a good fit for inVision U?",
    q2: "⚠️ Risks",       q2full: "What are the risks with this candidate?",
    q3: "👑 Leadership",  q3full: "Assess leadership potential in detail",
    q4: "✅ Decision",    q4full: "Give a final recommendation: accept or decline?",

    shortlistTitle: "🌟 Shortlist",
    shortlistSub:   "Selected candidates · inVision U 2025",
    selectHint:     "Select 2 candidates to compare",
    selectedHint:   "✅ Two selected — ready to compare!",
    selectedCount:  "Selected:",
    btnCompare:     "⚡ Compare",
    btnExport:      "📄 Export PDF",
    btnEnrollAll:   "🎉 Enrol all!",
    btnEnroll:      "🎉 Enrol!",
    outOf:          "out of 100",
    compareTitle:   "⚡ Compare candidates",
    compareLeads:   "🏆 Leading:",
    compareTie:     "🤝 Equal score — committee decides",
    enrolledMsg:    "has been enrolled in inVision U!",
    enrolledAllMsg: "All shortlisted candidates have been enrolled!",

    profileTitle:   "Administrator profile",
    profileName:    "Aigul Nazarova",
    profileRole:    "Head of Admissions Committee",
    profileEmail:   "a.nazarova@invision.kz",
    profileDept:    "inVision University · Almaty",
    profileSince:   "In system since 2024",
    profileDecisions: "Decisions made",
    profileReviewed:  "Applications reviewed",
    profileAccepted:  "Accepted",
    profileLogout:  "Sign out",
    profileEdit:    "Edit profile",
    recentActivity: "Recent activity",
  }
};

let currentLang = localStorage.getItem("tr_lang") || "ru";

function t(key) {
  return TRANSLATIONS[currentLang]?.[key] || TRANSLATIONS.ru[key] || key;
}

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem("tr_lang", lang);
  document.querySelectorAll(".lang-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.lang === lang);
  });
  if (typeof onLangChange === "function") onLangChange();
}

function initLangSwitcher() {
  document.querySelectorAll(".lang-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.lang === currentLang);
    b.addEventListener("click", () => setLang(b.dataset.lang));
  });
}
