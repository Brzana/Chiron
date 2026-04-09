from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import InvalidTokenError

from packages.backend.core.config import get_settings
from packages.backend.schemas.auth import TokenPayload


def hash_password(password: str) -> str:
	password_bytes = password.encode("utf-8")
	return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
	settings = get_settings()
	expire_at = datetime.now(timezone.utc) + (
		expires_delta or timedelta(minutes=settings.jwt_expiration_minutes)
	)
	payload = data.copy()
	payload.update({"exp": expire_at})

	return jwt.encode(
		payload,
		settings.require_jwt_secret_key(),
		algorithm=settings.jwt_algorithm,
	)


def decode_token(token: str) -> TokenPayload | None:
	settings = get_settings()

	try:
		payload = jwt.decode(
			token,
			settings.require_jwt_secret_key(),
			algorithms=[settings.jwt_algorithm],
		)
	except (InvalidTokenError, RuntimeError):
		return None

	try:
		return TokenPayload.model_validate(payload)
	except Exception:
		return None
