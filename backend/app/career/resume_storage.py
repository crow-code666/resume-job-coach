"""Owner-independent filesystem checks for private uploaded resume blobs."""

from pathlib import Path

from app.core.config import Settings
from app.models import Resume


def read_resume_file(resume: Resume, settings: Settings) -> bytes:
    root = settings.upload_path.resolve()
    suffix = Path(resume.original_name).suffix.casefold()
    destination = (root / f"{resume.storage_key}{suffix}").resolve()
    if root not in destination.parents:
        raise FileNotFoundError
    data = destination.read_bytes()
    if not data or len(data) > settings.max_upload_bytes:
        raise ValueError("The stored resume exceeds the current upload limit.")
    return data
