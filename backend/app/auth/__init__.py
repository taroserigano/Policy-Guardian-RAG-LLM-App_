"""
Authentication module for Policy RAG application.
Provides JWT-based authentication with user management.
"""
from app.auth.models import User
from app.auth.utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.dependencies import get_current_user, get_current_active_user

__all__ = [
    "User",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "get_current_active_user",
]
