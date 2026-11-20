from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MedTrust-Engine Backend Configuration Settings."""

    # Project Information
    PROJECT_NAME: str = "MedTrust Engine"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data_storage"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    INDEX_DIR: Path = DATA_DIR / "indexes"

    # Database Configuration (Defaults to SQLite for local zero-config, supports PostgreSQL via env)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'medtrust.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'medtrust.db'}"

    # Retrieval Configuration
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    TOP_K_EVIDENCE: int = 5
    TOP_N_CANDIDATES: int = 20
    RRF_K: int = 60
    RRF_ALPHA: float = 0.5  # Weight for dense retrieval in RRF (0.5 = balanced dense/sparse)
    CHUNK_SIZE_TOKENS: int = 350
    CHUNK_OVERLAP_TOKENS: int = 50

    # Safety & File Upload Boundaries
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    MAX_PDF_PAGES: int = 100
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def init_directories(self) -> None:
        """Ensure necessary storage directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.INDEX_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_directories()
