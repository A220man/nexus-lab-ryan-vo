from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from app.core.config import get_settings
from jose import JWTError, jwt
from pydantic import BaseModel

logger = structlog.get_logger()

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenData(BaseModel):
    sub: str
    email: str | None = None
    name: str | None = None
    roles: list[str] = []
    exp: int
    iat: int
    jti: str


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update(
        {
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "jti": f"{data.get('sub', '')}:{int(now.timestamp() * 1000)}",
        }
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    return create_access_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except JWTError as e:
        logger.warning("token_decode_failed", error=str(e))
        return None


def verify_token(token: str) -> TokenData | None:
    """Verify access token and return token data if valid."""
    token_data = decode_token(token)
    if not token_data:
        return None
    # Check expiration
    if datetime.fromtimestamp(token_data.exp, tz=UTC) < datetime.now(UTC):
        logger.warning("token_expired", sub=token_data.sub)
        return None
    return token_data


# Role definitions
class Role:
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"

    @classmethod
    def all(cls) -> list[str]:
        return [cls.VIEWER, cls.OPERATOR, cls.ADMIN]

    @classmethod
    def hierarchy(cls) -> dict[str, int]:
        return {cls.VIEWER: 1, cls.OPERATOR: 2, cls.ADMIN: 3}

    @classmethod
    def has_permission(cls, user_roles: list[str], required: str) -> bool:
        user_level = max((cls.hierarchy().get(r, 0) for r in user_roles), default=0)
        required_level = cls.hierarchy().get(required, 0)
        return user_level >= required_level
