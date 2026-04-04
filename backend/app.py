"""
app.py — TalentRadar FastAPI Backend

ЗАПУСК:
  uvicorn app:app --reload --port 8000

SWAGGER UI:
  http://localhost:8000/docs
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from models import (
    CandidateCreate, CandidateResponse, CandidateListResponse,
    BotAnswerSubmit, ShortlistUpdate, WeightsUpdate,
    CommentCreate, AnalyticsSummary,
)
from scoring import ScoringEngine, WEIGHTS

# ══════════════════════════════════════════════
# SQLite
# ══════════════════════════════════════════════

DB_PATH = os.getenv("DB_PATH", "talent_radar.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id           TEXT PRIMARY KEY,
                telegram_id  TEXT NOT NULL,
                name         TEXT NOT NULL,
                age          INTEGER,
                city         TEXT,
                university   TEXT,
                specialty    TEXT,
                essay        TEXT,
                achievements TEXT DEFAULT '[]',
                bot_answers  TEXT DEFAULT '[]',
                scores       TEXT,
                comments     TEXT DEFAULT '[]',
                shortlisted  INTEGER DEFAULT 0,
                status       TEXT DEFAULT 'pending',
                created_at   TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tg ON candidates(telegram_id)"
        )
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for f in ("achievements", "bot_answers", "comments"):
        try:
            d[f] = json.loads(d[f]) if d.get(f) else []
        except Exception:
            d[f] = []
    try:
        d["scores"] = json.loads(d["scores"]) if d.get("scores") else None
    except Exception:
        d["scores"] = None
    d["shortlisted"] = bool(d.get("shortlisted", 0))
    return d


def get_or_404(candidate_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Кандидат не найден")
    return row_to_dict(row)


# ══════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════

_engine = ScoringEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"✅ TalentRadar запущен. База: {DB_PATH}")
    yield
    print("🛑 TalentRadar остановлен.")


app = FastAPI(
    title="TalentRadar API",
    description="Умный отбор кандидатов с PPI-прогнозом.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════
# КАНДИДАТЫ
# ══════════════════════════════════════════════

@app.post("/candidates", response_model=CandidateResponse, tags=["Кандидаты"])
async def create_candidate(data: CandidateCreate):
    """Создать кандидата. Вызывается из Telegram-бота."""
    cid = f"c_{data.telegram_id}_{int(datetime.utcnow().timestamp())}"
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO candidates
            (id,telegram_id,name,age,city,university,specialty,
             essay,achievements,bot_answers,scores,comments,
             shortlisted,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            cid, data.telegram_id, data.name, data.age,
            data.city, data.university, data.specialty,
            data.essay or "",
            json.dumps(data.achievements, ensure_ascii=False),
            "[]", None, "[]", 0, "pending", now,
        ))
        conn.commit()

    return CandidateResponse(**get_or_404(cid))


@app.get("/candidates", response_model=CandidateListResponse, tags=["Кандидаты"])
async def list_candidates(
    shortlisted_only: bool          = Query(False),
    min_score:        float         = Query(0),
    city:             Optional[str] = Query(None),
    university:       Optional[str] = Query(None),
    limit:            int           = Query(100, ge=1, le=500),
    offset:           int           = Query(0, ge=0),
):
    """Список кандидатов с фильтрацией и сортировкой по баллу."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM candidates ORDER BY created_at DESC"
        ).fetchall()

    items = [row_to_dict(r) for r in rows]

    if shortlisted_only:
        items = [c for c in items if c["shortlisted"]]
    if min_score > 0:
        items = [c for c in items if (c.get("scores") or {}).get("total", 0) >= min_score]
    if city:
        items = [c for c in items if city.lower() in c["city"].lower()]
    if university:
        items = [c for c in items if university.lower() in c["university"].lower()]

    items.sort(key=lambda c: (c.get("scores") or {}).get("total", 0), reverse=True)

    return CandidateListResponse(
        candidates=[CandidateResponse(**c) for c in items[offset: offset + limit]],
        total=len(items),
        scored=sum(1 for c in items if c.get("scores")),
        shortlisted=sum(1 for c in items if c["shortlisted"]),
    )


@app.get("/candidates/{candidate_id}", response_model=CandidateResponse, tags=["Кандидаты"])
async def get_candidate(candidate_id: str):
    return CandidateResponse(**get_or_404(candidate_id))


@app.patch("/candidates/{candidate_id}/shortlist", tags=["Кандидаты"])
async def toggle_shortlist(candidate_id: str, body: ShortlistUpdate):
    get_or_404(candidate_id)
    with get_db() as conn:
        conn.execute(
            "UPDATE candidates SET shortlisted=? WHERE id=?",
            (1 if body.shortlisted else 0, candidate_id),
        )
        conn.commit()
    return {"id": candidate_id, "shortlisted": body.shortlisted}


@app.post("/candidates/{candidate_id}/comments", tags=["Кандидаты"])
async def add_comment(candidate_id: str, body: CommentCreate):
    """Комиссия оставляет заметку к кандидату."""
    c = get_or_404(candidate_id)
    comments = c.get("comments", [])
    comment = {
        "author": body.author,
        "text": body.text,
        "created_at": datetime.utcnow().isoformat(),
    }
    comments.append(comment)
    with get_db() as conn:
        conn.execute(
            "UPDATE candidates SET comments=? WHERE id=?",
            (json.dumps(comments, ensure_ascii=False), candidate_id),
        )
        conn.commit()
    return {"id": candidate_id, "comment": comment}


@app.delete("/candidates/{candidate_id}", tags=["Кандидаты"])
async def delete_candidate(candidate_id: str):
    get_or_404(candidate_id)
    with get_db() as conn:
        conn.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
        conn.commit()
    return {"deleted": candidate_id}


# ══════════════════════════════════════════════
# БОТ
# ══════════════════════════════════════════════

@app.post("/bot/answers/{candidate_id}", tags=["Бот"])
async def submit_answers(
    candidate_id: str,
    body: BotAnswerSubmit,
    background: BackgroundTasks,
):
    """
    Принимает ответы из бота, сохраняет, запускает скоринг в фоне.
    Бот не ждёт — сразу получает 200 OK.
    """
    get_or_404(candidate_id)
    answers_json = json.dumps(
        [a.model_dump() for a in body.answers], ensure_ascii=False
    )
    with get_db() as conn:
        conn.execute(
            "UPDATE candidates SET bot_answers=?, status='scoring' WHERE id=?",
            (answers_json, candidate_id),
        )
        conn.commit()
    background.add_task(_score_task, candidate_id)
    return {"status": "accepted", "candidate_id": candidate_id}


async def _score_task(candidate_id: str):
    try:
        c = get_or_404(candidate_id)
        result = await _engine.score(c)
        with get_db() as conn:
            conn.execute(
                "UPDATE candidates SET scores=?, status='scored' WHERE id=?",
                (json.dumps(result, ensure_ascii=False), candidate_id),
            )
            conn.commit()
        print(f"✅ Скоринг завершён: {candidate_id} → {result['total']}")
    except Exception as e:
        with get_db() as conn:
            conn.execute(
                "UPDATE candidates SET status='error' WHERE id=?",
                (candidate_id,),
            )
            conn.commit()
        print(f"❌ Ошибка скоринга {candidate_id}: {e}")


# ══════════════════════════════════════════════
# СКОРИНГ
# ══════════════════════════════════════════════

@app.get("/scoring/{candidate_id}", tags=["Скоринг"])
async def get_scoring(candidate_id: str):
    c = get_or_404(candidate_id)
    if not c.get("scores"):
        if c.get("status") == "scoring":
            raise HTTPException(202, "Скоринг выполняется, попробуй через 10 сек")
        raise HTTPException(404, "Скоринг ещё не выполнен")
    return c["scores"]


@app.post("/scoring/{candidate_id}/rescore", tags=["Скоринг"])
async def rescore(candidate_id: str, background: BackgroundTasks):
    """Пересчитать скоринг — например после смены весов."""
    get_or_404(candidate_id)
    with get_db() as conn:
        conn.execute(
            "UPDATE candidates SET status='scoring' WHERE id=?", (candidate_id,)
        )
        conn.commit()
    background.add_task(_score_task, candidate_id)
    return {"status": "rescoring_started"}


@app.post("/scoring/weights", tags=["Скоринг"])
async def update_weights(body: WeightsUpdate):
    """
    Обновить веса компонентов без перезапуска сервера.
    Комиссия может менять приоритеты через дашборд.
    """
    new_w = body.model_dump()
    WEIGHTS.update(new_w)
    return {"message": "Веса обновлены", "weights": WEIGHTS}


# ══════════════════════════════════════════════
# АНАЛИТИКА
# ══════════════════════════════════════════════

@app.get("/analytics/summary", response_model=AnalyticsSummary, tags=["Аналитика"])
async def summary():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM candidates").fetchall()
    all_c  = [row_to_dict(r) for r in rows]
    scored = [c for c in all_c if c.get("scores")]
    vals   = [c["scores"]["total"] for c in scored]

    rec_b = {"strong_yes": 0, "yes": 0, "maybe": 0, "no": 0}
    ai_n = underdog_n = 0
    for c in scored:
        rec_b[c["scores"].get("recommendation", "no")] = \
            rec_b.get(c["scores"].get("recommendation", "no"), 0) + 1
        if c["scores"].get("components", {}).get("authenticity", {}).get("ai_probability", 0) > 0.65:
            ai_n += 1
        if c["scores"].get("components", {}).get("growth_trajectory", {}).get("details", {}).get("underdog_bonus", 0) >= 10:
            underdog_n += 1

    return AnalyticsSummary(
        total_candidates=len(all_c),
        scored=len(scored),
        shortlisted=sum(1 for c in all_c if c["shortlisted"]),
        avg_score=round(sum(vals) / len(vals), 1) if vals else 0,
        max_score=max(vals, default=0),
        min_score=min(vals, default=0),
        ai_detected=ai_n,
        underdog_count=underdog_n,
        recommendation_breakdown=rec_b,
    )


@app.get("/analytics/distribution", tags=["Аналитика"])
async def distribution():
    """Распределение кандидатов по диапазонам баллов."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT scores FROM candidates WHERE scores IS NOT NULL"
        ).fetchall()
    buckets = {"0-24": 0, "25-49": 0, "50-64": 0, "65-79": 0, "80-100": 0}
    for r in rows:
        try:
            s = json.loads(r["scores"]).get("total", 0)
            key = "0-24" if s < 25 else "25-49" if s < 50 else "50-64" if s < 65 else "65-79" if s < 80 else "80-100"
            buckets[key] += 1
        except Exception:
            pass
    return buckets


@app.get("/analytics/top", tags=["Аналитика"])
async def top_candidates(n: int = Query(10, ge=1, le=50)):
    """Топ-N по текущему баллу."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM candidates WHERE scores IS NOT NULL"
        ).fetchall()
    items = sorted(
        [row_to_dict(r) for r in rows],
        key=lambda c: c["scores"].get("total", 0),
        reverse=True,
    )
    return [
        {
            "rank": i + 1, "id": c["id"], "name": c["name"], "age": c["age"],
            "score": c["scores"].get("total"),
            "rec_label": c["scores"].get("rec_label"),
            "ppi_predicted": c["scores"].get("ppi", {}).get("predicted_score"),
            "invest_label": c["scores"].get("ppi", {}).get("invest_label"),
            "shortlisted": c["shortlisted"],
        }
        for i, c in enumerate(items[:n])
    ]


@app.get("/analytics/ppi-leaders", tags=["Аналитика"])
async def ppi_leaders(n: int = Query(10, ge=1, le=50)):
    """
    Топ по PPI-прогнозу — 'скрытые алмазы'.
    Сортирует по predicted_score через 18 мес, а не по текущему баллу.
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM candidates WHERE scores IS NOT NULL"
        ).fetchall()
    items = sorted(
        [row_to_dict(r) for r in rows],
        key=lambda c: c["scores"].get("ppi", {}).get("predicted_score", 0),
        reverse=True,
    )
    return [
        {
            "rank": i + 1, "id": c["id"], "name": c["name"], "age": c["age"],
            "current_score":   c["scores"].get("total"),
            "predicted_score": c["scores"].get("ppi", {}).get("predicted_score"),
            "gain":            c["scores"].get("ppi", {}).get("gain"),
            "trajectory":      c["scores"].get("ppi", {}).get("trajectory_label"),
            "invest_label":    c["scores"].get("ppi", {}).get("invest_label"),
            "shortlisted":     c["shortlisted"],
        }
        for i, c in enumerate(items[:n])
    ]


# ══════════════════════════════════════════════
# СИСТЕМА
# ══════════════════════════════════════════════

@app.get("/health", tags=["Система"])
async def health():
    try:
        with get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        db_ok = True
    except Exception:
        count = 0
        db_ok = False
    return {
        "status":     "ok",
        "db":         "ok" if db_ok else "error",
        "candidates": count,
        "timestamp":  datetime.utcnow().isoformat(),
        "weights":    WEIGHTS,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
