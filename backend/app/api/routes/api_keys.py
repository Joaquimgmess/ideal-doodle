import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import ApiKeyDep, SessionDep, get_current_active_superuser
from app.models import ApiKey, ApiKeyCreate, ApiKeyCreated, ApiKeyPublic

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _generate_key() -> tuple[str, str, str]:
    """Returns (plain_key, prefix, sha256_hash)."""
    raw = secrets.token_hex(24)
    plain_key = f"sos_{raw}"
    prefix = plain_key[:8]
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, prefix, key_hash


@router.post("", response_model=ApiKeyCreated)
async def create_api_key(session: SessionDep, key_in: ApiKeyCreate) -> ApiKeyCreated:
    plain_key, prefix, key_hash = _generate_key()
    api_key = ApiKey(
        name=key_in.name,
        description=key_in.description,
        prefix=prefix,
        key_hash=key_hash,
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return ApiKeyCreated(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        prefix=api_key.prefix,
        created_at=api_key.created_at,
        is_active=api_key.is_active,
        key=plain_key,
    )


@router.get(
    "",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[ApiKeyPublic],
)
async def list_api_keys(session: SessionDep) -> list[ApiKeyPublic]:
    keys = (await session.exec(select(ApiKey))).all()
    return keys


@router.get("/me/{prefix}", response_model=ApiKeyPublic)
async def get_my_api_key(prefix: str, api_key: ApiKeyDep) -> ApiKeyPublic:
    if api_key.prefix != prefix:
        raise HTTPException(
            status_code=403, detail="Prefix does not match authenticated key"
        )
    return api_key


@router.delete(
    "/{key_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
async def deactivate_api_key(session: SessionDep, key_id: uuid.UUID) -> dict[str, str]:
    api_key = await session.get(ApiKey, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key não encontrada")
    api_key.is_active = False
    session.add(api_key)
    await session.commit()
    return {"message": "API Key desativada"}
