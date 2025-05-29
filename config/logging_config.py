"""
Sistema de logging robusto.
Este módulo implementa logging estruturado com rotação e níveis.
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from config.settings import LOGGING_CONFIG, LOGS_DIR

class CaseLogger:
    """Logger estruturado para casos de uso."""
    
    def __init__(self, case_name: str):
        self.case_name = case_name
        self.logger = logging.getLogger(case_name)
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Configura o logger com handlers e formatters."""
        # Limpar handlers existentes
        self.logger.handlers.clear()
        
        # Configurar nível
        self.logger.setLevel(logging.INFO)
        
        # Criar diretório de logs do caso
        case_log_dir = LOGS_DIR / self.case_name
        case_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOGGING_CONFIG["formatters"]["default"]["format"]))
        self.logger.addHandler(console_handler)
        
        # Handler para arquivo principal
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(case_log_dir / "app.log"),
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(LOGGING_CONFIG["formatters"]["json"]["format"]))
        self.logger.addHandler(file_handler)
        
        # Handler para erros
        error_handler = logging.handlers.RotatingFileHandler(
            filename=str(case_log_dir / "error.log"),
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(LOGGING_CONFIG["formatters"]["json"]["format"]))
        self.logger.addHandler(error_handler)
        
        # Handler para métricas
        metrics_handler = logging.handlers.RotatingFileHandler(
            filename=str(case_log_dir / "metrics.log"),
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
        metrics_handler.setFormatter(logging.Formatter(LOGGING_CONFIG["formatters"]["json"]["format"]))
        self.logger.addHandler(metrics_handler)
    
    def _format_message(self, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """Formata mensagem de log com metadados."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "case": self.case_name,
            "message": message
        }
        
        if extra:
            log_data.update(extra)
        
        return json.dumps(log_data)
    
    def log_info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registra mensagem de informação."""
        self.logger.info(self._format_message(message, extra))
    
    def log_warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registra mensagem de aviso."""
        self.logger.warning(self._format_message(message, extra))
    
    def log_error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registra mensagem de erro."""
        self.logger.error(self._format_message(message, extra))
    
    def log_debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registra mensagem de debug."""
        self.logger.debug(self._format_message(message, extra))
    
    def log_metric(self, metric_name: str, value: Any, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registra métrica."""
        metric_data = {
            "metric": metric_name,
            "value": value
        }
        if extra:
            metric_data.update(extra)
        
        self.logger.info(self._format_message("metric_recorded", metric_data))
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Registra evento."""
        event_log = {
            "event_type": event_type,
            "event_data": event_data
        }
        self.logger.info(self._format_message("event_recorded", event_log))
    
    def log_alert(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """Registra alerta."""
        alert_log = {
            "alert_type": alert_type,
            "alert_data": alert_data
        }
        self.logger.warning(self._format_message("alert_triggered", alert_log))
    
    def log_stream_event(self, stream_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Registra evento de stream."""
        stream_log = {
            "stream_id": stream_id,
            "event_type": event_type,
            "event_data": event_data
        }
        self.logger.info(self._format_message("stream_event", stream_log))
    
    def log_detection(self, stream_id: str, detection_data: Dict[str, Any]) -> None:
        """Registra detecção."""
        detection_log = {
            "stream_id": stream_id,
            "detection_data": detection_data
        }
        self.logger.info(self._format_message("detection_recorded", detection_log))
    
    def log_performance(self, operation: str, duration: float, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registra métrica de performance."""
        perf_data = {
            "operation": operation,
            "duration_ms": duration * 1000
        }
        if extra:
            perf_data.update(extra)
        
        self.logger.info(self._format_message("performance_metric", perf_data))

# Configurar logging root
logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_CONFIG["formatters"]["default"]["format"],
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            filename=str(LOGS_DIR / "root.log"),
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
    ]
) 