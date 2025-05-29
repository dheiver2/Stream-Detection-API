"""
Testes para a API de detecção.
Este módulo contém testes unitários e de integração.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import cv2
import numpy as np
from datetime import datetime, timedelta
from api import app
from config.settings import API_CONFIG, MODEL_CONFIG
from cases.database_config import get_db_session, Base, engine
from cases.event_manager import event_manager

# Configurar cliente de teste
client = TestClient(app)

# Fixtures
@pytest.fixture(scope="session")
def test_db():
    """Fixture para banco de dados de teste."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_stream():
    """Fixture para stream de vídeo mock."""
    return Mock(spec=cv2.VideoCapture)

@pytest.fixture
def mock_model():
    """Fixture para modelo YOLO mock."""
    return Mock()

@pytest.fixture
def sample_frame():
    """Fixture para frame de teste."""
    return np.zeros((480, 640, 3), dtype=np.uint8)

# Testes de API
def test_health_check():
    """Testa endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_stream_creation():
    """Testa criação de stream."""
    stream_data = {
        "stream_id": "test_stream",
        "url": "rtsp://test.com/stream",
        "case_type": "traffic",
        "config": {
            "buffer_size": 30,
            "confidence_threshold": 0.5
        }
    }
    
    response = client.post("/streams", json=stream_data)
    assert response.status_code == 201
    assert response.json()["stream_id"] == "test_stream"

def test_stream_deletion():
    """Testa deleção de stream."""
    response = client.delete("/streams/test_stream")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

def test_invalid_stream():
    """Testa stream inválido."""
    response = client.get("/streams/invalid_stream/status")
    assert response.status_code == 404

# Testes de Detecção
@patch("api.process_stream")
def test_detection_processing(mock_process):
    """Testa processamento de detecção."""
    mock_process.return_value = {
        "detections": [
            {"class": "car", "confidence": 0.9, "bbox": [0, 0, 100, 100]}
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/detect",
        json={
            "stream_id": "test_stream",
            "frame": "base64_encoded_frame"
        }
    )
    
    assert response.status_code == 200
    assert "detections" in response.json()

# Testes de Eventos
def test_event_creation(test_db):
    """Testa criação de evento."""
    event_data = {
        "stream_id": "test_stream",
        "event_type": "traffic_violation",
        "confidence": 0.95,
        "metadata": {
            "violation_type": "speed",
            "speed": 80
        }
    }
    
    response = client.post("/events", json=event_data)
    assert response.status_code == 201
    assert response.json()["event_type"] == "traffic_violation"

def test_event_retrieval(test_db):
    """Testa recuperação de eventos."""
    response = client.get("/events?stream_id=test_stream&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Testes de Alertas
def test_alert_creation(test_db):
    """Testa criação de alerta."""
    alert_data = {
        "stream_id": "test_stream",
        "alert_type": "high_speed",
        "severity": "high",
        "message": "Vehicle exceeding speed limit",
        "metadata": {
            "speed": 120,
            "location": "highway_1"
        }
    }
    
    response = client.post("/alerts", json=alert_data)
    assert response.status_code == 201
    assert response.json()["alert_type"] == "high_speed"

def test_alert_retrieval(test_db):
    """Testa recuperação de alertas."""
    response = client.get("/alerts?stream_id=test_stream&active=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Testes de Métricas
def test_metrics_retrieval():
    """Testa recuperação de métricas."""
    response = client.get("/metrics?stream_id=test_stream")
    assert response.status_code == 200
    assert "cpu_usage" in response.json()
    assert "memory_usage" in response.json()

# Testes de Casos de Uso
def test_traffic_monitoring():
    """Testa funcionalidades de monitoramento de tráfego."""
    # Criar stream de tráfego
    stream_data = {
        "stream_id": "traffic_test",
        "url": "rtsp://test.com/traffic",
        "case_type": "traffic",
        "config": {
            "track_objects": True,
            "save_violations": True
        }
    }
    
    response = client.post("/streams", json=stream_data)
    assert response.status_code == 201
    
    # Verificar métricas de tráfego
    response = client.get("/cases/traffic/metrics?stream_id=traffic_test")
    assert response.status_code == 200
    assert "vehicle_count" in response.json()

def test_security_monitoring():
    """Testa funcionalidades de monitoramento de segurança."""
    # Criar stream de segurança
    stream_data = {
        "stream_id": "security_test",
        "url": "rtsp://test.com/security",
        "case_type": "security",
        "config": {
            "track_objects": True,
            "save_events": True
        }
    }
    
    response = client.post("/streams", json=stream_data)
    assert response.status_code == 201
    
    # Verificar eventos de segurança
    response = client.get("/cases/security/events?stream_id=security_test")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Testes de Performance
def test_concurrent_streams():
    """Testa processamento de múltiplos streams."""
    # Criar múltiplos streams
    streams = [
        {
            "stream_id": f"test_stream_{i}",
            "url": f"rtsp://test.com/stream_{i}",
            "case_type": "traffic",
            "config": {"buffer_size": 30}
        }
        for i in range(5)
    ]
    
    for stream in streams:
        response = client.post("/streams", json=stream)
        assert response.status_code == 201
    
    # Verificar status dos streams
    response = client.get("/streams/status")
    assert response.status_code == 200
    assert len(response.json()) == 5

# Testes de Erro
def test_invalid_config():
    """Testa configuração inválida."""
    stream_data = {
        "stream_id": "invalid_config",
        "url": "rtsp://test.com/stream",
        "case_type": "invalid_case",
        "config": {}
    }
    
    response = client.post("/streams", json=stream_data)
    assert response.status_code == 400

def test_invalid_credentials():
    """Testa credenciais inválidas."""
    response = client.get("/streams", headers={"Authorization": "invalid_token"})
    assert response.status_code == 401

# Testes de Limpeza
def test_cleanup():
    """Testa limpeza de recursos."""
    # Limpar streams de teste
    for i in range(5):
        response = client.delete(f"/streams/test_stream_{i}")
        assert response.status_code == 200
    
    # Verificar limpeza
    response = client.get("/streams/status")
    assert response.status_code == 200
    assert len(response.json()) == 0 