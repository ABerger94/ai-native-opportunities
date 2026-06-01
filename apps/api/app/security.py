from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, Query
from jwt import PyJWKClient

from app.config import get_settings


@lru_cache
def _jwks_client() -> PyJWKClient | None:
    settings = get_settings()
    if not settings.clerk_jwks_url:
        return None
    return PyJWKClient(str(settings.clerk_jwks_url))


def get_current_user_id(
    authorization: str | None = Header(default=None),
    local_user_id: str | None = Query(default=None),
) -> str:
    settings = get_settings()
    client = _jwks_client()
    if local_user_id and not authorization:
        return local_user_id
    if client is None:
        if local_user_id:
            return local_user_id
        raise HTTPException(
            status_code=401,
            detail="Authentication is not configured. Provide local_user_id only in local development.",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization.split(" ", 1)[1]
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token.") from exc
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Token did not include a subject.")
    return str(subject)


CurrentUserId = Depends(get_current_user_id)
