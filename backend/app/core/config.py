from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    auth_mode: Literal["local", "cloud"] = Field(default="local", alias="AUTH_MODE")
    storage_mode: Literal["local", "s3"] = Field(default="local", alias="STORAGE_MODE")
    model_gateway: str = Field(default="litellm", alias="MODEL_GATEWAY")
    workspace: Path = Field(default=Path("~/.argument-lab"), alias="ARGUMENT_LAB_WORKSPACE")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    prompt_version: str = "v0_1"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    @field_validator("workspace", mode="before")
    @classmethod
    def expand_workspace(cls, value: str | Path) -> Path:
        return Path(value).expanduser()

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            if self.database_url.startswith("sqlite:///~"):
                return "sqlite:///" + str(Path(self.database_url.removeprefix("sqlite:///")).expanduser())
            return self.database_url
        return f"sqlite:///{self.workspace / 'config' / 'argument_lab.sqlite3'}"

    @property
    def matters_dir(self) -> Path:
        return self.workspace / "matters"

    @property
    def uploads_dir(self) -> Path:
        return self.workspace / "uploads"

    @property
    def indexes_dir(self) -> Path:
        return self.workspace / "indexes"

    @property
    def exports_dir(self) -> Path:
        return self.workspace / "exports"

    @property
    def config_dir(self) -> Path:
        return self.workspace / "config"

    @property
    def logs_dir(self) -> Path:
        return self.workspace / "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()

