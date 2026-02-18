from cryptography.fernet import Fernet, InvalidToken

from common.app_logger import AppLogger

logger = AppLogger(__name__)


class TokenEncryptor:
    """Fernet-based encrypt/decrypt for refresh tokens at rest.

    The key must be a URL-safe base64-encoded 32-byte key.
    Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """

    def __init__(self, key: str):
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt token — key may have rotated")
            raise ValueError("Cannot decrypt refresh token")
