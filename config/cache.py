"""
Sistema de cache para otimização de performance.
Este módulo implementa cache em memória para melhorar performance.
"""

import threading
import weakref
import psutil
from typing import Dict, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from config.settings import CACHE_CONFIG
from config.logging_config import CaseLogger

logger = CaseLogger("cache")

class Singleton:
    """Implementa padrão Singleton com thread-safety."""
    
    _instances = weakref.WeakValueDictionary()
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__new__(cls)
                    cls._instances[cls] = instance
        return cls._instances[cls]

class CacheManager(Singleton):
    """Gerenciador de cache em memória com controle de recursos."""
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.memory_cache: Dict[str, Dict[str, Any]] = {}
            self.memory_lock = threading.Lock()
            self.last_cleanup = datetime.utcnow()
            self.initialized = True
    
    def _get_memory_usage(self) -> float:
        """Obtém uso de memória em MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _check_memory_limit(self) -> bool:
        """Verifica se uso de memória está dentro do limite."""
        try:
            memory_usage = self._get_memory_usage()
            memory_limit = CACHE_CONFIG.get("memory_limit_mb", 1024)  # 1GB default
            return memory_usage < memory_limit
        except Exception as e:
            logger.log_error("memory_check_error", {"error": str(e)})
            return False
    
    def _generate_key(self, key: Union[str, Dict[str, Any]]) -> str:
        """Gera chave de cache."""
        if isinstance(key, dict):
            key_str = str(sorted(key.items()))
        else:
            key_str = str(key)
        return key_str
    
    def _cleanup_if_needed(self) -> None:
        """Limpa cache se necessário."""
        current_time = datetime.utcnow()
        if (current_time - self.last_cleanup).total_seconds() > CACHE_CONFIG.get("cleanup_interval", 300):
            self.cleanup_expired()
            self.last_cleanup = current_time
    
    def get(self, key: Union[str, Dict[str, Any]], default: Any = None) -> Any:
        """Obtém valor do cache."""
        try:
            cache_key = self._generate_key(key)
            
            with self.memory_lock:
                if cache_key in self.memory_cache:
                    cache_data = self.memory_cache[cache_key]
                    if datetime.utcnow() < cache_data["expires_at"]:
                        return cache_data["value"]
                    else:
                        del self.memory_cache[cache_key]
            
            return default
        
        except Exception as e:
            logger.log_error("cache_get_error", {"error": str(e)})
            return default
    
    def set(self, key: Union[str, Dict[str, Any]], value: Any, ttl: int = None) -> bool:
        """Armazena valor no cache com verificação de memória."""
        try:
            if ttl is None:
                ttl = CACHE_CONFIG["default_ttl"]
            
            # Verificar limite de memória
            if not self._check_memory_limit():
                logger.log_warning("memory_limit_reached")
                self.cleanup_expired()
                if not self._check_memory_limit():
                    return False
            
            cache_key = self._generate_key(key)
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            cache_data = {
                "value": value,
                "expires_at": expires_at,
                "size": len(str(value))  # Estimativa grosseira de tamanho
            }
            
            with self.memory_lock:
                # Verificar limite de tamanho do cache
                if len(self.memory_cache) >= CACHE_CONFIG["memory_cache_size"]:
                    # Remover item mais antigo
                    oldest_key = min(self.memory_cache.items(), 
                                   key=lambda x: x[1]["expires_at"])[0]
                    del self.memory_cache[oldest_key]
                
                self.memory_cache[cache_key] = cache_data
                self._cleanup_if_needed()
            
            return True
        
        except Exception as e:
            logger.log_error("cache_set_error", {"error": str(e)})
            return False
    
    def delete(self, key: Union[str, Dict[str, Any]]) -> bool:
        """Remove valor do cache."""
        try:
            cache_key = self._generate_key(key)
            with self.memory_lock:
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
                    return True
            return False
        
        except Exception as e:
            logger.log_error("cache_delete_error", {"error": str(e)})
            return False
    
    def clear(self) -> None:
        """Limpa cache."""
        try:
            with self.memory_lock:
                self.memory_cache.clear()
        
        except Exception as e:
            logger.log_error("cache_clear_error", {"error": str(e)})
    
    def cleanup_expired(self) -> None:
        """Remove itens expirados do cache."""
        try:
            current_time = datetime.utcnow()
            with self.memory_lock:
                expired_keys = [
                    key for key, data in self.memory_cache.items()
                    if current_time >= data["expires_at"]
                ]
                for key in expired_keys:
                    del self.memory_cache[key]
        
        except Exception as e:
            logger.log_error("cache_cleanup_error", {"error": str(e)})

def cached(ttl: int = None, max_size: int = None):
    """Decorator para cache de funções com controle de recursos."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Gerar chave de cache
                cache_key = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                # Verificar tamanho máximo
                if max_size is not None:
                    key_size = len(str(cache_key))
                    if key_size > max_size:
                        logger.log_warning("cache_key_too_large", {
                            "func": func.__name__,
                            "size": key_size
                        })
                        return func(*args, **kwargs)
                
                # Tentar obter do cache
                cache_manager = CacheManager()
                cached_value = cache_manager.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Executar função
                result = func(*args, **kwargs)
                
                # Armazenar no cache
                if cache_manager.set(cache_key, result, ttl):
                    return result
                else:
                    logger.log_warning("cache_set_failed", {"func": func.__name__})
                    return result
            
            except Exception as e:
                logger.log_error("cache_decorator_error", {
                    "func": func.__name__,
                    "error": str(e)
                })
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Instância global do gerenciador de cache
cache_manager = CacheManager() 