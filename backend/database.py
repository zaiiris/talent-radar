"""
database.py — PostgreSQL модуль для TalentRadar.

Используется одновременно:
  - Telegram-ботом    → синхронно через psycopg2
  - FastAPI бэкендом  → асинхронно через asyncpg

Настройка (.env):
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/talentrada
"""

import os, json, uuid, logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


# ── DDL ───────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS candidates (
    id                TEXT        PRIMARY KEY,
    telegram_id       TEXT,
    telegram_username TEXT,
    name              TEXT        NOT NULL,
    age               INTEGER,
    city              TEXT,
    school            TEXT,
    language          TEXT        DEFAULT 'ru',
    interview         JSONB       DEFAULT '[]',
    scores            JSONB,
    shortlisted       BOOLEAN     DEFAULT FALSE,
    status            TEXT        DEFAULT 'pending',
    recommendation    TEXT,
    summary           TEXT,
    ai_text_detected  BOOLEAN     DEFAULT FALSE,
    ai_text_reason    TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cand_tg   ON candidates(telegram_id);
CREATE INDEX IF NOT EXISTS idx_cand_stat ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_cand_ts   ON candidates(created_at DESC);
"""


# ══════════════════════════════════════════════
# СИНХРОННОЕ (psycopg2) — Telegram-бот
# ══════════════════════════════════════════════

def _sync_conn():
    try:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    except ImportError:
        raise RuntimeError("Установи: pip install psycopg2-binary")


def init_db():
    """Создаёт таблицу. Вызывается при старте бота и FastAPI."""
    conn = _sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        logger.info("✅ PostgreSQL: таблица candidates готова")
    except Exception as e:
        conn.rollback(); logger.error(f"init_db error: {e}"); raise
    finally:
        conn.close()


def save_candidate_to_db(data: dict, analysis: dict) -> str:
    """
    Сохраняет кандидата из бота в PostgreSQL.
    data     = context.user_data
    analysis = результат analyze_candidate()
    """
    cid  = f"candidate_{uuid.uuid4().hex}"
    raw  = analysis.get("scores", {})

    def to25(v): return round((v or 0) * 25 / 100)

    scores = {
        "leadership":   to25(raw.get("leadership", 0)),
        "growth":       to25(raw.get("trajectory", 0)),
        "motivation":   to25(raw.get("motivation", 0)),
        "authenticity": to25(raw.get("authenticity", 0)),
        "total":        analysis.get("total", 0),
        "strengths":    analysis.get("strengths", []),
        "growth_areas": analysis.get("growth_areas", []),
        "raw":          raw,
    }

    rec = analysis.get("recommendation", "На рассмотрение")
    status = ("shortlist" if rec == "Рекомендован"
              else "declined" if rec == "Не рекомендован"
              else "review")

    conn = _sync_conn()
    try:
        import psycopg2.extras
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO candidates
                  (id,telegram_id,telegram_username,name,age,city,school,
                   language,interview,scores,shortlisted,status,
                   recommendation,summary,ai_text_detected,ai_text_reason)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING
            """, (
                cid,
                str(data.get("telegram_id", "")),
                str(data.get("telegram_username", "")),
                data.get("name", ""),
                int(data.get("age", 0) or 0),
                data.get("city", ""),
                data.get("school", ""),
                data.get("lang", "ru"),
                json.dumps(data.get("history", []), ensure_ascii=False),
                json.dumps(scores, ensure_ascii=False),
                status == "shortlist",
                status,
                rec,
                analysis.get("summary", ""),
                bool(analysis.get("ai_text_detected")),
                analysis.get("ai_text_reason"),
            ))
        conn.commit()
        logger.info(f"✅ Saved: {data.get('name')} | score={analysis.get('total')} | {rec}")
        return cid
    except Exception as e:
        conn.rollback(); logger.error(f"save error: {e}"); raise
    finally:
        conn.close()


# ══════════════════════════════════════════════
# АСИНХРОННОЕ (asyncpg) — FastAPI
# ══════════════════════════════════════════════

async def create_pool():
    """Создаёт asyncpg пул. Вызвать один раз при старте FastAPI."""
    try:
        import asyncpg
        return await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    except ImportError:
        raise RuntimeError("Установи: pip install asyncpg")


async def init_db_async(pool):
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)
    logger.info("✅ PostgreSQL (async): таблица готова")


# ── Конвертация строки БД → формат фронтенда ─

def _parse_json(val):
    if val is None: return None
    if isinstance(val, (dict, list)): return val
    try: return json.loads(val)
    except Exception: return None


def row_to_frontend(row: dict) -> dict:
    """Конвертирует строку PostgreSQL в формат CANDIDATES[i] фронтенда."""
    scores    = _parse_json(row.get("scores")) or {}
    interview = _parse_json(row.get("interview")) or []

    answers = [
        {"q": h.get("q",""), "a": h.get("a","")}
        for h in interview if h.get("q") and h.get("a")
    ]

    ts = row.get("created_at", "")
    date_str = ts.isoformat()[:10] if hasattr(ts, "isoformat") else str(ts)[:10]

    return {
        "id":             row["id"],
        "name":           row.get("name", ""),
        "username":       row.get("telegram_username") or f"tg_{row.get('telegram_id','')}",
        "score":          scores.get("total", 0),
        "leadership":     scores.get("leadership", 0),
        "growth":         scores.get("trajectory", 0),  # было "growth"
        "motivation":     scores.get("motivation", 0),
        "authenticity":   scores.get("authenticity", 0),
        "status":         row.get("status", "review"),
        "ai_text":        bool(row.get("ai_text_detected", False)),
        "date":           date_str,
        "summary":        row.get("summary", ""),
        "answers":        answers,
        "city":           row.get("city", ""),
        "school":         row.get("school", ""),
        "language":       row.get("language", "ru"),
        "shortlisted":    bool(row.get("shortlisted", False)),
        "recommendation": row.get("recommendation", ""),
        "ai_text_reason": row.get("ai_text_reason"),
    }


# ── Async CRUD ────────────────────────────────

async def db_get_all(pool, status_filter: str = None, search: str = None):
    async with pool.acquire() as conn:
        conditions = []
        params = []
        if status_filter:
            params.append(status_filter)
            conditions.append(f"status = ${len(params)}")
        if search:
            params.append(f"%{search}%")
            conditions.append(f"name ILIKE ${len(params)}")
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = await conn.fetch(f"SELECT * FROM candidates {where} ORDER BY created_at DESC", *params)
        return [dict(r) for r in rows]


async def db_get_one(pool, cid: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM candidates WHERE id=$1", cid)
    return dict(row) if row else None


async def db_update_status(pool, cid: str, status: str, shortlisted: bool):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE candidates SET status=$1, shortlisted=$2 WHERE id=$3",
            status, shortlisted, cid
        )


async def db_update_scores(pool, cid: str, scores: dict, status: str = "scored"):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE candidates SET scores=$1::jsonb, status=$2 WHERE id=$3",
            json.dumps(scores, ensure_ascii=False), status, cid
        )


async def db_insert(pool, fields: dict) -> str:
    """Вставляет нового кандидата через FastAPI."""
    cid = fields.get("id") or f"c_{uuid.uuid4().hex}"
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO candidates
              (id,telegram_id,name,age,city,school,language,
               interview,scores,shortlisted,status,
               recommendation,summary,ai_text_detected)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
            ON CONFLICT (id) DO NOTHING
        """,
            cid,
            str(fields.get("telegram_id","")),
            fields.get("name",""),
            int(fields.get("age",0) or 0),
            fields.get("city",""),
            fields.get("school","") or fields.get("university",""),
            fields.get("language","ru"),
            json.dumps(fields.get("interview",[]), ensure_ascii=False),
            json.dumps(fields.get("scores"), ensure_ascii=False) if fields.get("scores") else None,
            bool(fields.get("shortlisted",False)),
            fields.get("status","pending"),
            fields.get("recommendation"),
            fields.get("summary"),
            bool(fields.get("ai_text_detected",False)),
        )
    return cid


async def db_delete(pool, cid: str):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM candidates WHERE id=$1", cid)


async def db_add_comment(pool, cid: str, comment: dict):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE candidates
            SET scores = jsonb_set(
                COALESCE(scores, '{}'::jsonb),
                '{comments}',
                COALESCE(scores->'comments','[]'::jsonb) || $1::jsonb
            )
            WHERE id = $2
        """, json.dumps([comment], ensure_ascii=False), cid)
