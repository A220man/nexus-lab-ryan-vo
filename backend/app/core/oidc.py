from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog
from app.core.config import get_settings
from app.core.security import Role, TokenData, create_access_token, create_refresh_token, decode_token
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from pydantic import BaseModel

logger = structlog.get_logger()

settings = get_settings()


class OIDCConfig(BaseModel):
    """Keycloak OIDC configuration from well-known endpoint."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    end_session_endpoint: str
    code_challenge_methods_supported: list[str] = ["S256"]


class TokenResponse(BaseModel):
    """OIDC token response."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    id_token: str | None = None
    scope: str | None = None


class UserInfo(BaseModel):
    """OIDC user info response."""

    sub: str
    email: str | None = None
    email_verified: bool = False
    name: str | None = None
    preferred_username: str | None = None
    roles: list[str] = []


class AuthState(BaseModel):
    """PKCE auth state stored in session."""

    state: str
    code_verifier: str
    redirect_uri: str
    created_at: datetime
    nonce: str | None = None


class OIDCClient:
    """Keycloak OIDC client with PKCE support."""

    def __init__(self):
        self._config: OIDCConfig | None = None
        self._jwks: dict[str, Any] | None = None
        self._jwks_fetched_at: datetime | None = None

    async def get_config(self) -> OIDCConfig:
        """Fetch OIDC configuration from Keycloak well-known endpoint."""
        if self._config:
            return self._config

        well_known_url = f"{settings.keycloak_issuer}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(well_known_url)
            resp.raise_for_status()
            self._config = OIDCConfig(**resp.json())
            logger.info("oidc_config_loaded", issuer=self._config.issuer)
            return self._config

    async def get_jwks(self) -> dict[str, Any]:
        """Fetch and cache JWKS from Keycloak."""
        now = datetime.now(UTC)
        if self._jwks and self._jwks_fetched_at and (now - self._jwks_fetched_at) < timedelta(hours=1):
            return self._jwks

        config = await self.get_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(config.jwks_uri)
            resp.raise_for_status()
            self._jwks = resp.json()
            self._jwks_fetched_at = now
            logger.info("jwks_loaded", keys_count=len(self._jwks.get("keys", [])))
            return self._jwks

    def get_public_key(self, kid: str) -> str | None:
        """Get RSA public key by key ID from JWKS."""
        if not self._jwks:
            return None
        for key in self._jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwk.construct(key).to_pem().decode()
        return None

    async def verify_id_token(self, id_token: str, nonce: str | None = None) -> TokenData | None:
        """Verify ID token signature and claims."""
        try:
            # Get unverified header to find key ID
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")
            if not kid:
                logger.warning("id_token_missing_kid")
                return None

            # Get public key
            public_key = self.get_public_key(kid)
            if not public_key:
                # Refresh JWKS and retry
                await self.get_jwks()
                public_key = self.get_public_key(kid)
                if not public_key:
                    logger.warning("id_token_kid_not_found", kid=kid)
                    return None

            # Decode and verify
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=settings.keycloak_client_id,
                issuer=settings.keycloak_issuer,
            )

            # Verify nonce if provided
            if nonce and payload.get("nonce") != nonce:
                logger.warning("id_token_nonce_mismatch", expected=nonce, got=payload.get("nonce"))
                return None

            # Extract roles from realm_access and resource_access
            roles = []
            if "realm_access" in payload and "roles" in payload["realm_access"]:
                roles.extend(payload["realm_access"]["roles"])
            if "resource_access" in payload:
                for client_roles in payload["resource_access"].values():
                    if "roles" in client_roles:
                        roles.extend(client_roles["roles"])

            return TokenData(
                sub=payload["sub"],
                email=payload.get("email"),
                name=payload.get("name"),
                roles=roles,
                exp=payload["exp"],
                iat=payload["iat"],
                jti=payload.get("jti", f"{payload['sub']}:{payload['iat']}"),
            )
        except JWTError as e:
            logger.warning("id_token_verification_failed", error=str(e))
            return None

    def build_auth_url(self, state: str, code_challenge: str, redirect_uri: str, nonce: str | None = None) -> str:
        """Build Keycloak authorization URL with PKCE."""
        config = self._config
        if not config:
            # Use settings directly if config not loaded yet
            auth_url = settings.keycloak_auth_url
        else:
            auth_url = config.authorization_endpoint

        params = {
            "client_id": settings.keycloak_client_id,
            "response_type": "code",
            "scope": "openid profile email roles offline_access",
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if nonce:
            params["nonce"] = nonce

        return f"{auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, code_verifier: str, redirect_uri: str) -> TokenResponse | None:
        """Exchange authorization code for tokens."""
        config = await self.get_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            data = {
                "grant_type": "authorization_code",
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            }
            try:
                resp = await client.post(
                    config.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                resp.raise_for_status()
                return TokenResponse(**resp.json())
            except httpx.HTTPStatusError as e:
                logger.warning("code_exchange_failed", status=e.response.status_code, response=e.response.text)
                return None

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse | None:
        """Refresh access token using refresh token."""
        config = await self.get_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            data = {
                "grant_type": "refresh_token",
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
                "refresh_token": refresh_token,
            }
            try:
                resp = await client.post(
                    config.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                resp.raise_for_status()
                return TokenResponse(**resp.json())
            except httpx.HTTPStatusError as e:
                logger.warning("token_refresh_failed", status=e.response.status_code, response=e.response.text)
                return None

    async def get_userinfo(self, access_token: str) -> UserInfo | None:
        """Fetch user info from Keycloak."""
        config = await self.get_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    config.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
                data = resp.json()
                # Extract roles from realm_access
                roles = []
                if "realm_access" in data and "roles" in data["realm_access"]:
                    roles.extend(data["realm_access"]["roles"])
                return UserInfo(
                    sub=data["sub"],
                    email=data.get("email"),
                    email_verified=data.get("email_verified", False),
                    name=data.get("name"),
                    preferred_username=data.get("preferred_username"),
                    roles=roles,
                )
            except httpx.HTTPStatusError as e:
                logger.warning("userinfo_failed", status=e.response.status_code, response=e.response.text)
                return None

    def build_logout_url(self, post_logout_redirect_uri: str | None = None, id_token_hint: str | None = None) -> str:
        """Build Keycloak logout URL."""
        config = self._config
        if not config:
            logout_url = settings.keycloak_logout_url
        else:
            logout_url = config.end_session_endpoint

        params = {}
        if post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = post_logout_redirect_uri
        if id_token_hint:
            params["id_token_hint"] = id_token_hint

        if params:
            return f"{logout_url}?{urlencode(params)}"
        return logout_url


# Global OIDC client instance
oidc_client = OIDCClient()


# In-memory state store (use Redis in production)
_auth_states: dict[str, AuthState] = {}


def store_auth_state(state: AuthState) -> None:
    """Store PKCE auth state."""
    _auth_states[state.state] = state
    # Cleanup old states (>10 min)
    cutoff = datetime.now(UTC) - timedelta(minutes=10)
    for k, v in list(_auth_states.items()):
        if v.created_at < cutoff:
            del _auth_states[k]


def get_auth_state(state: str) -> AuthState | None:
    """Retrieve and remove PKCE auth state."""
    return _auth_states.pop(state, None)


def generate_code_verifier() -> str:
    """Generate PKCE code verifier (43-128 chars)."""
    import secrets
    return secrets.token_urlsafe(32)[:128]


def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code challenge (S256)."""
    import hashlib
    import base64
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def generate_state() -> str:
    """Generate random state parameter."""
    import secrets
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    """Generate random nonce."""
    import secrets
    return secrets.token_urlsafe(32)


async def authenticate_user(code: str, state: str) -> tuple[TokenData, str, str] | None:
    """
    Complete OIDC authentication flow.
    Returns (token_data, access_token, refresh_token) or None.
    """
    auth_state = get_auth_state(state)
    if not auth_state:
        logger.warning("auth_state_not_found", state=state[:8])
        return None

    # Exchange code for tokens
    token_resp = await oidc_client.exchange_code(code, auth_state.code_verifier, auth_state.redirect_uri)
    if not token_resp:
        return None

    # Verify ID token
    token_data = await oidc_client.verify_id_token(token_resp.id_token or "", auth_state.nonce)
    if not token_data:
        return None

    # Create internal tokens
    access_token = create_access_token(
        {
            "sub": token_data.sub,
            "email": token_data.email,
            "name": token_data.name,
            "roles": token_data.roles,
        }
    )
    refresh_token = create_refresh_token(
        {
            "sub": token_data.sub,
            "email": token_data.email,
            "name": token_data.name,
            "roles": token_data.roles,
        }
    )

    return token_data, access_token, refresh_token


def create_demo_user() -> TokenData:
    """Create a demo user for local development."""
    now = datetime.now(UTC)
    return TokenData(
        sub="demo-user",
        email="demo@nexus-lab.local",
        name="Demo User",
        roles=[Role.VIEWER, Role.OPERATOR],
        exp=int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        iat=int(now.timestamp()),
        jti=f"demo:{int(now.timestamp() * 1000)}",
    )


def create_demo_tokens() -> tuple[str, str]:
    """Create demo access and refresh tokens."""
    user = create_demo_user()
    access = create_access_token(
        {
            "sub": user.sub,
            "email": user.email,
            "name": user.name,
            "roles": user.roles,
        }
    )
    refresh = create_refresh_token(
        {
            "sub": user.sub,
            "email": user.email,
            "name": user.name,
            "roles": user.roles,
        }
    )
    return access, refresh
