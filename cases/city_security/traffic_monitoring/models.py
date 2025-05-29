"""
Modelos de banco de dados para monitoramento de tráfego.
Este módulo contém as definições das tabelas específicas para eventos de tráfego.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from cases.database_config import Base, BaseEvent, BaseAlert

class VehicleType(enum.Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    BUS = "bus"
    TRUCK = "truck"

class TrafficEvent(BaseEvent):
    """Eventos de tráfego."""
    __tablename__ = "traffic_events"
    
    vehicle_type = Column(String)  # Tipo de veículo detectado
    speed = Column(Float, nullable=True)  # Velocidade estimada
    direction = Column(String, nullable=True)  # Direção do movimento
    lane = Column(String, nullable=True)  # Faixa de tráfego
    traffic_light_state = Column(String, nullable=True)  # Estado do semáforo
    violation_type = Column(String, nullable=True)  # Tipo de violação, se houver
    
    def __repr__(self):
        return f"<TrafficEvent(vehicle_type={self.vehicle_type}, speed={self.speed}, timestamp={self.timestamp})>"

class TrafficAlert(BaseAlert):
    """Alertas de tráfego."""
    __tablename__ = "traffic_alerts"
    
    vehicle_count = Column(Integer)  # Número de veículos envolvidos
    congestion_level = Column(Float)  # Nível de congestionamento
    average_speed = Column(Float, nullable=True)  # Velocidade média
    affected_area = Column(String)  # Área afetada
    traffic_condition = Column(String)  # Condição do tráfego
    
    def __repr__(self):
        return f"<TrafficAlert(type={self.alert_type}, severity={self.severity}, timestamp={self.timestamp})>"

class TrafficViolation(Base):
    """Registro de violações de trânsito."""
    __tablename__ = "traffic_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    vehicle_type = Column(String)
    violation_type = Column(String)  # Ex: excesso de velocidade, semáforo vermelho
    speed = Column(Float, nullable=True)
    location = Column(String)
    confidence = Column(Float)
    image_path = Column(String, nullable=True)  # Caminho para a imagem da violação
    processed = Column(Boolean, default=False)  # Se a violação foi processada
    ticket_issued = Column(Boolean, default=False)  # Se uma multa foi emitida
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "vehicle_type": self.vehicle_type,
            "violation_type": self.violation_type,
            "speed": self.speed,
            "location": self.location,
            "confidence": self.confidence,
            "image_path": self.image_path,
            "processed": self.processed,
            "ticket_issued": self.ticket_issued,
            "metadata": self.metadata
        }

class TrafficMetrics(Base):
    """Métricas de tráfego agregadas."""
    __tablename__ = "traffic_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    period = Column(String)  # hourly, daily, weekly
    vehicle_count = Column(Integer)
    average_speed = Column(Float)
    congestion_level = Column(Float)
    vehicle_types = Column(JSON)  # Contagem por tipo de veículo
    peak_hours = Column(JSON)  # Horários de pico
    traffic_flow = Column(JSON)  # Fluxo de tráfego por direção
    weather_conditions = Column(String, nullable=True)
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "period": self.period,
            "vehicle_count": self.vehicle_count,
            "average_speed": self.average_speed,
            "congestion_level": self.congestion_level,
            "vehicle_types": self.vehicle_types,
            "peak_hours": self.peak_hours,
            "traffic_flow": self.traffic_flow,
            "weather_conditions": self.weather_conditions,
            "metadata": self.metadata
        }

# Funções auxiliares para manipulação dos dados
def create_traffic_event(db, event_data: dict):
    """Cria um novo evento de tráfego."""
    event = TrafficEvent(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def create_traffic_alert(db, alert_data: dict):
    """Cria um novo alerta de tráfego."""
    alert = TrafficAlert(**alert_data)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def create_traffic_violation(db, violation_data: dict):
    """Cria um novo registro de violação."""
    violation = TrafficViolation(**violation_data)
    db.add(violation)
    db.commit()
    db.refresh(violation)
    return violation

def create_traffic_metrics(db, metrics_data: dict):
    """Cria um novo registro de métricas."""
    metrics = TrafficMetrics(**metrics_data)
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    return metrics

def get_traffic_events(db, stream_id: str, start_time: datetime = None, end_time: datetime = None):
    """Obtém eventos de tráfego filtrados."""
    query = db.query(TrafficEvent).filter(TrafficEvent.stream_id == stream_id)
    if start_time:
        query = query.filter(TrafficEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(TrafficEvent.timestamp <= end_time)
    return query.all()

def get_traffic_alerts(db, stream_id: str, resolved: bool = None):
    """Obtém alertas de tráfego filtrados."""
    query = db.query(TrafficAlert).filter(TrafficAlert.stream_id == stream_id)
    if resolved is not None:
        query = query.filter(TrafficAlert.resolved == resolved)
    return query.all()

def get_traffic_violations(db, stream_id: str, processed: bool = None):
    """Obtém violações de tráfego filtradas."""
    query = db.query(TrafficViolation).filter(TrafficViolation.stream_id == stream_id)
    if processed is not None:
        query = query.filter(TrafficViolation.processed == processed)
    return query.all()

def get_traffic_metrics(db, stream_id: str, period: str = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém métricas de tráfego filtradas."""
    query = db.query(TrafficMetrics).filter(TrafficMetrics.stream_id == stream_id)
    if period:
        query = query.filter(TrafficMetrics.period == period)
    if start_time:
        query = query.filter(TrafficMetrics.timestamp >= start_time)
    if end_time:
        query = query.filter(TrafficMetrics.timestamp <= end_time)
    return query.all() 