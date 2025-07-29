import pytest
import pytest_asyncio

import httpx
from httpx import ASGITransport

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
    AsyncConnection # AsyncConnection 임포트 추가
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db, Base
from app.core.config import settings

# 1) SyncEngine 생성 및 스키마 관리 (session scope)
# 이제 AsyncEngine은 각 함수 스코프에서 생성됩니다.
@pytest_asyncio.fixture(scope="session", autouse=True)
async def database_schema_manager(): # 픽스처 이름 변경
    """
    테스트 세션 동안 데이터베이스 스키마 생성 및 삭제를 관리합니다.
    """
    SYNC_URL = (
        f"postgresql://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@postgreSQL:5432/user_test_db"
    )
    sync_engine = create_engine(SYNC_URL)

    # 스키마 생성 (sync) - 테스트 세션 시작 시 한 번만 실행
    with sync_engine.connect() as conn:
        conn.execute(text("COMMIT")) # 이전 트랜잭션이 남아있을 수 있으므로 커밋
        # 기존 스키마를 완전히 삭제하고 새로 생성하여 깨끗한 상태를 보장합니다.
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"))
        Base.metadata.create_all(bind=conn)
        conn.commit()

    yield sync_engine # sync_engine만 yield하여 스키마 정리 시 사용

    # 스키마 삭제 (sync) - 테스트 세션 종료 후 한 번만 실행
    with sync_engine.connect() as conn:
        conn.execute(text("COMMIT")) # 이전 트랜잭션이 남아있을 수 있으므로 커밋
        Base.metadata.drop_all(bind=conn)
        conn.commit()
    
    sync_engine.dispose()


# 2) Function-scoped AsyncEngine 및 AsyncSession 메이커
@pytest_asyncio.fixture(scope="function")
async def async_db_engine_and_session_maker():
    """
    각 테스트 함수에 독립적인 AsyncEngine과 AsyncSessionMaker를 제공합니다.
    """
    ASYNC_URL = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@postgreSQL:5432/user_test_db"
    )
    # 각 테스트 함수마다 새로운 AsyncEngine을 생성합니다.
    async_engine: AsyncEngine = create_async_engine(ASYNC_URL, future=True)
    
    # 이 엔진에 바인딩된 sessionmaker를 생성합니다.
    TestAsyncSessionLocal = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    
    yield async_engine, TestAsyncSessionLocal

    # 테스트 함수 종료 후 AsyncEngine을 해제합니다.
    await async_engine.dispose()


# 3) Function-scoped DB 세션 (강화된 명시적 트랜잭션 및 연결 관리)
@pytest_asyncio.fixture(scope="function")
async def db_session(async_db_engine_and_session_maker):
    """
    각 테스트 함수에 독립적인 비동기 데이터베이스 세션을 제공하고,
    테스트 종료 시 모든 변경사항을 롤백하여 깨끗한 상태를 유지합니다.
    명시적으로 연결을 얻고 트랜잭션을 관리하여 견고성을 높입니다.
    """
    async_engine, async_session_maker = async_db_engine_and_session_maker

    # AsyncSession 컨텍스트 매니저를 사용하여 세션 생명주기를 관리합니다.
    async with async_session_maker() as session:
        transaction = await session.begin()

        session.commit = session.flush

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        try:
            yield session # 테스트 함수에 세션을 제공합니다.
        finally:
            await transaction.rollback()
            await session.close()
            
            app.dependency_overrides.clear()


# 4) 비동기 TestClient (httpx.AsyncClient 사용)
@pytest_asyncio.fixture(scope="function")
async def client(db_session): # db_session 픽스처에 의존합니다.
    """
    FastAPI 애플리케이션을 테스트하기 위한 비동기 httpx 클라이언트를 제공합니다.
    앱의 lifespan 이벤트를 자동으로 처리하며, 각 테스트마다 독립적인 클라이언트를 생성합니다.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # client 픽스처의 teardown에서는 의존성 오버라이드를 다시 정리할 필요가 없습니다.
    # db_session 픽스처의 finally 블록에서 이미 모든 정리가 이루어집니다.
