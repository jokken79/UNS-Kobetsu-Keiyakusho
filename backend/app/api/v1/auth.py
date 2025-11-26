"""
Authentication API endpoints.
Handles login, token refresh, and user management.
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    Token,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
    get_current_user,
)
from app.core.config import settings

router = APIRouter()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request body."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str


# In-memory user store for demo (replace with database in production)
# This is a simplified implementation - in production use proper User model
_demo_users = {
    "admin@example.com": {
        "id": 1,
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrD5K",  # pre-hashed "admin123"
        "role": "admin",
        "is_active": True,
    }
}


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns access and refresh tokens on successful authentication.
    """
    # Check if user exists (demo implementation)
    user = _demo_users.get(request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    # Create tokens
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access and refresh tokens.
    """
    # Verify refresh token
    token_data = verify_token(request.refresh_token, token_type="refresh")

    # Create new tokens
    new_token_data = {
        "sub": token_data.user_id,
        "email": token_data.email,
        "role": token_data.role,
    }

    access_token = create_access_token(new_token_data)
    refresh_token = create_refresh_token(new_token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's information.

    Requires valid JWT access token in Authorization header.
    """
    # Get full user data (demo implementation)
    user = _demo_users.get(current_user["email"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **email**: User's email address (must be unique)
    - **password**: User's password (min 8 characters)
    - **full_name**: User's full name
    - **role**: User role (default: "user")

    Note: In production, this endpoint should be admin-only or have email verification.
    """
    # Check if user already exists
    if request.email in _demo_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    # Create user (demo implementation)
    new_id = len(_demo_users) + 1
    _demo_users[request.email] = {
        "id": new_id,
        "email": request.email,
        "full_name": request.full_name,
        "hashed_password": get_password_hash(request.password),
        "role": request.role,
        "is_active": True,
    }

    return UserResponse(
        id=new_id,
        email=request.email,
        full_name=request.full_name,
        role=request.role,
        is_active=True,
    )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Change current user's password.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 characters)
    """
    # Get user (demo implementation)
    user = _demo_users.get(current_user["email"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(request.current_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    # Update password
    user["hashed_password"] = get_password_hash(request.new_password)

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.

    In a production system, this would invalidate the token
    (e.g., add to a blacklist in Redis).
    """
    # In production, you would:
    # 1. Add the token to a blacklist in Redis
    # 2. Clear any server-side session data

    return {"message": "Successfully logged out"}
