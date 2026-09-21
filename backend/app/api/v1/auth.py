from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.db.database import get_db
from app.db.models import User, Family, Role
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
    oauth2_scheme,
)
from app.core.config import settings
router = APIRouter()


oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    },
)


# -----------------------------
# Google Login
# -----------------------------

@router.get("/debug-token")
async def debug_token(
    token: str = Depends(oauth2_scheme),
):
    return {
        "token_received": bool(token),
        "token_length": len(token),
        "token_start": token[:20],
    }



@router.get("/google/login")
async def google_login(request: Request):
    #redirect_uri = settings.google_redirect_uri

    return await oauth.google.authorize_redirect(
        request,
       settings.google_redirect_uri,
    )


# -----------------------------
# Google Callback
# -----------------------------

@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        token = await oauth.google.authorize_access_token(request)

        user_info = token.get("userinfo")

        if not user_info:
            user_info = await oauth.google.userinfo(token=token)

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Google authentication failed: {str(exc)}",
        )

    email = user_info.get("email")
    name = user_info.get("name") or email

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Google account did not provide an email address",
        )

    # Check existing user
    result = (
        await db.execute(
            select(User).where(User.email == email)
        )
    )#.scalar_one_or_none()
    user = result.scalar_one_or_none()
    # Create user if doesn't exist
    if not user:

        user = User(
            email=email,
            name=name,
            password_hash=None,
            role=Role.PARENT,
        )

        db.add(user)

        await db.flush()

        family = Family(owner_id=user.id)

        db.add(family)

        await db.commit()

        await db.refresh(user)

    # Create our JWT tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "message": "Google authentication successful",
        "user_id": str(user.id),
        "email": user.email,
        "name": user.name,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@router.post("/google", response_model=TokenResponse)
async def google_login(
    body: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Flutter Google Sign-In endpoint.

    Flutter sends a Google ID token.
    Backend verifies the token with Google.
    Backend then creates/finds the local user
    and returns the normal AI Parent Tutor JWT tokens.
    """

    # -----------------------------------------------------
    # 1. Verify Google ID token
    # -----------------------------------------------------

    if not settings.google_client_id:
        raise HTTPException(
            status_code=500,
            detail="Google client ID is not configured",
        )

    try:
        google_user = google_id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google ID token",
        )

    # -----------------------------------------------------
    # 2. Get Google user information
    # -----------------------------------------------------

    google_id = google_user.get("sub")
    email = google_user.get("email")
    name = google_user.get("name") or email

    if not google_id:
        raise HTTPException(
            status_code=400,
            detail="Google account did not provide a user ID",
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Google account did not provide an email address",
        )

    # -----------------------------------------------------
    # 3. Find user by Google ID
    # -----------------------------------------------------

    result = await db.execute(
        select(User).where(User.google_id == google_id)
    )

    user = result.scalar_one_or_none()

    # -----------------------------------------------------
    # 4. If Google ID is not linked, check email
    # -----------------------------------------------------

    if not user:
        result = await db.execute(
            select(User).where(User.email == email)
        )

        user = result.scalar_one_or_none()

        if user:
            # Existing email/password account.
            # Link this Google account to the existing user.
            if user.google_id and user.google_id != google_id:
                raise HTTPException(
                    status_code=409,
                    detail="This email is already linked to another Google account",
                )

            user.google_id = google_id

        else:
            # -------------------------------------------------
            # 5. Create a new parent account
            # -------------------------------------------------

            user = User(
                email=email,
                name=name,
                password_hash=None,
                google_id=google_id,
                role=Role.PARENT,
            )

            db.add(user)

            await db.flush()

            # Every parent gets a family
            family = Family(owner_id=user.id)

            db.add(family)

        await db.commit()
        await db.refresh(user)

    # -----------------------------------------------------
    # 6. Create AI Parent Tutor JWT tokens
    # -----------------------------------------------------

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):

    existing_user = (
        await db.execute(
            select(User).where(User.email == body.email)
        )
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=Role.PARENT,
    )

    db.add(user)

    await db.flush()

    family = Family(
        owner_id=user.id
    )

    db.add(family)

    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):

    user = (
        await db.execute(
            select(User).where(User.email == form_data.username)
        )
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

@router.get(
    "/me",
    response_model=UserResponse,
)
async def me(
    user: User = Depends(get_current_user),
):

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
    )