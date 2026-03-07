import hashlib
import secrets
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import ApiKey, User

TEST_DB_URL = str(settings.SQLALCHEMY_DATABASE_URI).replace(
    settings.POSTGRES_DB, f"{settings.POSTGRES_DB}_test"
)

engine_test = create_async_engine(TEST_DB_URL)


@pytest.fixture(autouse=True)
async def db_setup():
    async with engine_test.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine_test) as session:
        yield session


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.api.deps import get_db
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def superuser(session: AsyncSession) -> User:
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict[str, str]:  # noqa: ARG001
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def superuser_headers(client: AsyncClient, superuser: User) -> dict[str, str]:  # noqa: ARG001
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin@example.com", "password": "adminpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def api_key_headers(session: AsyncSession) -> dict[str, str]:
    plain_key = f"sos_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    api_key = ApiKey(
        name="test-key",
        slug="test-key",
        prefix=plain_key[:8],
        key_hash=key_hash,
        is_active=True,
    )
    session.add(api_key)
    await session.commit()
    return {"X-API-Key": plain_key}


@pytest.fixture
async def other_api_key_headers(session: AsyncSession) -> dict[str, str]:
    plain_key = f"sos_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    api_key = ApiKey(
        name="other-key",
        slug="other-key",
        prefix=plain_key[:8],
        key_hash=key_hash,
        is_active=True,
    )
    session.add(api_key)
    await session.commit()
    return {"X-API-Key": plain_key}
