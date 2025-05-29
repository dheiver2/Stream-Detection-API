"""
Configurações centralizadas do sistema.
Este módulo define todas as configurações do sistema.
"""

import os
from typing import Dict, Any
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"

# Criar diretórios necessários
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configurações da API
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "8000")),
    "debug": os.getenv("API_DEBUG", "False").lower() == "true",
    "workers": int(os.getenv("API_WORKERS", "4")),
    "timeout": int(os.getenv("API_TIMEOUT", "60")),
    "max_requests": int(os.getenv("API_MAX_REQUESTS", "1000")),
    "max_requests_jitter": int(os.getenv("API_MAX_REQUESTS_JITTER", "50")),
    "keep_alive": int(os.getenv("API_KEEP_ALIVE", "5")),
    "graceful_timeout": int(os.getenv("API_GRACEFUL_TIMEOUT", "120")),
}

# Configurações de segurança
SECURITY_CONFIG = {
    "secret_key": os.getenv("SECRET_KEY", "your-secret-key-here"),
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "rate_limit": {
        "enabled": True,
        "requests_per_minute": 60,
        "burst": 10
    },
    "allowed_hosts": os.getenv("ALLOWED_HOSTS", "*").split(","),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
    "ssl_enabled": os.getenv("SSL_ENABLED", "False").lower() == "true",
    "ssl_cert": os.getenv("SSL_CERT", ""),
    "ssl_key": os.getenv("SSL_KEY", ""),
}

# Configurações de armazenamento
STORAGE_CONFIG = {
    "data_dir": str(DATA_DIR),
    "events_dir": str(DATA_DIR / "events"),
    "alerts_dir": str(DATA_DIR / "alerts"),
    "metrics_dir": str(DATA_DIR / "metrics"),
    "retention_days": int(os.getenv("DATA_RETENTION_DAYS", "30")),
    "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "100")),
    "compression_enabled": os.getenv("COMPRESSION_ENABLED", "False").lower() == "true",
    "min_disk_space_mb": int(os.getenv("MIN_DISK_SPACE_MB", "1024")),  # 1GB mínimo
    "backup_enabled": os.getenv("BACKUP_ENABLED", "True").lower() == "true",
    "backup_interval_hours": int(os.getenv("BACKUP_INTERVAL_HOURS", "24")),
    "backup_retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", "7")),
    "validate_data": os.getenv("VALIDATE_DATA", "True").lower() == "true",
    "max_concurrent_writes": int(os.getenv("MAX_CONCURRENT_WRITES", "10")),
}

# Configurações de cache
CACHE_CONFIG = {
    "memory_cache_size": int(os.getenv("MEMORY_CACHE_SIZE", "1000")),
    "default_ttl": int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
    "memory_limit_mb": int(os.getenv("CACHE_MEMORY_LIMIT_MB", "1024")),  # 1GB limite
    "cleanup_interval": int(os.getenv("CACHE_CLEANUP_INTERVAL", "300")),  # 5 minutos
    "max_key_size": int(os.getenv("CACHE_MAX_KEY_SIZE", "1024")),  # 1KB
    "max_value_size": int(os.getenv("CACHE_MAX_VALUE_SIZE", "1048576")),  # 1MB
    "compression_threshold": int(os.getenv("CACHE_COMPRESSION_THRESHOLD", "1024")),  # 1KB
    "compression_level": int(os.getenv("CACHE_COMPRESSION_LEVEL", "6")),
    "enable_metrics": os.getenv("CACHE_ENABLE_METRICS", "True").lower() == "true",
    "metrics_interval": int(os.getenv("CACHE_METRICS_INTERVAL", "60")),  # 1 minuto
}

# Configurações de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": str(LOGS_DIR / "app.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "INFO"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}

# Configurações de streams
STREAM_CONFIG = {
    "default_buffer_size": int(os.getenv("STREAM_BUFFER_SIZE", "30")),
    "max_retries": int(os.getenv("STREAM_MAX_RETRIES", "3")),
    "retry_delay": int(os.getenv("STREAM_RETRY_DELAY", "5")),
    "timeout": int(os.getenv("STREAM_TIMEOUT", "30")),
    "max_streams": int(os.getenv("MAX_STREAMS", "10")),
    "frame_skip": int(os.getenv("FRAME_SKIP", "2")),
    "save_frames": os.getenv("SAVE_FRAMES", "False").lower() == "true",
    "frames_dir": str(DATA_DIR / "frames"),
}

# Configurações de modelos
MODEL_CONFIG = {
    "default_model": os.getenv("DEFAULT_MODEL", "yolov8n.pt"),
    "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
    "iou_threshold": float(os.getenv("IOU_THRESHOLD", "0.45")),
    "device": os.getenv("MODEL_DEVICE", "cpu"),
    "batch_size": int(os.getenv("MODEL_BATCH_SIZE", "1")),
    "models_dir": str(MODELS_DIR),
    "model_cache_size": int(os.getenv("MODEL_CACHE_SIZE", "2")),
}

# Configurações de casos de uso
CASE_CONFIG = {
    "traffic": {
        "enabled": True,
        "min_confidence": 0.6,
        "track_objects": True,
        "save_violations": True,
        "violation_types": ["speed", "red_light", "wrong_way"],
        "metrics_interval": 300,  # 5 minutos
    },
    "security": {
        "enabled": True,
        "min_confidence": 0.7,
        "track_objects": True,
        "save_events": True,
        "alert_types": ["unauthorized_access", "suspicious_activity"],
        "metrics_interval": 300,
    },
    "bar": {
        "enabled": True,
        "min_confidence": 0.6,
        "track_objects": True,
        "save_events": True,
        "alert_types": ["crowding", "aggression", "intoxication"],
        "metrics_interval": 300,
    }
}

# Configurações de exportação
EXPORT_CONFIG = {
    "enabled": True,
    "formats": ["json", "csv", "excel"],
    "export_dir": str(DATA_DIR / "exports"),
    "max_exports": int(os.getenv("MAX_EXPORTS", "100")),
    "export_retention_days": int(os.getenv("EXPORT_RETENTION_DAYS", "30")),
}

# Configurações de monitoramento
MONITORING_CONFIG = {
    "enabled": True,
    "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),
    "metrics_interval": int(os.getenv("METRICS_INTERVAL", "60")),
    "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "300")),
    "alert_thresholds": {
        "cpu_percent": 80,
        "memory_percent": 80,
        "disk_percent": 90,
        "error_rate": 0.01,
    }
}

def get_case_config(case_type: str) -> Dict[str, Any]:
    """Obtém configurações específicas para um caso de uso."""
    return CASE_CONFIG.get(case_type, {}) 