import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """
    Testa se o endpoint de health check está funcionando corretamente.
    
    Deve retornar status 200 e um objeto JSON com status "healthy".
    """
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """
    Testa se o endpoint raiz está funcionando corretamente.
    
    Deve retornar status 200 e uma mensagem de boas-vindas.
    """
    response = await client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Bem-vindo" in response.json()["message"]
