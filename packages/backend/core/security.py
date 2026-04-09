from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import bcrypt
import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidAlgorithmError, InvalidSignatureError, InvalidTokenError
from pydantic import ValidationError

from packages.backend.core.config import get_settings
from packages.backend.schemas.auth import TokenPayload


class TokenDecodeError(Exception):
	def __init__(
		self,
		code: str,
		message: str,
		status_code: int = HTTPStatus.UNAUTHORIZED,
	) -> None:
		super().__init__(message)
		self.code = code
		self.message = message
		self.status_code = int(status_code)

	def as_detail(self) -> dict[str, str]:
		return {
			"code": self.code,
			"message": self.message,
		}


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


def decode_token(token: str) -> TokenPayload:
	settings = get_settings()
	secret_key = settings.jwt_secret_key

	if not token.strip():
		raise TokenDecodeError(
			code="token_missing",
			message="Token is missing.",
		)

	if not secret_key:
		raise TokenDecodeError(
			code="auth_not_configured",
			message="JWT authentication is not configured on the server.",
			status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
		)

	try:
		payload = jwt.decode(
			token,
			secret_key,
			algorithms=[settings.jwt_algorithm],
			options={"require": ["exp", "sub", "role"]},
		)
	except ExpiredSignatureError as exc:
		raise TokenDecodeError(
			code="token_expired",
			message="Token has expired.",
		) from exc
	except InvalidSignatureError as exc:
		raise TokenDecodeError(
			code="token_signature_invalid",
			message="Token signature is invalid.",
		) from exc
	except InvalidAlgorithmError as exc:
		raise TokenDecodeError(
			code="token_algorithm_invalid",
			message="Token algorithm is invalid.",
		) from exc
	except DecodeError as exc:
		raise TokenDecodeError(
			code="token_malformed",
			message="Token is malformed and could not be decoded.",
		) from exc
	except InvalidTokenError as exc:
		raise TokenDecodeError(
			code="token_invalid",
			message="Token is invalid.",
		) from exc

	try:
		return TokenPayload.model_validate(payload)
	except ValidationError as exc:
		raise TokenDecodeError(
			code="token_payload_invalid",
			message="Token payload is invalid.",
		) from exc
