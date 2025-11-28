from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import secrets
from app.database import get_db
from app.models.user import User
from app.config import settings
from app.auth import create_access_token
from datetime import datetime

router = APIRouter(prefix="/api/v1/auth/github", tags=["GitHub OAuth"])

# In-memory store for OAuth state (in production, use Redis)
oauth_states = {}


@router.get("/login")
async def github_login():
    """
    Redirect user to GitHub OAuth authorization page
    """
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"created_at": datetime.utcnow()}

    # Build GitHub OAuth URL
    github_oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=user:email"
        f"&state={state}"
    )

    return RedirectResponse(github_oauth_url)


@router.get("/callback")
async def github_callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Handle GitHub OAuth callback
    """
    # Verify state to prevent CSRF
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter"
        )

    # Clean up state
    del oauth_states[state]

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from GitHub",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from GitHub",
            )

        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from GitHub",
            )

        github_user = user_response.json()

        # Get user's email (might be private)
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        emails = email_response.json() if email_response.status_code == 200 else []
        primary_email = next(
            (e["email"] for e in emails if e["primary"] and e["verified"]),
            github_user.get("email"),
        )

        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email found in GitHub account. Please make your email public or verify it.",
            )

    # Check if user exists by GitHub ID (most reliable)
    github_username = github_user["login"]
    github_id = str(github_user["id"])

    # First, try to find user by GitHub ID (already linked account)
    user = db.query(User).filter(User.github_id == github_id).first()

    if user:
        # User already linked their GitHub account, log them in
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
            )

        # Update username/avatar if changed on GitHub
        if user.github_username != github_username:
            user.github_username = github_username
        if not user.avatar_url and github_user.get("avatar_url"):
            user.avatar_url = github_user["avatar_url"]
        db.commit()
    else:
        # No GitHub ID match - check if email exists (account linking scenario)
        existing_user = db.query(User).filter(User.email == primary_email).first()

        if existing_user:
            # Email exists but not linked to GitHub yet
            # Link this GitHub account to the existing user
            if existing_user.github_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is already associated with a different GitHub account",
                )

            if not existing_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
                )

            # Link GitHub to existing account
            existing_user.github_id = github_id
            existing_user.github_username = github_username
            if not existing_user.avatar_url and github_user.get("avatar_url"):
                existing_user.avatar_url = github_user["avatar_url"]
            db.commit()
            user = existing_user
        else:
            # Check if GitHub username is already taken
            username_taken = (
                db.query(User).filter(User.username == github_username).first()
            )
            if username_taken:
                # Generate unique username by adding random suffix
                import random

                random_suffix = random.randint(1000, 9999)
                github_username = f"{github_username}{random_suffix}"

            # Create new user from GitHub data
            user = User(
                username=github_username,
                email=primary_email,
                display_name=github_user.get("name") or github_username,
                bio=github_user.get("bio") or "",
                github_id=github_id,
                github_username=github_username,
                avatar_url=github_user.get("avatar_url"),
                is_verified=True,  # GitHub email is verified
                password_hash=None,  # No password for OAuth users
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    # Create JWT token
    jwt_token = create_access_token(data={"sub": str(user.id)})

    # Redirect to frontend with token
    redirect_url = f"{settings.frontend_url}/auth/github/success?token={jwt_token}"
    return RedirectResponse(redirect_url)
