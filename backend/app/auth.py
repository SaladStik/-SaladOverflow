from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    Note: bcrypt has a 72-byte limit, so we truncate if necessary
    """
    import logging

    logger = logging.getLogger(__name__)

    # Ensure password is within bcrypt's 72-byte limit
    password_bytes = password.encode("utf-8")
    original_length = len(password_bytes)

    if len(password_bytes) > 72:
        # Truncate to 72 bytes
        password = password_bytes[:72].decode("utf-8", errors="ignore")
        logger.info(f"Password truncated from {original_length} bytes to 72 bytes")
    else:
        logger.info(f"Password length: {original_length} bytes (within limit)")

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    Note: bcrypt has a 72-byte limit, so we truncate if necessary
    """
    # Ensure password is within bcrypt's 72-byte limit (same as hash_password)
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        # Truncate to 72 bytes
        plain_password = password_bytes[:72].decode("utf-8", errors="ignore")

    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str):
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract token from credentials
        token = credentials.credentials

        # Decode token
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception

        # Get user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )

    # Update last active timestamp
    user.last_active = datetime.utcnow()
    db.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current active user (additional check)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(optional_security),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Optional dependency - returns user if authenticated, None if not
    Useful for endpoints that work differently for authenticated vs anonymous users
    """
    try:
        if not credentials:
            return None

        token = credentials.credentials
        payload = verify_token(token)
        if payload is None:
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == int(user_id)).first()
        if user and user.is_active:
            # Update last active timestamp
            user.last_active = datetime.utcnow()
            db.commit()
            return user

        return None

    except Exception:
        return None
