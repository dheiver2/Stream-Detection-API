"""
Configurações de segurança e autenticação.
Este módulo implementa medidas de segurança para a API.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import OAuth2PasswordBearer
from config.settings import SECURITY_CONFIG
import hashlib
import secrets

# Configurações de segurança
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class SecurityManager:
    """Gerenciador de segurança e autenticação."""
    
    def __init__(self):
        self.secret_key = SECURITY_CONFIG["secret_key"]
        self.algorithm = SECURITY_CONFIG["algorithm"]
        self.access_token_expire_minutes = SECURITY_CONFIG["access_token_expire_minutes"]
        self.rate_limit = SECURITY_CONFIG["rate_limit"]
        self._rate_limit_cache: Dict[str, Dict[str, Any]] = {}
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Gera hash da senha."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Cria token de acesso JWT."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica token JWT."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Verifica limite de requisições por cliente."""
        if not self.rate_limit["enabled"]:
            return True
        
        current_time = datetime.utcnow()
        client_data = self._rate_limit_cache.get(client_id, {
            "count": 0,
            "window_start": current_time
        })
        
        # Resetar contador se a janela de tempo expirou
        if (current_time - client_data["window_start"]) > timedelta(minutes=1):
            client_data = {
                "count": 0,
                "window_start": current_time
            }
        
        # Verificar limite
        if client_data["count"] >= self.rate_limit["requests_per_minute"]:
            return False
        
        # Atualizar contador
        client_data["count"] += 1
        self._rate_limit_cache[client_id] = client_data
        return True
    
    def generate_api_key(self) -> str:
        """Gera uma nova chave de API."""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Gera hash da chave de API."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verifica se a chave de API é válida."""
        return self.hash_api_key(api_key) == hashed_key

# Instância global do gerenciador de segurança
security_manager = SecurityManager()

# Dependências para autenticação
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Obtém o usuário atual a partir do token."""
    return security_manager.verify_token(token)

async def verify_api_key(api_key: str = Security(oauth2_scheme)) -> bool:
    """Verifica a chave de API."""
    # Implementar verificação da chave de API no banco de dados
    return True 