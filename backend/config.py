from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Home Assistant connection (optional — omit for standalone mode)
    ha_url: str | None = None
    ha_token: str | None = None

    # Persistence
    data_path: str = "data"
    db_filename: str = "aipresence.db"

    # ML training
    sample_rate: float = Field(default=2.0, gt=0)
    minimum_training_samples: int = Field(default=200, gt=0)

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": "backend/.env", "env_file_encoding": "utf-8"}

    @property
    def ha_configured(self) -> bool:
        return self.ha_url is not None and self.ha_token is not None


# Backward-compatible module-level constants so existing imports
# (e.g. `from . import config; config.DATA_PATH`) keep working
# until callers are migrated in task 5.
_defaults = Settings()
DATA_PATH = _defaults.data_path
DB_FILENAME = _defaults.db_filename
SAMPLE_RATE = _defaults.sample_rate
MINIMUM_TRAINING_SAMPLES = _defaults.minimum_training_samples
