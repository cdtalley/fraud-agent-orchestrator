"""FastAPI dependencies: DB session, actor (JWT/RBAC), role gates."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_agent_orchestrator.api.auth import decode_bearer_token
from fraud_agent_orchestrator.contracts.schemas import ActorContext
from fraud_agent_orchestrator.db.session import get_db_session
from fraud_agent_orchestrator.settings.env import get_settings

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    async for session in get_db_session():
        yield session


def _roles_from_payload(payload: dict, roles_claim: str) -> list[str]:
    raw = payload.get(roles_claim)
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return []


async def get_actor(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> ActorContext:
    settings = get_settings()
    rid = request.headers.get("x-request-id")
    tenant = request.headers.get("x-tenant-id")

    if settings.auth_disabled:
        roles = [
            r.strip()
            for r in settings.dev_default_roles.split(",")
            if r.strip()
        ]
        return ActorContext(
            sub="dev-user",
            roles=roles,
            request_id=rid,
            tenant_id=tenant,
        )

    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        payload = decode_bearer_token(creds.credentials, settings)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e!s}") from e

    roles = _roles_from_payload(payload, settings.auth_roles_claim)
    sub = str(payload.get("sub", ""))
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing sub")
    return ActorContext(
        sub=sub,
        roles=roles,
        email=payload.get("email") if isinstance(payload.get("email"), str) else None,
        request_id=rid,
        tenant_id=tenant,
    )


class RoleChecker:
    """Depends(RoleChecker('analyst', 'admin')) for RBAC."""

    def __init__(self, *allowed: str) -> None:
        self._allowed = frozenset(allowed)

    async def __call__(self, actor: ActorContext = Depends(get_actor)) -> ActorContext:
        if not self._allowed & set(actor.roles):
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {sorted(self._allowed)}",
            )
        return actor
