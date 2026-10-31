from app.core.config import get_settings
from app.core.oidc import (
    AuthState,
    generate_code_challenge,
    generate_code_verifier,
    generate_nonce,
    generate_state,
    oidc_client,
    store_auth_state,
    create_demo_tokens,
    create_demo_user,
)
from app.core.security import TokenData, verify_token
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


class LoginResponse(BaseModel):
    """Login initiation response."""

    auth_url: str
    state: str


class TokenResponse(BaseModel):
    """Token response for frontend."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user: dict


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UserInfoResponse(BaseModel):
    """Current user info."""

    sub: str
    email: str | None = None
    name: str | None = None
    roles: list[str] = []


@router.get("/login", response_model=LoginResponse)
async def login(redirect_uri: str | None = None):
    """
    Initiate OIDC login flow with PKCE.
    Returns authorization URL and state for frontend.
    """
    # Demo mode: return demo tokens directly
    if settings.demo_mode:
        access_token, refresh_token = create_demo_tokens()
        user = create_demo_user()
        # Redirect to frontend with tokens in fragment
        frontend_url = redirect_uri or settings.frontend_url
        fragment = f"access_token={access_token}&refresh_token={refresh_token}&token_type=bearer&expires_in=1800"
        return RedirectResponse(url=f"{frontend_url}/#/callback?{fragment}")

    # Generate PKCE parameters
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = generate_state()
    nonce = generate_nonce()

    # Store auth state
    auth_state = AuthState(
        state=state,
        code_verifier=code_verifier,
        redirect_uri=redirect_uri or settings.frontend_url,
        created_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        nonce=nonce,
    )
    store_auth_state(auth_state)

    # Build authorization URL
    auth_url = oidc_client.build_auth_url(state, code_challenge, auth_state.redirect_uri, nonce)

    return LoginResponse(auth_url=auth_url, state=state)


@router.get("/callback")
async def callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """
    OIDC callback endpoint.
    Exchanges code for tokens and redirects to frontend.
    """
    # Handle OAuth errors
    if error:
        frontend_url = settings.frontend_url
        return RedirectResponse(url=f"{frontend_url}/#/login?error={error}")

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or state")

    # Complete authentication
    result = await __import__("app.core.oidc", fromlist=["authenticate_user"]).authenticate_user(code, state)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    token_data, access_token, refresh_token = result

    # Redirect to frontend with tokens in fragment
    fragment = f"access_token={access_token}&refresh_token={refresh_token}&token_type=bearer&expires_in=1800"
    return RedirectResponse(url=f"{settings.frontend_url}/#/callback?{fragment}")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    token_data = verify_token(request.refresh_token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Create new tokens
    access_token = __import__("app.core.security", fromlist=["create_access_token"]).create_access_token(
        {
            "sub": token_data.sub,
            "email": token_data.email,
            "name": token_data.name,
            "roles": token_data.roles,
        }
    )
    refresh_token = __import__("app.core.security", fromlist=["create_refresh_token"]).create_refresh_token(
        {
            "sub": token_data.sub,
            "email": token_data.email,
            "name": token_data.name,
            "roles": token_data.roles,
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "sub": token_data.sub,
            "email": token_data.email,
            "name": token_data.name,
            "roles": token_data.roles,
        },
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(token_data: TokenData = Depends(verify_token)):
    """
    Get current authenticated user info.
    Requires valid access token.
    """
    return UserInfoResponse(
        sub=token_data.sub,
        email=token_data.email,
        name=token_data.name,
        roles=token_data.roles,
    )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint.
    In demo mode, just returns success.
    In production, redirects to Keycloak logout.
    """
    if settings.demo_mode:
        return {"message": "Logged out successfully"}

    # Get ID token from Authorization header
    auth_header = request.headers.get("Authorization")
    id_token_hint = None
    if auth_header and auth_header.startswith("Bearer "):
        id_token_hint = auth_header[7:]

    logout_url = oidc_client.build_logout_url(
        post_logout_redirect_uri=settings.frontend_url,
        id_token_hint=id_token_hint,
    )
    return {"logout_url": logout_url}


@router.get("/config")
async def auth_config():
    """
    Get auth configuration for frontend.
    """
    return {
        "demo_mode": settings.demo_mode,
        "keycloak_url": settings.keycloak_url,
        "keycloak_realm": settings.keycloak_realm,
        "keycloak_client_id": settings.keycloak_client_id,
    }
