from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Criar engine assíncrona para conexão com o banco de dados
engine = create_async_engine(
    str(settings.DATABASE_URL), 
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Session factory para criar sessões de banco de dados
SessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência para obter uma sessão de banco de dados.
    
    Deve ser utilizada como uma dependência FastAPI para garantir
    que a sessão seja fechada corretamente após o uso.
    
    Yields:
        AsyncSession: Sessão de banco de dados.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
