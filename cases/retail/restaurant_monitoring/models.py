"""
Modelos de banco de dados para monitoramento de bares e restaurantes.
Este módulo contém as definições das tabelas específicas para eventos de restaurante.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from cases.database_config import Base, BaseEvent, BaseAlert

class AreaType(enum.Enum):
    ENTRANCE = "entrance"
    DINING = "dining"
    BAR = "bar"
    KITCHEN = "kitchen"
    SERVICE = "service"

class RestaurantEvent(BaseEvent):
    """Eventos de restaurante."""
    __tablename__ = "restaurant_events"
    
    area_type = Column(String)  # Tipo de área (entrada, salão, bar, etc.)
    person_count = Column(Integer)  # Número de pessoas detectadas
    table_id = Column(String, nullable=True)  # ID da mesa, se aplicável
    wait_time = Column(Float, nullable=True)  # Tempo de espera em segundos
    queue_length = Column(Integer, nullable=True)  # Tamanho da fila
    staff_present = Column(Boolean)  # Se há funcionários presentes
    
    def __repr__(self):
        return f"<RestaurantEvent(type={self.event_type}, area={self.area_type}, timestamp={self.timestamp})>"

class RestaurantAlert(BaseAlert):
    """Alertas de restaurante."""
    __tablename__ = "restaurant_alerts"
    
    alert_category = Column(String)  # Categoria do alerta (fila, ocupação, etc.)
    affected_area = Column(String)  # Área afetada
    person_count = Column(Integer, nullable=True)  # Número de pessoas envolvidas
    wait_time = Column(Float, nullable=True)  # Tempo de espera
    queue_length = Column(Integer, nullable=True)  # Tamanho da fila
    table_occupancy = Column(Float, nullable=True)  # Taxa de ocupação das mesas
    staff_notified = Column(Boolean, default=False)  # Se a equipe foi notificada
    
    def __repr__(self):
        return f"<RestaurantAlert(type={self.alert_type}, category={self.alert_category}, timestamp={self.timestamp})>"

class CustomerMetrics(Base):
    """Métricas de clientes."""
    __tablename__ = "customer_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    area_type = Column(String)
    customer_count = Column(Integer)
    wait_time = Column(Float, nullable=True)
    queue_length = Column(Integer, nullable=True)
    table_occupancy = Column(Float, nullable=True)
    average_stay_time = Column(Float, nullable=True)  # Tempo médio de permanência
    peak_hour = Column(Boolean, default=False)  # Se é horário de pico
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "area_type": self.area_type,
            "customer_count": self.customer_count,
            "wait_time": self.wait_time,
            "queue_length": self.queue_length,
            "table_occupancy": self.table_occupancy,
            "average_stay_time": self.average_stay_time,
            "peak_hour": self.peak_hour,
            "metadata": self.metadata
        }

class StaffMetrics(Base):
    """Métricas da equipe."""
    __tablename__ = "staff_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    area_type = Column(String)
    staff_count = Column(Integer)
    activity_level = Column(Float)  # Nível de atividade (0-1)
    response_time = Column(Float, nullable=True)  # Tempo médio de resposta
    table_visits = Column(Integer)  # Número de visitas às mesas
    idle_time = Column(Float, nullable=True)  # Tempo ocioso
    service_quality_score = Column(Float, nullable=True)  # Pontuação de qualidade
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "area_type": self.area_type,
            "staff_count": self.staff_count,
            "activity_level": self.activity_level,
            "response_time": self.response_time,
            "table_visits": self.table_visits,
            "idle_time": self.idle_time,
            "service_quality_score": self.service_quality_score,
            "metadata": self.metadata
        }

class TableStatus(Base):
    """Status das mesas."""
    __tablename__ = "table_status"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    table_id = Column(String, index=True)
    status = Column(String)  # occupied, available, reserved, cleaning
    customer_count = Column(Integer, nullable=True)
    occupancy_start = Column(DateTime, nullable=True)
    estimated_departure = Column(DateTime, nullable=True)
    wait_time = Column(Float, nullable=True)  # Tempo de espera para esta mesa
    last_service = Column(DateTime, nullable=True)  # Último atendimento
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "table_id": self.table_id,
            "status": self.status,
            "customer_count": self.customer_count,
            "occupancy_start": self.occupancy_start.isoformat() if self.occupancy_start else None,
            "estimated_departure": self.estimated_departure.isoformat() if self.estimated_departure else None,
            "wait_time": self.wait_time,
            "last_service": self.last_service.isoformat() if self.last_service else None,
            "metadata": self.metadata
        }

class BusinessAnalytics(Base):
    """Análises de negócio."""
    __tablename__ = "business_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    period = Column(String)  # hourly, daily, weekly
    total_customers = Column(Integer)
    average_wait_time = Column(Float)
    peak_hours = Column(JSON)  # Horários de pico
    table_turnover = Column(Float)  # Taxa de rotatividade das mesas
    staff_efficiency = Column(Float)  # Eficiência da equipe
    customer_satisfaction = Column(Float, nullable=True)  # Índice de satisfação
    revenue_per_hour = Column(Float, nullable=True)  # Receita por hora
    metadata = Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "stream_id": self.stream_id,
            "timestamp": self.timestamp.isoformat(),
            "period": self.period,
            "total_customers": self.total_customers,
            "average_wait_time": self.average_wait_time,
            "peak_hours": self.peak_hours,
            "table_turnover": self.table_turnover,
            "staff_efficiency": self.staff_efficiency,
            "customer_satisfaction": self.customer_satisfaction,
            "revenue_per_hour": self.revenue_per_hour,
            "metadata": self.metadata
        }

# Funções auxiliares para manipulação dos dados
def create_restaurant_event(db, event_data: dict):
    """Cria um novo evento de restaurante."""
    event = RestaurantEvent(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def create_restaurant_alert(db, alert_data: dict):
    """Cria um novo alerta de restaurante."""
    alert = RestaurantAlert(**alert_data)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def create_customer_metrics(db, metrics_data: dict):
    """Cria um novo registro de métricas de clientes."""
    metrics = CustomerMetrics(**metrics_data)
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    return metrics

def create_staff_metrics(db, metrics_data: dict):
    """Cria um novo registro de métricas da equipe."""
    metrics = StaffMetrics(**metrics_data)
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    return metrics

def create_table_status(db, status_data: dict):
    """Cria um novo registro de status de mesa."""
    status = TableStatus(**status_data)
    db.add(status)
    db.commit()
    db.refresh(status)
    return status

def create_business_analytics(db, analytics_data: dict):
    """Cria um novo registro de análises de negócio."""
    analytics = BusinessAnalytics(**analytics_data)
    db.add(analytics)
    db.commit()
    db.refresh(analytics)
    return analytics

def get_restaurant_events(db, stream_id: str, area_type: str = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém eventos de restaurante filtrados."""
    query = db.query(RestaurantEvent).filter(RestaurantEvent.stream_id == stream_id)
    if area_type:
        query = query.filter(RestaurantEvent.area_type == area_type)
    if start_time:
        query = query.filter(RestaurantEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(RestaurantEvent.timestamp <= end_time)
    return query.all()

def get_restaurant_alerts(db, stream_id: str, resolved: bool = None):
    """Obtém alertas de restaurante filtrados."""
    query = db.query(RestaurantAlert).filter(RestaurantAlert.stream_id == stream_id)
    if resolved is not None:
        query = query.filter(RestaurantAlert.resolved == resolved)
    return query.all()

def get_customer_metrics(db, stream_id: str, area_type: str = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém métricas de clientes filtradas."""
    query = db.query(CustomerMetrics).filter(CustomerMetrics.stream_id == stream_id)
    if area_type:
        query = query.filter(CustomerMetrics.area_type == area_type)
    if start_time:
        query = query.filter(CustomerMetrics.timestamp >= start_time)
    if end_time:
        query = query.filter(CustomerMetrics.timestamp <= end_time)
    return query.all()

def get_staff_metrics(db, stream_id: str, area_type: str = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém métricas da equipe filtradas."""
    query = db.query(StaffMetrics).filter(StaffMetrics.stream_id == stream_id)
    if area_type:
        query = query.filter(StaffMetrics.area_type == area_type)
    if start_time:
        query = query.filter(StaffMetrics.timestamp >= start_time)
    if end_time:
        query = query.filter(StaffMetrics.timestamp <= end_time)
    return query.all()

def get_table_status(db, stream_id: str, table_id: str = None, status: str = None):
    """Obtém status das mesas filtrado."""
    query = db.query(TableStatus).filter(TableStatus.stream_id == stream_id)
    if table_id:
        query = query.filter(TableStatus.table_id == table_id)
    if status:
        query = query.filter(TableStatus.status == status)
    return query.all()

def get_business_analytics(db, stream_id: str, period: str = None, start_time: datetime = None, end_time: datetime = None):
    """Obtém análises de negócio filtradas."""
    query = db.query(BusinessAnalytics).filter(BusinessAnalytics.stream_id == stream_id)
    if period:
        query = query.filter(BusinessAnalytics.period == period)
    if start_time:
        query = query.filter(BusinessAnalytics.timestamp >= start_time)
    if end_time:
        query = query.filter(BusinessAnalytics.timestamp <= end_time)
    return query.all() 