import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
	jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")
	jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
	jwt_expiration_minutes: int = Field(default=60, alias="JWT_EXPIRATION_MINUTES")

	def require_jwt_secret_key(self) -> str:
		if not self.jwt_secret_key:
			raise RuntimeError("JWT_SECRET_KEY environment variable is not configured.")

		return self.jwt_secret_key


@lru_cache
def get_settings() -> Settings:
	return Settings.model_validate(os.environ)
