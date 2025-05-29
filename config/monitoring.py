"""
Sistema de monitoramento e métricas.
Este módulo implementa coleta e análise de métricas do sistema.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psutil
import threading
from collections import deque
import json
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from config.logging_config import CaseLogger

logger = CaseLogger("monitoring")

class SystemMetrics:
    """Coleta métricas do sistema."""
    
    def __init__(self, history_size: int = 3600):
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        
        # Métricas Prometheus
        self.cpu_usage = Gauge('cpu_usage_percent', 'CPU usage in percent')
        self.memory_usage = Gauge('memory_usage_percent', 'Memory usage in percent')
        self.disk_usage = Gauge('disk_usage_percent', 'Disk usage in percent')
        self.network_io = Gauge('network_io_bytes', 'Network I/O in bytes')
        self.active_streams = Gauge('active_streams', 'Number of active streams')
        self.detection_latency = Histogram('detection_latency_seconds', 'Detection latency in seconds')
        self.event_count = Counter('events_total', 'Total number of events', ['event_type'])
        self.alert_count = Counter('alerts_total', 'Total number of alerts', ['alert_type'])
        
        # Iniciar servidor Prometheus
        start_http_server(8000)
        
        # Iniciar thread de coleta
        self.collection_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        self.collection_thread.start()
    
    def _collect_metrics(self) -> None:
        """Coleta métricas do sistema periodicamente."""
        while True:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_history.append((datetime.utcnow(), cpu_percent))
                self.cpu_usage.set(cpu_percent)
                
                # Memória
                memory = psutil.virtual_memory()
                self.memory_history.append((datetime.utcnow(), memory.percent))
                self.memory_usage.set(memory.percent)
                
                # Disco
                disk = psutil.disk_usage('/')
                self.disk_history.append((datetime.utcnow(), disk.percent))
                self.disk_usage.set(disk.percent)
                
                # Rede
                net_io = psutil.net_io_counters()
                self.network_history.append((
                    datetime.utcnow(),
                    net_io.bytes_sent + net_io.bytes_recv
                ))
                self.network_io.set(net_io.bytes_sent + net_io.bytes_recv)
                
            except Exception as e:
                logger.log_error("metrics_collection_error", {"error": str(e)})
            
            threading.Event().wait(60)  # Coletar a cada minuto
    
    def get_system_health(self) -> Dict[str, Any]:
        """Retorna estado de saúde do sistema."""
        try:
            return {
                "cpu": {
                    "current": psutil.cpu_percent(),
                    "history": list(self.cpu_history)
                },
                "memory": {
                    "current": psutil.virtual_memory().percent,
                    "history": list(self.memory_history)
                },
                "disk": {
                    "current": psutil.disk_usage('/').percent,
                    "history": list(self.disk_history)
                },
                "network": {
                    "current": sum(psutil.net_io_counters()[:2]),
                    "history": list(self.network_history)
                }
            }
        except Exception as e:
            logger.log_error("health_check_error", {"error": str(e)})
            return {}
    
    def record_detection(self, latency: float) -> None:
        """Registra latência de detecção."""
        self.detection_latency.observe(latency)
    
    def record_event(self, event_type: str) -> None:
        """Registra evento."""
        self.event_count.labels(event_type=event_type).inc()
    
    def record_alert(self, alert_type: str) -> None:
        """Registra alerta."""
        self.alert_count.labels(alert_type=alert_type).inc()
    
    def update_active_streams(self, count: int) -> None:
        """Atualiza contagem de streams ativos."""
        self.active_streams.set(count)

class StreamMetrics:
    """Métricas específicas para streams."""
    
    def __init__(self):
        self.frame_count = Counter('frames_processed_total', 'Total frames processed', ['stream_id'])
        self.detection_count = Counter('detections_total', 'Total detections', ['stream_id', 'class'])
        self.stream_latency = Histogram('stream_latency_seconds', 'Stream processing latency', ['stream_id'])
        self.stream_errors = Counter('stream_errors_total', 'Total stream errors', ['stream_id', 'error_type'])
    
    def record_frame(self, stream_id: str) -> None:
        """Registra frame processado."""
        self.frame_count.labels(stream_id=stream_id).inc()
    
    def record_detection(self, stream_id: str, class_name: str) -> None:
        """Registra detecção."""
        self.detection_count.labels(stream_id=stream_id, class=class_name).inc()
    
    def record_latency(self, stream_id: str, latency: float) -> None:
        """Registra latência de processamento."""
        self.stream_latency.labels(stream_id=stream_id).observe(latency)
    
    def record_error(self, stream_id: str, error_type: str) -> None:
        """Registra erro de stream."""
        self.stream_errors.labels(stream_id=stream_id, error_type=error_type).inc()

# Instâncias globais
system_metrics = SystemMetrics()
stream_metrics = StreamMetrics() 