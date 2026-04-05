"""
app.py — TalentRadar FastAPI Backend (PostgreSQL)

ЗАПУСК:
  uvicorn app:app --reload --port 8000

SWAGGER:
  http://localhost:8000/docs
"""

import os, json
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
from database import (
    create_pool, init_db_async,
    db_get_all, db_get_one, db_insert, db_delete,
    db_update_status, db_update_scores, db_add_comment,
    row_to_frontend,
)

# ══════════════════════════════════════════════
# STARTUP / SHUTDOWN
# ══════════════════════════════════════════════

_pool   = None
_engine = ScoringEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    _pool = await create_pool()
    await init_db_async(_pool)
    print("✅ TalentRadar запущен | PostgreSQL пул создан")
    yield
    await _pool.close()
    print("🛑 TalentRadar остановлен")


app = FastAPI(
    title="TalentRadar API",
    description="inVision U — умный отбор кандидатов",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _pool_or_500():
    if not _pool:
        raise HTTPException(503, "БД не подключена")
    return _pool


# ══════════════════════════════════════════════
# /api/* — ДЛЯ ФРОНТЕНДА (index.html, candidate.html)
# ══════════════════════════════════════════════

@app.get("/api/candidates", tags=["Фронтенд"])
async def api_list(
    status: Optional[str] = Query(None, description="shortlist|review|declined"),
    search: Optional[str] = Query(None, description="поиск по имени"),
):
    """
    Список кандидатов в формате фронтенда TalentRadar.
    Используется в index.html вместо захардкоженного CANDIDATES[].
    """
    pool  = _pool_or_500()
    items = await db_get_all(pool, status_filter=status, search=search)
    items = [row_to_frontend(c) for c in items]
    return {
        "candidates": items,
        "total":      len(items),
        "shortlisted":sum(1 for c in items if c["status"] == "shortlist"),
        "review":     sum(1 for c in items if c["status"] == "review"),
        "declined":   sum(1 for c in items if c["status"] == "declined"),
        "avg_score":  round(sum(c.get("score", 0) for c in items)/len(items), 1) if items else 0,
    }


@app.get("/api/candidates/{cid}", tags=["Фронтенд"])
async def api_get_one(cid: str):
    """Один кандидат по id — для candidate.html."""
    pool = _pool_or_500()
    c    = await db_get_one(pool, cid)
    if not c:
        raise HTTPException(404, "Кандидат не найден")
    return row_to_frontend(c)


@app.patch("/api/candidates/{cid}/status", tags=["Фронтенд"])
async def api_set_status(cid: str, body: ShortlistUpdate):
    """Кнопка 'В Shortlist' / 'Отказать' из дашборда."""
    pool   = _pool_or_500()
    if body.shortlisted:
        status = "shortlist"
    else:
        # Для decline устанавливаем статус "declined"
        status = "declined"
    await db_update_status(pool, cid, status, body.shortlisted)
    return {"id": cid, "status": status, "shortlisted": body.shortlisted}


# ══════════════════════════════════════════════
# /candidates — стандартный REST (для бота / Swagger)
# ══════════════════════════════════════════════

@app.post("/candidates", tags=["Кандидаты"])
async def create_candidate(data: CandidateCreate, background: BackgroundTasks):
    pool = _pool_or_500()
    cid  = await db_insert(pool, {
        "telegram_id": data.telegram_id,
        "name":        data.name,
        "age":         data.age,
        "city":        data.city,
        "school":      data.university,
        "language":    "ru",
        "interview":   [],
        "status":      "pending",
    })
    return {"id": cid, "status": "created"}


@app.get("/candidates", response_model=CandidateListResponse, tags=["Кандидаты"])
async def list_candidates(
    shortlisted_only: bool          = Query(False),
    min_score:        float         = Query(0),
    city:             Optional[str] = Query(None),
    limit:            int           = Query(100, ge=1, le=500),
    offset:           int           = Query(0, ge=0),
):
    pool  = _pool_or_500()
    items = await db_get_all(pool)

    if shortlisted_only:
        items = [c for c in items if c["shortlisted"]]
    if min_score > 0:
        items = [c for c in items if c.get("score", 0) >= min_score]
    if city:
        items = [c for c in items if city.lower() in (c.get("city") or "").lower()]

    paged = items[offset: offset + limit]
    return CandidateListResponse(
        candidates=[CandidateResponse(**_adapt(c)) for c in paged],
        total=len(items),
        scored=sum(1 for c in items if c.get("score")),
        shortlisted=sum(1 for c in items if c["shortlisted"]),
    )


@app.get("/candidates/{cid}", tags=["Кандидаты"])
async def get_candidate(cid: str):
    pool = _pool_or_500()
    c    = await db_get_one(pool, cid)
    if not c: raise HTTPException(404, "Кандидат не найден")
    return c


@app.patch("/candidates/{cid}/shortlist", tags=["Кандидаты"])
async def toggle_shortlist(cid: str, body: ShortlistUpdate):
    pool   = _pool_or_500()
    status = "shortlist" if body.shortlisted else "review"
    await db_update_status(pool, cid, status, body.shortlisted)
    return {"id": cid, "shortlisted": body.shortlisted}


@app.delete("/candidates/{cid}", tags=["Кандидаты"])
async def delete_candidate(cid: str):
    pool = _pool_or_500()
    await db_delete(pool, cid)
    return {"deleted": cid}


@app.post("/candidates/{cid}/comments", tags=["Кандидаты"])
async def add_comment(cid: str, body: CommentCreate):
    pool    = _pool_or_500()
    comment = {"author": body.author, "text": body.text,
                "created_at": datetime.utcnow().isoformat()}
    await db_add_comment(pool, cid, comment)
    return {"id": cid, "comment": comment}


# ══════════════════════════════════════════════
# БОТ — приём ответов + фоновый скоринг
# ══════════════════════════════════════════════

@app.post("/bot/answers/{cid}", tags=["Бот"])
async def submit_answers(cid: str, body: BotAnswerSubmit, bg: BackgroundTasks):
    """Бот отправляет ответы — скоринг запускается в фоне."""
    pool     = _pool_or_500()
    answers  = [a.model_dump() for a in body.answers]
    c        = await db_get_one(pool, cid)
    if not c: raise HTTPException(404, "Кандидат не найден")

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE candidates SET interview=$1::jsonb, status='scoring' WHERE id=$2",
            json.dumps(answers, ensure_ascii=False), cid
        )
    bg.add_task(_score_bg, cid)
    return {"status": "accepted", "candidate_id": cid}


async def _score_bg(cid: str):
    try:
        pool = _pool_or_500()
        c    = await db_get_one(pool, cid)
        result = await _engine.score(c)
        await db_update_scores(pool, cid, result, "scored")
        print(f"✅ Скоринг: {cid} → {result.get('total')}")
    except Exception as e:
        try:
            await db_update_scores(_pool, cid, {}, "error")
        except Exception:
            pass
        print(f"❌ Скоринг ошибка {cid}: {e}")


# ══════════════════════════════════════════════
# АНАЛИТИКА
# ══════════════════════════════════════════════

@app.get("/analytics/summary", response_model=AnalyticsSummary, tags=["Аналитика"])
async def analytics_summary():
    pool  = _pool_or_500()
    items = await db_get_all(pool)
    vals  = [c["score"] for c in items if c.get("score")]

    return AnalyticsSummary(
        total_candidates=len(items),
        scored=sum(1 for c in items if c.get("score")),
        shortlisted=sum(1 for c in items if c["shortlisted"]),
        avg_score=round(sum(vals)/len(vals), 1) if vals else 0,
        max_score=max(vals, default=0),
        min_score=min(vals, default=0),
        ai_detected=sum(1 for c in items if c.get("ai_text")),
        underdog_count=0,
        recommendation_breakdown={
            "Рекомендован":    sum(1 for c in items if c.get("recommendation")=="Рекомендован"),
            "На рассмотрение": sum(1 for c in items if c.get("recommendation")=="На рассмотрение"),
            "Не рекомендован": sum(1 for c in items if c.get("recommendation")=="Не рекомендован"),
        },
    )


@app.get("/analytics/top", tags=["Аналитика"])
async def top(n: int = Query(10, ge=1, le=50)):
    pool  = _pool_or_500()
    items = await db_get_all(pool)
    return [
        {"rank": i+1, "id": c["id"], "name": c["name"],
         "score": c["score"], "shortlisted": c["shortlisted"]}
        for i, c in enumerate(items[:n])
    ]


# ══════════════════════════════════════════════
# СИСТЕМА
# ══════════════════════════════════════════════

@app.get("/health", tags=["Система"])
async def health():
    try:
        pool  = _pool_or_500()
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM candidates")
        db_ok = True
    except Exception:
        count, db_ok = 0, False
    return {
        "status":     "ok",
        "db":         "postgresql" if db_ok else "error",
        "candidates": count,
        "timestamp":  datetime.utcnow().isoformat(),
        "weights":    WEIGHTS,
    }


# ── Вспомогательная адаптация для CandidateResponse ─

def _adapt(c: dict) -> dict:
    """Переводит frontend-формат обратно в модель CandidateResponse."""
    return {
        "id":           c["id"],
        "telegram_id":  c.get("username",""),
        "name":         c["name"],
        "age":          c.get("age") or 0,
        "city":         c.get("city",""),
        "university":   c.get("school",""),
        "specialty":    "",
        "essay":        c.get("summary",""),
        "achievements": [],
        "created_at":   c.get("date",""),
        "status":       c.get("status","review"),
        "shortlisted":  c.get("shortlisted",False),
        "bot_answers":  c.get("answers",[]),
        "scores":       None,
        "comments":     [],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT",8000)), reload=True)
