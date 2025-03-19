import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.session import get_db
from app.main import app

# Define test database URL - use SQLite in memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Set up test environment variables
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture que cria um loop de eventos para testes assíncronos.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Cria uma sessão de banco de dados para testes.
    
    Retorna:
        Uma sessão de banco de dados para testes.
    """
    # Create async engine for tests
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
    )
    
    # Create tables for each test
    async with engine.begin() as conn:
        from app.db.base import Base  # Import here to avoid circular imports
        
        await conn.run_sync(Base.metadata.create_all)
    
    # Create and yield a session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    
    async with async_session() as session:
        yield session
    
    # Clean up after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def app_with_test_db(db_session) -> FastAPI:
    """
    Cria uma instância da aplicação FastAPI com uma sessão de banco de dados de teste.
    
    Args:
        db_session: Uma sessão de banco de dados de teste.
    
    Retorna:
        Uma instância da aplicação FastAPI.
    """
    # Override the get_db dependency
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()
    
    # Replace the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest_asyncio.fixture
async def client(app_with_test_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Cria um cliente HTTP assíncrono para testes.
    
    Args:
        app_with_test_db: Uma instância da aplicação FastAPI.
    
    Retorna:
        Um cliente HTTP assíncrono.
    """
    async with AsyncClient(
        app=app_with_test_db, base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(scope="function")
def setup_and_teardown_db():
    """
    Configura e limpa o banco de dados antes e depois dos testes.
    
    Este fixture é útil para testes que não usam o db_session diretamente,
    mas precisam garantir que o banco de dados esteja limpo.
    """
    # Setup - create database and tables
    engine = create_engine(str(settings.DATABASE_URL).replace("+asyncpg", ""))
    from app.db.base import Base  # Import here to avoid circular imports
    
    Base.metadata.create_all(engine)
    
    yield  # Run the test
    
    # Teardown - drop all tables
    Base.metadata.drop_all(engine)
