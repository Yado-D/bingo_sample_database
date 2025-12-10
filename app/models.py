"""Compatibility wrapper for models.

This file re-exports the original model definitions which have been
moved to `app.models_old`. Keeping this file allows existing imports
(`from app import models`) to continue working while the project is
reorganized.
"""

from app.models_old import *

__all__ = [
    "Role",
    "User",
    "GameTransaction",
    "PackageTransaction",
    "BingoCard",
    "StoredData",
    "GameSession",
    "CreditRequest",
]
