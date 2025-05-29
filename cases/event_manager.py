"""
Gerenciador de eventos para otimizar armazenamento e processamento.
Este módulo implementa estratégias para gerenciar eventos de forma eficiente.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import threading
from queue import Queue
import json
from config.logging_config import CaseLogger
from cases.database_config import (
    get_db_session, BaseEvent, BaseAlert, EventSeverity,
    TrafficEvent, TrafficAlert, SecurityEvent, SecurityAlert,
    BarEvent, BarAlert, should_store_event, compress_event_data,
    RETENTION_POLICIES
)

logger = CaseLogger("event_manager")

class EventManager:
    """Gerenciador de eventos com otimizações de armazenamento."""
    
    def __init__(self, batch_size: int = 100, flush_interval: int = 60):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.event_queue = Queue()
        self.alert_queue = Queue()
        self.batch_lock = threading.Lock()
        self.event_batches: Dict[str, List[Dict[str, Any]]] = {
            'traffic': [],
            'security': [],
            'bar': []
        }
        self.alert_batches: Dict[str, List[Dict[str, Any]]] = {
            'traffic': [],
            'security': [],
            'bar': []
        }
        
        # Iniciar thread de processamento em lote
        self.processing_thread = threading.Thread(target=self._process_batches, daemon=True)
        self.processing_thread.start()
    
    def add_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Adiciona um evento à fila de processamento."""
        # Comprimir dados do evento
        compressed_data = compress_event_data(event_data)
        
        # Verificar se o evento deve ser armazenado
        severity = EventSeverity(event_data.get('severity', 'low'))
        if should_store_event(event_type, severity, compressed_data):
            with self.batch_lock:
                self.event_batches[event_type].append(compressed_data)
                
                # Verificar se atingiu o tamanho do lote
                if len(self.event_batches[event_type]) >= self.batch_size:
                    self._flush_events(event_type)
    
    def add_alert(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """Adiciona um alerta à fila de processamento."""
        with self.batch_lock:
            self.alert_batches[alert_type].append(alert_data)
            
            # Verificar se atingiu o tamanho do lote
            if len(self.alert_batches[alert_type]) >= self.batch_size:
                self._flush_alerts(alert_type)
    
    def _process_batches(self) -> None:
        """Processa lotes de eventos e alertas periodicamente."""
        while True:
            # Aguardar intervalo de flush
            threading.Event().wait(self.flush_interval)
            
            # Flush de eventos
            with self.batch_lock:
                for event_type in self.event_batches:
                    if self.event_batches[event_type]:
                        self._flush_events(event_type)
                
                # Flush de alertas
                for alert_type in self.alert_batches:
                    if self.alert_batches[alert_type]:
                        self._flush_alerts(alert_type)
    
    def _flush_events(self, event_type: str) -> None:
        """Salva lote de eventos no banco de dados."""
        if not self.event_batches[event_type]:
            return
        
        session = get_db_session()
        try:
            # Mapear tipo de evento para classe do modelo
            event_class = {
                'traffic': TrafficEvent,
                'security': SecurityEvent,
                'bar': BarEvent
            }.get(event_type)
            
            if not event_class:
                logger.log_error("invalid_event_type", {"event_type": event_type})
                return
            
            # Criar objetos de evento
            events = []
            for event_data in self.event_batches[event_type]:
                try:
                    event = event_class(**event_data)
                    events.append(event)
                except Exception as e:
                    logger.log_error("event_creation_error", {
                        "error": str(e),
                        "event_data": event_data
                    })
            
            # Salvar em lote
            if events:
                session.bulk_save_objects(events)
                session.commit()
                logger.log_metric(f"{event_type}_events_saved", len(events))
            
            # Limpar lote
            self.event_batches[event_type] = []
            
        except Exception as e:
            session.rollback()
            logger.log_error("event_flush_error", {
                "error": str(e),
                "event_type": event_type
            })
        finally:
            session.close()
    
    def _flush_alerts(self, alert_type: str) -> None:
        """Salva lote de alertas no banco de dados."""
        if not self.alert_batches[alert_type]:
            return
        
        session = get_db_session()
        try:
            # Mapear tipo de alerta para classe do modelo
            alert_class = {
                'traffic': TrafficAlert,
                'security': SecurityAlert,
                'bar': BarAlert
            }.get(alert_type)
            
            if not alert_class:
                logger.log_error("invalid_alert_type", {"alert_type": alert_type})
                return
            
            # Criar objetos de alerta
            alerts = []
            for alert_data in self.alert_batches[alert_type]:
                try:
                    alert = alert_class(**alert_data)
                    alerts.append(alert)
                except Exception as e:
                    logger.log_error("alert_creation_error", {
                        "error": str(e),
                        "alert_data": alert_data
                    })
            
            # Salvar em lote
            if alerts:
                session.bulk_save_objects(alerts)
                session.commit()
                logger.log_metric(f"{alert_type}_alerts_saved", len(alerts))
            
            # Limpar lote
            self.alert_batches[alert_type] = []
            
        except Exception as e:
            session.rollback()
            logger.log_error("alert_flush_error", {
                "error": str(e),
                "alert_type": alert_type
            })
        finally:
            session.close()
    
    def cleanup_old_data(self) -> None:
        """Limpa dados antigos baseado nas políticas de retenção."""
        session = get_db_session()
        try:
            current_time = datetime.utcnow()
            
            # Limpar eventos antigos
            for event_type, policies in RETENTION_POLICIES.items():
                for severity, days in policies.items():
                    cutoff_date = current_time - timedelta(days=days)
                    
                    # Mapear tipo de evento para classe do modelo
                    event_class = {
                        'traffic_events': TrafficEvent,
                        'security_events': SecurityEvent,
                        'bar_events': BarEvent
                    }.get(event_type)
                    
                    if event_class:
                        # Deletar eventos antigos
                        deleted = session.query(event_class).filter(
                            event_class.timestamp < cutoff_date,
                            event_class.severity == severity
                        ).delete()
                        
                        logger.log_metric(f"{event_type}_cleaned", deleted)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.log_error("cleanup_error", {"error": str(e)})
        finally:
            session.close()
    
    def get_recent_events(self,
                         event_type: str,
                         stream_id: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Recupera eventos recentes com filtros."""
        session = get_db_session()
        try:
            # Mapear tipo de evento para classe do modelo
            event_class = {
                'traffic': TrafficEvent,
                'security': SecurityEvent,
                'bar': BarEvent
            }.get(event_type)
            
            if not event_class:
                return []
            
            # Construir query
            query = session.query(event_class)
            
            if stream_id:
                query = query.filter(event_class.stream_id == stream_id)
            
            if start_time:
                query = query.filter(event_class.timestamp >= start_time)
            
            if end_time:
                query = query.filter(event_class.timestamp <= end_time)
            
            # Ordenar e limitar
            events = query.order_by(event_class.timestamp.desc()).limit(limit).all()
            
            # Converter para dicionário
            return [event.__dict__ for event in events]
            
        finally:
            session.close()
    
    def get_active_alerts(self,
                         alert_type: str,
                         severity: Optional[EventSeverity] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Recupera alertas ativos com filtros."""
        session = get_db_session()
        try:
            # Mapear tipo de alerta para classe do modelo
            alert_class = {
                'traffic': TrafficAlert,
                'security': SecurityAlert,
                'bar': BarAlert
            }.get(alert_type)
            
            if not alert_class:
                return []
            
            # Construir query
            query = session.query(alert_class).filter(alert_class.resolved == False)
            
            if severity:
                query = query.filter(alert_class.severity == severity)
            
            # Ordenar e limitar
            alerts = query.order_by(alert_class.timestamp.desc()).limit(limit).all()
            
            # Converter para dicionário
            return [alert.__dict__ for alert in alerts]
            
        finally:
            session.close()

# Instância global do gerenciador de eventos
event_manager = EventManager() 