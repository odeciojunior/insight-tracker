from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings

# Contexto de criptografia para senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT para autenticação.
    
    Args:
        subject: Identificador do usuário, geralmente o ID ou e-mail.
        expires_delta: Tempo de expiração do token. Se None, usa o padrão da configuração.
        
    Returns:
        Token JWT codificado.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde à senha com hash.
    
    Args:
        plain_password: Senha em texto plano.
        hashed_password: Senha com hash armazenada no banco de dados.
        
    Returns:
        True se a senha corresponder, False caso contrário.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera um hash da senha usando bcrypt.
    
    Args:
        password: Senha em texto plano.
        
    Returns:
        Hash da senha.
    """
    return pwd_context.hash(password)
