"""
Authentication API package for POORNASREE AI Platform
"""

from .auth import router as auth_router
from .schemas import *

__all__ = [
    "auth_router"
]
