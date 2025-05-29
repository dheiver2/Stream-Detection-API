"""
Exemplo de uso da API para monitoramento de tráfego em cidades.
Este script demonstra como configurar e usar a API para diferentes cenários de monitoramento de tráfego.
"""

import requests
import json
import time
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional

from config import TRAFFIC_CONFIG, CAMERA_CONFIGS, ALERT_CONFIG, EXPORT_CONFIG

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrafficMonitoring:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.active_streams: Dict[str, dict] = {}
        
    def start_intersection_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento de uma interseção."""
        try:
            config = TRAFFIC_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["intersection"]["model_config"])
            
            stream_config = {
                "url": rtsp_url,
                "stream_id": stream_id,
                "model_config": config["model_config"],
                "rtsp_config": config["rtsp_config"],
                "output_dir": f"output/intersection/{stream_id}"
            }
            
            response = requests.post(
                f"{self.api_url}/start-detection",
                json=stream_config
            )
            
            if response.status_code == 200:
                self.active_streams[stream_id] = {
                    "type": "intersection",
                    "config": stream_config,
                    "start_time": datetime.now()
                }
                logger.info(f"Monitoramento iniciado para interseção {stream_id}")
                return True
            else:
                logger.error(f"Erro ao iniciar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento de interseção: {str(e)}")
            return False
    
    def start_highway_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento de uma rodovia."""
        try:
            config = TRAFFIC_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["highway"]["model_config"])
            
            stream_config = {
                "url": rtsp_url,
                "stream_id": stream_id,
                "model_config": config["model_config"],
                "rtsp_config": config["rtsp_config"],
                "output_dir": f"output/highway/{stream_id}"
            }
            
            response = requests.post(
                f"{self.api_url}/start-detection",
                json=stream_config
            )
            
            if response.status_code == 200:
                self.active_streams[stream_id] = {
                    "type": "highway",
                    "config": stream_config,
                    "start_time": datetime.now()
                }
                logger.info(f"Monitoramento iniciado para rodovia {stream_id}")
                return True
            else:
                logger.error(f"Erro ao iniciar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento de rodovia: {str(e)}")
            return False
    
    def start_parking_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento de um estacionamento."""
        try:
            config = TRAFFIC_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["parking"]["model_config"])
            
            stream_config = {
                "url": rtsp_url,
                "stream_id": stream_id,
                "model_config": config["model_config"],
                "rtsp_config": config["rtsp_config"],
                "output_dir": f"output/parking/{stream_id}"
            }
            
            response = requests.post(
                f"{self.api_url}/start-detection",
                json=stream_config
            )
            
            if response.status_code == 200:
                self.active_streams[stream_id] = {
                    "type": "parking",
                    "config": stream_config,
                    "start_time": datetime.now()
                }
                logger.info(f"Monitoramento iniciado para estacionamento {stream_id}")
                return True
            else:
                logger.error(f"Erro ao iniciar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento de estacionamento: {str(e)}")
            return False
    
    def stop_monitoring(self, stream_id: str) -> bool:
        """Para o monitoramento de um stream específico."""
        try:
            response = requests.post(
                f"{self.api_url}/stop-detection",
                json={"stream_id": stream_id}
            )
            
            if response.status_code == 200:
                if stream_id in self.active_streams:
                    del self.active_streams[stream_id]
                logger.info(f"Monitoramento parado para {stream_id}")
                return True
            else:
                logger.error(f"Erro ao parar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao parar monitoramento: {str(e)}")
            return False
    
    def get_stream_status(self, stream_id: str) -> Optional[dict]:
        """Obtém o status atual de um stream."""
        try:
            response = requests.get(
                f"{self.api_url}/stream-status/{stream_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao obter status: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter status do stream: {str(e)}")
            return None
    
    def check_alerts(self, stream_id: str) -> List[dict]:
        """Verifica alertas para um stream específico."""
        alerts = []
        status = self.get_stream_status(stream_id)
        
        if not status:
            return alerts
            
        # Verifica congestionamento
        if ALERT_CONFIG["congestion"]["enabled"]:
            vehicle_count = sum(status.get("detection_counts", {}).values())
            if vehicle_count >= ALERT_CONFIG["congestion"]["threshold"]:
                alerts.append({
                    "type": "congestion",
                    "stream_id": stream_id,
                    "severity": "high",
                    "message": f"Congestionamento detectado: {vehicle_count} veículos",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Verifica acidentes
        if ALERT_CONFIG["accident"]["enabled"]:
            stopped_vehicles = status.get("analysis_data", {}).get("stopped_vehicles", 0)
            if stopped_vehicles >= ALERT_CONFIG["accident"]["detection"]["stopped_vehicles"]:
                alerts.append({
                    "type": "accident",
                    "stream_id": stream_id,
                    "severity": "critical",
                    "message": f"Possível acidente detectado: {stopped_vehicles} veículos parados",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Verifica excesso de velocidade
        if ALERT_CONFIG["speeding"]["enabled"]:
            speeds = status.get("analysis_data", {}).get("speeds", [])
            if speeds:
                avg_speed = sum(speeds) / len(speeds)
                if avg_speed > ALERT_CONFIG["speeding"]["speed_limit"] * ALERT_CONFIG["speeding"]["threshold"]:
                    alerts.append({
                        "type": "speeding",
                        "stream_id": stream_id,
                        "severity": "medium",
                        "message": f"Excesso de velocidade detectado: {avg_speed:.1f} km/h",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return alerts
    
    def export_data(self, stream_id: str) -> bool:
        """Exporta dados do stream para os formatos configurados."""
        try:
            status = self.get_stream_status(stream_id)
            if not status:
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Exporta dados de tráfego
            if EXPORT_CONFIG["traffic_data"]["enabled"]:
                traffic_data = {
                    "timestamp": timestamp,
                    "vehicle_count": sum(status.get("detection_counts", {}).values()),
                    "vehicle_types": status.get("detection_counts", {}),
                    "average_speed": status.get("analysis_data", {}).get("average_speed", 0),
                    "congestion_level": status.get("analysis_data", {}).get("congestion_level", 0)
                }
                
                output_dir = Path(EXPORT_CONFIG["traffic_data"]["destination"])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                with open(output_dir / f"traffic_data_{stream_id}_{timestamp}.json", "w") as f:
                    json.dump(traffic_data, f, indent=2)
            
            # Exporta violações
            if EXPORT_CONFIG["violations"]["enabled"]:
                violations = status.get("analysis_data", {}).get("violations", [])
                if violations:
                    output_dir = Path(EXPORT_CONFIG["violations"]["destination"])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_dir / f"violations_{stream_id}_{timestamp}.csv", "w") as f:
                        f.write(",".join(EXPORT_CONFIG["violations"]["fields"]) + "\n")
                        for violation in violations:
                            f.write(",".join(str(violation.get(field, "")) for field in EXPORT_CONFIG["violations"]["fields"]) + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            return False

def main():
    """Função principal com exemplo de uso."""
    # Inicializa o monitoramento
    monitor = TrafficMonitoring()
    
    # Exemplo de monitoramento de interseção
    intersection_url = "rtsp://camera1.city.gov/intersection1"
    if monitor.start_intersection_monitoring("intersection1", intersection_url):
        logger.info("Monitoramento de interseção iniciado com sucesso")
    
    # Exemplo de monitoramento de rodovia
    highway_url = "rtsp://camera2.city.gov/highway1"
    if monitor.start_highway_monitoring("highway1", highway_url):
        logger.info("Monitoramento de rodovia iniciado com sucesso")
    
    # Exemplo de monitoramento de estacionamento
    parking_url = "rtsp://camera3.city.gov/parking1"
    if monitor.start_parking_monitoring("parking1", parking_url):
        logger.info("Monitoramento de estacionamento iniciado com sucesso")
    
    try:
        # Loop principal de monitoramento
        while True:
            for stream_id in list(monitor.active_streams.keys()):
                # Verifica status
                status = monitor.get_stream_status(stream_id)
                if status:
                    logger.info(f"Status do stream {stream_id}: {json.dumps(status, indent=2)}")
                
                # Verifica alertas
                alerts = monitor.check_alerts(stream_id)
                for alert in alerts:
                    logger.warning(f"Alerta detectado: {json.dumps(alert, indent=2)}")
                
                # Exporta dados periodicamente
                if datetime.now().second % EXPORT_CONFIG["traffic_data"]["interval"] == 0:
                    monitor.export_data(stream_id)
            
            time.sleep(1)  # Aguarda 1 segundo antes da próxima verificação
            
    except KeyboardInterrupt:
        logger.info("Encerrando monitoramento...")
    finally:
        # Para todos os streams ativos
        for stream_id in list(monitor.active_streams.keys()):
            monitor.stop_monitoring(stream_id)

if __name__ == "__main__":
    main() 