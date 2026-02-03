from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

# 加密密钥生成
def get_encryption_key():
    """获取或生成加密密钥"""
    key = os.getenv("ENCRYPT_KEY")
    if key:
        # 如果是环境变量中的密钥，需要确保是有效的Fernet密钥
        try:
            return base64.urlsafe_b64decode(key)
        except Exception:
            pass
    
    # 从密钥派生
    password = "llmgateway-secret-key".encode()
    salt = b'llmgateway-salt-2024'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

# 初始化Fernet
_fernet = None

def get_fernet():
    global _fernet
    if _fernet is None:
        _fernet = Fernet(get_encryption_key())
    return _fernet

def encrypt_api_key(api_key: str) -> str:
    """加密API Key"""
    f = get_fernet()
    encrypted = f.encrypt(api_key.encode())
    return encrypted.decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """解密API Key"""
    f = get_fernet()
    decrypted = f.decrypt(encrypted_key.encode())
    return decrypted.decode()

def generate_new_key() -> str:
    """生成新的加密密钥（用于密钥轮换）"""
    return Fernet.generate_key().decode()
