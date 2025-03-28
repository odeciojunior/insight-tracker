import base64
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class ModelEncryption:
    """Handles encryption and decryption of model data."""
    
    def __init__(self):
        self._fernet = self._initialize_encryption()
        
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption using application secret key."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=settings.SECRET_KEY.encode()[:16],
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
            return Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt_model_weights(self, weights: bytes) -> bytes:
        """Encrypt model weights before storage."""
        try:
            return self._fernet.encrypt(weights)
        except Exception as e:
            logger.error(f"Failed to encrypt model weights: {e}")
            raise
    
    def decrypt_model_weights(self, encrypted_weights: bytes) -> bytes:
        """Decrypt model weights for loading."""
        try:
            return self._fernet.decrypt(encrypted_weights)
        except Exception as e:
            logger.error(f"Failed to decrypt model weights: {e}")
            raise
    
    def encrypt_model_config(self, config: Dict[str, Any]) -> str:
        """Encrypt model configuration."""
        try:
            config_bytes = str(config).encode()
            encrypted = self._fernet.encrypt(config_bytes)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt model config: {e}")
            raise
    
    def decrypt_model_config(self, encrypted_config: str) -> Dict[str, Any]:
        """Decrypt model configuration."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_config.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return eval(decrypted.decode())  # Safe since we encrypted it ourselves
        except Exception as e:
            logger.error(f"Failed to decrypt model config: {e}")
            raise

# Singleton instance
model_encryption = ModelEncryption()
