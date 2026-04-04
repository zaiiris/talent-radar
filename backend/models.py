"""
models.py — Pydantic-схемы данных для всего API TalentRadar.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any


# ── Входящие ──────────────────────────────────

class CandidateCreate(BaseModel):
    telegram_id:  str
    name:         str = Field(..., min_length=2, max_length=120)
    age:          int = Field(..., ge=14, le=35)
    city:         str
    university:   str
    specialty:    str
    essay:        Optional[str] = None
    achievements: List[str]    = Field(default_factory=list)

    @field_validator("achievements")
    @classmethod
    def clean(cls, v: List[str]) -> List[str]:
        return [a.strip() for a in v if a.strip()]


class BotAnswer(BaseModel):
    question_id:   str
    question_text: str
    answer_text:   str
    timestamp:     Optional[str] = None


class BotAnswerSubmit(BaseModel):
    answers: List[BotAnswer]


class ShortlistUpdate(BaseModel):
    shortlisted: bool


class WeightsUpdate(BaseModel):
    growth_trajectory: float = Field(..., ge=0, le=1)
    leadership:        float = Field(..., ge=0, le=1)
    authenticity:      float = Field(..., ge=0, le=1)
    communication:     float = Field(..., ge=0, le=1)

    @field_validator("communication")
    @classmethod
    def must_sum_to_one(cls, v, info) -> float:
        d = info.data
        total = d.get("growth_trajectory",0) + d.get("leadership",0) + d.get("authenticity",0) + v
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Сумма весов = {round(total,3)}, нужно 1.0")
        return v


class CommentCreate(BaseModel):
    author: str = Field(..., min_length=2, max_length=60)
    text:   str = Field(..., min_length=3, max_length=1000)


# ── Исходящие ─────────────────────────────────

class CandidateResponse(BaseModel):
    id:           str
    telegram_id:  str
    name:         str
    age:          int
    city:         str
    university:   str
    specialty:    str
    essay:        Optional[str] = None
    achievements: List[str]    = Field(default_factory=list)
    created_at:   str
    status:       str
    shortlisted:  bool = False
    bot_answers:  List[Dict[str, Any]] = Field(default_factory=list)
    scores:       Optional[Dict[str, Any]] = None
    comments:     List[Dict[str, Any]]     = Field(default_factory=list)


class CandidateListResponse(BaseModel):
    candidates:  List[CandidateResponse]
    total:       int
    scored:      int
    shortlisted: int


class AnalyticsSummary(BaseModel):
    total_candidates: int
    scored:           int
    shortlisted:      int
    avg_score:        float
    max_score:        float
    min_score:        float
    ai_detected:      int
    underdog_count:   int
    recommendation_breakdown: Dict[str, int]
