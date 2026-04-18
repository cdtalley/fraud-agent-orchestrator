"""JWT validation (OIDC JWKS) with dev bypass."""

from __future__ import annotations

from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from fraud_agent_orchestrator.settings.env import AppSettings


def decode_bearer_token(token: str, settings: AppSettings) -> dict[str, Any]:
    if not settings.oidc_jwks_url:
        raise ValueError("OIDC_JWKS_URL required when AUTH_DISABLED=false")

    jwks = PyJWKClient(settings.oidc_jwks_url)
    signing_key = jwks.get_signing_key_from_jwt(token)
    algorithms = ["RS256", "ES256"]
    kwargs: dict[str, Any] = {
        "algorithms": algorithms,
        "options": {"require": ["exp", "sub"]},
    }
    if settings.oidc_audience:
        kwargs["audience"] = settings.oidc_audience
    if settings.oidc_issuer:
        kwargs["issuer"] = settings.oidc_issuer
    return jwt.decode(token, signing_key.key, **kwargs)


async def fetch_jwks_uri_from_issuer(issuer: str) -> str | None:
    """Discover JWKS URL from OIDC issuer (optional helper)."""

    meta_url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(meta_url)
            r.raise_for_status()
            data = r.json()
            return str(data.get("jwks_uri")) if data.get("jwks_uri") else None
    except (httpx.HTTPError, ValueError, TypeError):
        return None
