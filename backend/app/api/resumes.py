from io import BytesIO
from hashlib import sha256
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from uuid import UUID, uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, field_validator, model_validator
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import _csrf, _same_origin, current_user
from app.career.analyzer import analyze_resume
from app.career.resume_storage import read_resume_file
from app.core.config import get_settings
from app.db import get_db
from app.models import AnalysisRun, Resume, User

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024


class ResumeView(BaseModel):
    id: str
    original_name: str
    content_type: str

    model_config = {"from_attributes": True}


class AnalyzeResumeRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=120)
    additional_evidence_text: str = Field(default="", max_length=5_000)
    evidence_type: Literal["project", "experience"] | None = None
    evidence_url: str | None = Field(default=None, max_length=2048)
    baseline_run_id: UUID | None = None

    @field_validator("evidence_url")
    @classmethod
    def require_https_evidence_link(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        from urllib.parse import urlsplit

        parsed = urlsplit(value.strip())
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Use a full HTTPS link for supporting evidence.")
        return value.strip()

    @model_validator(mode="after")
    def validate_evidence(self):
        has_text = bool(self.additional_evidence_text.strip())
        if has_text and (len(self.additional_evidence_text.strip()) < 20 or self.evidence_type is None):
            raise ValueError("Describe at least 20 characters of completed project or experience evidence and choose its type.")
        if not has_text and (self.evidence_type is not None or self.evidence_url is not None):
            raise ValueError("Add an evidence description before selecting its type or link.")
        return self


def _validate_upload(filename: str, data: bytes) -> str:
    extension = Path(filename).suffix.casefold()
    if extension == ".pdf" and data.startswith(b"%PDF-"):
        return "application/pdf"
    if extension == ".docx" and data.startswith(b"PK"):
        try:
            with ZipFile(BytesIO(data)) as document:
                infos = document.infolist()
                total_size = sum(info.file_size for info in infos)
                valid = "word/document.xml" in document.namelist()
                if valid and len(infos) <= 1000 and total_size <= MAX_UNCOMPRESSED_BYTES:
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except (BadZipFile, OSError):
            pass
    raise HTTPException(status_code=415, detail="Upload a valid PDF or DOCX resume.")


@router.get("", response_model=list[ResumeView])
def list_resumes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.created_at.desc())
        .limit(10)
    ).all()


@router.get("/{resume_id}/download")
def download_resume(resume_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    resume = db.scalar(select(Resume).where(Resume.id == str(resume_id), Resume.user_id == user.id))
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found in your account.")
    try:
        data = read_resume_file(resume, get_settings())
    except FileNotFoundError:
        raise HTTPException(status_code=410, detail="The stored resume file is missing. Upload it again to continue.") from None
    except ValueError as error:
        raise HTTPException(status_code=413, detail=str(error)) from None
    safe_name = Path(resume.original_name).name[:255] or "resume"
    return StreamingResponse(
        BytesIO(data),
        media_type=resume.content_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_name, safe='')}"},
    )


@router.post("", response_model=ResumeView, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    _origin_checked: None = Depends(_same_origin),
    _csrf_checked: None = Depends(_csrf),
):
    settings = get_settings()
    filename = Path(file.filename or "resume").name[:255]
    data = await file.read(settings.max_upload_bytes + 1)
    if not data or len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Resume must be smaller than 20 MB.")
    content_type = _validate_upload(filename, data)
    storage_key = str(uuid4())
    root = settings.upload_path
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{storage_key}{Path(filename).suffix.casefold()}"
    with destination.open("xb") as target:
        target.write(data)
    resume = Resume(
        user_id=user.id,
        original_name=filename,
        storage_key=storage_key,
        content_type=content_type,
    )
    db.add(resume)
    try:
        db.commit()
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise
    return resume


@router.post("/{resume_id}/analyze")
def analyze_saved_resume(
    resume_id: UUID,
    payload: AnalyzeResumeRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    _origin_checked: None = Depends(_same_origin),
    _csrf_checked: None = Depends(_csrf),
):
    target_role = payload.target_role.strip()
    if len(target_role) < 2:
        raise HTTPException(status_code=422, detail="Enter a target job title.")

    resume = db.scalar(
        select(Resume).where(Resume.id == str(resume_id), Resume.user_id == user.id)
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found in your account.")

    settings = get_settings()
    root = settings.upload_path.resolve()
    destination = (root / f"{resume.storage_key}{Path(resume.original_name).suffix.casefold()}").resolve()
    if root not in destination.parents:
        raise HTTPException(status_code=404, detail="Resume not found in your account.")
    try:
        data = destination.read_bytes()
    except FileNotFoundError:
        raise HTTPException(status_code=410, detail="The stored resume file is missing. Upload it again to continue.") from None
    if not data or len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="The stored resume exceeds the current upload limit.")

    fingerprint = sha256(f"role-profile-v1\0{target_role.casefold()}".encode("utf-8")).hexdigest()
    evidence_text = payload.additional_evidence_text.strip()
    try:
        analysis = analyze_resume(
            data, resume.original_name, target_role, additional_evidence_text=evidence_text,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None

    comparison = None
    baseline = None
    if evidence_text and payload.baseline_run_id:
        baseline = db.scalar(
            select(AnalysisRun).where(
                AnalysisRun.id == str(payload.baseline_run_id),
                AnalysisRun.user_id == user.id,
                AnalysisRun.run_kind == "baseline",
                AnalysisRun.input_fingerprint == fingerprint,
            )
        )

    if evidence_text and baseline is None:
        try:
            baseline_analysis = analyze_resume(data, resume.original_name, target_role)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        baseline = AnalysisRun(
            user_id=user.id,
            resume_id=resume.id,
            target_role=target_role,
            input_fingerprint=fingerprint,
            run_kind="baseline",
            overall_coverage=baseline_analysis["match"]["overall_coverage"],
            skill_coverage=baseline_analysis["match"]["skill_coverage"],
            matched_skills=baseline_analysis["match"]["matched_skills"],
            missing_skills=baseline_analysis["match"]["missing_skills"],
            score_components=baseline_analysis["match"]["score_components"],
            evidence_summary={"source": "resume"},
        )
        db.add(baseline)
        db.flush()

    if evidence_text:
        before = baseline.overall_coverage
        after = analysis["match"]["overall_coverage"]
        comparison = {
            "before_score": before,
            "after_score": after,
            "score_change": round(after - before, 2) if before is not None and after is not None else None,
            "newly_supported_skills": analysis["match"]["evidence_matched_skills"],
            "evidence_type": payload.evidence_type,
            "supporting_url": payload.evidence_url,
            "note": "This score uses candidate-submitted project or experience text. CareerLens does not independently verify the claim or link; course completion by itself is not counted as project or experience evidence.",
        }
        run = AnalysisRun(
            user_id=user.id,
            resume_id=resume.id,
            baseline_run_id=baseline.id,
            target_role=target_role,
            input_fingerprint=fingerprint,
            run_kind="evidence",
            overall_coverage=after,
            skill_coverage=analysis["match"]["skill_coverage"],
            matched_skills=analysis["match"]["matched_skills"],
            missing_skills=analysis["match"]["missing_skills"],
            score_components=analysis["match"]["score_components"],
            evidence_summary={
                "type": payload.evidence_type,
                "supporting_url": payload.evidence_url,
                "skills": analysis["match"]["evidence_matched_skills"],
            },
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        analysis["analysis_run_id"] = run.id
        analysis["baseline_run_id"] = baseline.id
    else:
        run = AnalysisRun(
            user_id=user.id,
            resume_id=resume.id,
            target_role=target_role,
            input_fingerprint=fingerprint,
            run_kind="baseline",
            overall_coverage=analysis["match"]["overall_coverage"],
            skill_coverage=analysis["match"]["skill_coverage"],
            matched_skills=analysis["match"]["matched_skills"],
            missing_skills=analysis["match"]["missing_skills"],
            score_components=analysis["match"]["score_components"],
            evidence_summary={"source": "resume"},
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        analysis["analysis_run_id"] = run.id
        analysis["baseline_run_id"] = run.id
    analysis["comparison"] = comparison
    return analysis
