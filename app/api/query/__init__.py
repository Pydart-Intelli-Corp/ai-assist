"""
Query processing API package for POORNASREE AI Platform
"""

from .query import router as query_router
from .schemas import *

__all__ = [
    "query_router"
]
