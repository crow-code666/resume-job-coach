from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    sessions: Mapped[list["LoginSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    candidate_profile: Mapped[Optional["CandidateProfile"]] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    applications: Mapped[list["JobApplication"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class CandidateProfile(Base):
    """Optional international job-search preferences, separate from login data."""

    __tablename__ = "candidate_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, default="IN")
    country_name: Mapped[str] = mapped_column(String(80), nullable=False, default="India")
    city: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    time_zone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    education_level: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    preferred_roles: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skill_interests: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    user: Mapped[User] = relationship(back_populates="candidate_profile")


class JobApplication(Base):
    """A private, owner-scoped application tracker entry."""

    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    job_title: Mapped[str] = mapped_column(String(180), nullable=False)
    company: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    posting_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="saved")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    user: Mapped[User] = relationship(back_populates="applications")


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    user: Mapped[User] = relationship(back_populates="sessions")


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (UniqueConstraint("user_id", "storage_key", name="uq_resume_owner_storage"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    user: Mapped[User] = relationship(back_populates="resumes")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class AnalysisRun(Base):
    """Compact, owner-scoped score history; avoids storing parsed resume text."""

    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    baseline_run_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_runs.id", ondelete="SET NULL"), nullable=True)
    target_role: Mapped[str] = mapped_column(String(120), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    run_kind: Mapped[str] = mapped_column(String(24), nullable=False, default="baseline")
    overall_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    skill_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    score_components: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    user: Mapped[User] = relationship(back_populates="analysis_runs")
    resume: Mapped[Resume] = relationship(back_populates="analysis_runs")


class InterviewSession(Base):
    """Private interview practice, stored without the candidate's resume text."""

    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    target_role: Mapped[str] = mapped_column(String(120), nullable=False)
    focus_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    final_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user: Mapped[User] = relationship(back_populates="interview_sessions")
    resume: Mapped[Resume] = relationship(back_populates="interview_sessions")
    turns: Mapped[list["InterviewTurn"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="InterviewTurn.turn_number")


class InterviewTurn(Base):
    """One question, candidate answer, and rubric evaluation in a session."""

    __tablename__ = "interview_turns"
    __table_args__ = (UniqueConstraint("session_id", "turn_number", name="uq_interview_turn_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    turn_number: Mapped[int] = mapped_column(nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    focus_skill: Mapped[str] = mapped_column(String(120), nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluated_by: Mapped[str | None] = mapped_column(String(24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    session: Mapped[InterviewSession] = relationship(back_populates="turns")
