"""Compatibility wrapper for schemas.

The original schemas were moved to `app.schemas_old`. This file
re-exports them so existing imports continue to work during the
reorganization.
"""

from app.schemas_old import *

__all__ = [name for name in dir() if not name.startswith("_")]
