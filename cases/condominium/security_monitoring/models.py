"""
Modelos de banco de dados para monitoramento de segurança em condomínios.
Este módulo contém as definições das tabelas específicas para eventos de segurança.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from cases.database_config import Base, BaseEvent, BaseAlert

class AccessType(enum.Enum):
    ENTRY = "entry"
    EXIT = "exit"
    UNAUTHORIZED = "unauthorized"

class SecurityEvent(BaseEvent):
    """Eventos de segurança."""
    __tablename__ = "security_events"
    
    access_type = Column(String)  # Tipo de acesso (entrada, saída, não autorizado)
    person_count = Column(Integer)  # Número de pessoas detectadas
    vehicle_type = Column(String, nullable=True)  # Tipo de veículo, se aplicável
    area = Column(String)  # Área do condomínio
    authorized = Column(Boolean)  # Se o acesso foi autorizado
    access_point = Column(String)  # Ponto de acesso (portaria, garagem, etc.)
    
    def __repr__(self):
        return f"<SecurityEvent(type={self.event_type}, access_type={self.access_type}, timestamp={self.timestamp})>"

class SecurityAlert(BaseAlert):
    """Alertas de segurança."""
    __tablename__ = "security_alerts"
    
    alert_category = Column(String)  # Categoria do alerta (intrusão, aglomeração, etc.)
    affected_area = Column(String)  # Área afetada
    person_count = Column(Integer, nullable=True)  # Número de pessoas envolvidas
    duration = Column(Float, nullable=True)  # Duração do evento em segundos
    action_taken = Column(String, nullable=True)  # Ação tomada
    security_notified = Column(Boolean, default=False)  # Se a segurança foi notificada
    
    def __repr__(self):
        return f"<SecurityAlert(type={self.alert_type}, category={self.alert_category}, timestamp={self.timestamp})>"

class AccessLog(Base):
    """Registro de acessos ao condomínio."""
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    access_type = Column(String)
    person_id = Column(String, nullable=True)  # ID da pessoa (se identificada)
    vehicle_plate = Column(String, nullable=True)  # Placa do veículo
    access_point = Column(String)
    authorized = Column(Boolean)
    authorization_method = Column(String, nullable=True)  # Método de autorização (biometria, cartão, etc.)
    visitor_info = Column(JSON, nullable=True)  # Informações do visitante
    image_path = Column(String, nullable=True)  # Caminho para a imagem do acesso
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "access_type": self.access_type,
            "person_id": self.person_id,
            "vehicle_plate": self.vehicle_plate,
            "access_point": self.access_point,
            "authorized": self.authorized,
            "authorization_method": self.authorization_method,
            "visitor_info": self.visitor_info,
            "image_path": self.image_path,
            "metadata": self.metadata
        }

class SuspiciousActivity(Base):
    """Registro de atividades suspeitas."""
    __tablename__ = "suspicious_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    activity_type = Column(String)  # Tipo de atividade suspeita
    location = Column(String)
    duration = Column(Float)  # Duração em segundos
    person_count = Column(Integer)
    description = Column(String)
    confidence = Column(Float)
    image_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    investigated = Column(Boolean, default=False)
    investigation_notes = Column(String, nullable=True)
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "activity_type": self.activity_type,
            "location": self.location,
            "duration": self.duration,
            "person_count": self.person_count,
            "description": self.description,
            "confidence": self.confidence,
            "image_path": self.image_path,
            "video_path": self.video_path,
            "investigated": self.investigated,
            "investigation_notes": self.investigation_notes,
            "metadata": self.metadata
        }

class SecurityMetrics(Base):
    """Métricas de segurança agregadas."""
    __tablename__ = "security_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    period = Column(String)  # hourly, daily, weekly
    total_accesses = Column(Integer)
    authorized_accesses = Column(Integer)
    unauthorized_accesses = Column(Integer)
    suspicious_activities = Column(Integer)
    alerts_generated = Column(Integer)
    average_response_time = Column(Float, nullable=True)  # Tempo médio de resposta
    visitor_count = Column(Integer)
    resident_count = Column(Integer)
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "period": self.period,
            "total_accesses": self.total_accesses,
            "authorized_accesses": self.authorized_accesses,
            "unauthorized_accesses": self.unauthorized_accesses,
            "suspicious_activities": self.suspicious_activities,
            "alerts_generated": self.alerts_generated,
            "average_response_time": self.average_response_time,
            "visitor_count": self.visitor_count,
            "resident_count": self.resident_count,
            "metadata": self.metadata
        }

# Funções auxiliares para manipulação dos dados
def create_security_event(db, event_data: dict):
    """Cria um novo evento de segurança."""
    event = SecurityEvent(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def create_security_alert(db, alert_data: dict):
    """Cria um novo alerta de segurança."""
    alert = SecurityAlert(**alert_data)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def create_access_log(db, log_data: dict):
    """Cria um novo registro de acesso."""
    log = AccessLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def create_suspicious_activity(db, activity_data: dict):
    """Cria um novo registro de atividade suspeita."""
    activity = SuspiciousActivity(**activity_data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

def create_security_metrics(db, metrics_data: dict):
    """Cria um novo registro de métricas."""
    metrics = SecurityMetrics(**metrics_data)
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    return metrics

def get_security_events(db, stream_id: str, start_time: datetime = None, end_time: datetime = None):
    """Obtém eventos de segurança filtrados."""
    query = db.query(SecurityEvent).filter(SecurityEvent.stream_id == stream_id)
    if start_time:
        query = query.filter(SecurityEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(SecurityEvent.timestamp <= end_time)
    return query.all()

def get_security_alerts(db, stream_id: str, resolved: bool = None):
    """Obtém alertas de segurança filtrados."""
    query = db.query(SecurityAlert).filter(SecurityAlert.stream_id == stream_id)
    if resolved is not None:
        query = query.filter(SecurityAlert.resolved == resolved)
    return query.all()

def get_access_logs(db, stream_id: str, access_type: str = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém logs de acesso filtrados."""
    query = db.query(AccessLog).filter(AccessLog.stream_id == stream_id)
    if access_type:
        query = query.filter(AccessLog.access_type == access_type)
    if start_time:
        query = query.filter(AccessLog.timestamp >= start_time)
    if end_time:
        query = query.filter(AccessLog.timestamp <= end_time)
    return query.all()

def get_suspicious_activities(db, stream_id: str, investigated: bool = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém atividades suspeitas filtradas."""
    query = db.query(SuspiciousActivity).filter(SuspiciousActivity.stream_id == stream_id)
    if investigated is not None:
        query = query.filter(SuspiciousActivity.investigated == investigated)
    if start_time:
        query = query.filter(SuspiciousActivity.timestamp >= start_time)
    if end_time:
        query = query.filter(SuspiciousActivity.timestamp <= end_time)
    return query.all()

def get_security_metrics(db, stream_id: str, period: str = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém métricas de segurança filtradas."""
    query = db.query(SecurityMetrics).filter(SecurityMetrics.stream_id == stream_id)
    if period:
        query = query.filter(SecurityMetrics.period == period)
    if start_time:
        query = query.filter(SecurityMetrics.timestamp >= start_time)
    if end_time:
        query = query.filter(SecurityMetrics.timestamp <= end_time)
    return query.all() 