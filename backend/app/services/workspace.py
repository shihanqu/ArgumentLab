import shutil
from pathlib import Path

from fastapi import HTTPException

from app.core.config import Settings, get_settings


def ensure_workspace(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    for path in [
        settings.matters_dir,
        settings.uploads_dir,
        settings.indexes_dir,
        settings.exports_dir,
        settings.config_dir,
        settings.logs_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._- " else "_" for char in filename)
    cleaned = cleaned.strip().replace(" ", "_")
    return cleaned or "upload.bin"


def matter_upload_dir(matter_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    path = settings.uploads_dir / matter_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def matter_export_dir(matter_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    path = settings.exports_dir / matter_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_matter_files(matter_id: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    for base in [settings.uploads_dir, settings.indexes_dir, settings.exports_dir, settings.matters_dir]:
        path = base / matter_id
        if path.exists():
            shutil.rmtree(path)


def assert_local_mode(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if settings.auth_mode != "local" or settings.storage_mode != "local":
        raise HTTPException(status_code=400, detail="This prototype build only enables AUTH_MODE=local and STORAGE_MODE=local.")

