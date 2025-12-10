from typing import Callable, List

from fastapi import Request, HTTPException, status, Depends
from jose import JWTError, jwt

from app.core.config import settings


async def verifyToken(request: Request):
    """Dependency that verifies a Bearer JWT from the Authorization header.

    On success the decoded token payload is attached as:
      - `request.state.user` (recommended FastAPI pattern)
      - `request.user` (convenience to match `req.user` style)

    Raises 401 if the token is missing or invalid.
    Returns the decoded payload for further use if needed.
    """
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Accept either 'Bearer <token>' or the raw token string
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
    else:
        token = auth.strip()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Attach user payload to request (both state and attribute)
    request.state.user = payload
    try:
        # also set attribute for `req.user` style access
        setattr(request, "user", payload)
    except Exception:
        # ignore if setting attribute is not allowed for some reason
        pass

    return payload


def authorizeRoles(*allowed_roles: List[str]) -> Callable:
    """Factory that returns a dependency to enforce allowed roles.

    Usage in a path operation:
      - as a dependency param: `Depends(authorizeRoles("owner", "manager"))`
      - or in `dependencies=[Depends(verifyToken), Depends(authorizeRoles("owner"))]`

    If `request.state.user` (or `request.user`) is missing or the user's role
    is not in `allowed_roles`, a 403 Forbidden is raised.
    """

    async def _authorize(request: Request = Depends(verifyToken)):
        # `verifyToken` will already have attached the payload to request
        user_payload = getattr(request, "user", None) or getattr(request.state, "user", None)
        if not user_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        # role may be present as a string in the payload
        role = None
        if isinstance(user_payload, dict):
            role = user_payload.get("role")
        else:
            # fall back if a custom object was attached
            role = getattr(user_payload, "role", None)

        if role is None or role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return True

    return _authorize
