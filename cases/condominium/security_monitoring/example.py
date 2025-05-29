"""
Exemplo de uso da API para monitoramento de segurança em condomínios.
Este script demonstra como configurar e usar a API para diferentes cenários de segurança.
"""

import requests
import json
import time
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional
import shutil
import os

from config import SECURITY_CONFIG, CAMERA_CONFIGS, ALERT_CONFIG, EXPORT_CONFIG, BACKUP_CONFIG

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityMonitoring:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.active_streams: Dict[str, dict] = {}
        self.backup_manager = BackupManager()
        
    def start_entrance_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento da entrada principal."""
        try:
            config = SECURITY_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["entrada"]["model_config"])
            
            stream_config = {
                "url": rtsp_url,
                "stream_id": stream_id,
                "model_config": config["model_config"],
                "rtsp_config": config["rtsp_config"],
                "output_dir": f"output/entrance/{stream_id}"
            }
            
            response = requests.post(
                f"{self.api_url}/start-detection",
                json=stream_config
            )
            
            if response.status_code == 200:
                self.active_streams[stream_id] = {
                    "type": "entrance",
                    "config": stream_config,
                    "start_time": datetime.now()
                }
                logger.info(f"Monitoramento iniciado para entrada {stream_id}")
                return True
            else:
                logger.error(f"Erro ao iniciar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento de entrada: {str(e)}")
            return False
    
    def start_parking_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento do estacionamento."""
        try:
            config = SECURITY_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["estacionamento"]["model_config"])
            
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
    
    def start_common_areas_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento das áreas comuns."""
        try:
            config = SECURITY_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["areas_comuns"]["model_config"])
            
            stream_config = {
                "url": rtsp_url,
                "stream_id": stream_id,
                "model_config": config["model_config"],
                "rtsp_config": config["rtsp_config"],
                "output_dir": f"output/common_areas/{stream_id}"
            }
            
            response = requests.post(
                f"{self.api_url}/start-detection",
                json=stream_config
            )
            
            if response.status_code == 200:
                self.active_streams[stream_id] = {
                    "type": "common_areas",
                    "config": stream_config,
                    "start_time": datetime.now()
                }
                logger.info(f"Monitoramento iniciado para área comum {stream_id}")
                return True
            else:
                logger.error(f"Erro ao iniciar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento de área comum: {str(e)}")
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
            
        stream_type = self.active_streams[stream_id]["type"]
        analysis_data = status.get("analysis_data", {})
        
        # Verifica acesso não autorizado
        if ALERT_CONFIG["unauthorized_access"]["enabled"]:
            unauthorized = analysis_data.get("unauthorized_access", [])
            for access in unauthorized:
                alerts.append({
                    "type": "unauthorized_access",
                    "stream_id": stream_id,
                    "severity": "high",
                    "message": f"Acesso não autorizado detectado em {access['area']}",
                    "timestamp": datetime.now().isoformat(),
                    "details": access
                })
        
        # Verifica comportamento suspeito
        if ALERT_CONFIG["suspicious_behavior"]["enabled"]:
            suspicious = analysis_data.get("suspicious_behavior", {})
            
            # Verifica permanência suspeita
            if suspicious.get("loitering"):
                alerts.append({
                    "type": "suspicious_behavior",
                    "subtype": "loitering",
                    "stream_id": stream_id,
                    "severity": "medium",
                    "message": "Permanência suspeita detectada",
                    "timestamp": datetime.now().isoformat(),
                    "details": suspicious["loitering"]
                })
            
            # Verifica aglomeração
            if suspicious.get("crowding"):
                alerts.append({
                    "type": "suspicious_behavior",
                    "subtype": "crowding",
                    "stream_id": stream_id,
                    "severity": "medium",
                    "message": "Aglomeração detectada",
                    "timestamp": datetime.now().isoformat(),
                    "details": suspicious["crowding"]
                })
        
        # Verifica aglomeração específica para áreas comuns
        if stream_type == "common_areas" and ALERT_CONFIG["crowding"]["enabled"]:
            crowd_count = sum(status.get("detection_counts", {}).values())
            if crowd_count >= CAMERA_CONFIGS["areas_comuns"]["model_config"]["analysis"]["parameters"]["crowd_monitoring"]["alert_threshold"]:
                alerts.append({
                    "type": "crowding",
                    "stream_id": stream_id,
                    "severity": "high",
                    "message": f"Aglomeração detectada: {crowd_count} pessoas",
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
            stream_type = self.active_streams[stream_id]["type"]
            
            # Exporta logs de acesso
            if EXPORT_CONFIG["access_logs"]["enabled"] and stream_type == "entrance":
                access_data = {
                    "timestamp": timestamp,
                    "camera_id": stream_id,
                    "event_type": "access",
                    "object_type": "person",
                    "confidence": status.get("average_confidence", 0),
                    "location": "entrance"
                }
                
                output_dir = Path(EXPORT_CONFIG["access_logs"]["destination"])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                with open(output_dir / f"access_log_{stream_id}_{timestamp}.json", "w") as f:
                    json.dump(access_data, f, indent=2)
            
            # Exporta eventos de segurança
            if EXPORT_CONFIG["security_events"]["enabled"]:
                events = status.get("analysis_data", {}).get("security_events", [])
                if events:
                    output_dir = Path(EXPORT_CONFIG["security_events"]["destination"])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_dir / f"security_events_{stream_id}_{timestamp}.csv", "w") as f:
                        f.write(",".join(EXPORT_CONFIG["security_events"]["fields"]) + "\n")
                        for event in events:
                            f.write(",".join(str(event.get(field, "")) for field in EXPORT_CONFIG["security_events"]["fields"]) + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            return False
    
    def handle_backup(self, stream_id: str, alert: dict) -> bool:
        """Gerencia o backup de vídeo quando um alerta é detectado."""
        try:
            if not BACKUP_CONFIG["enabled"]:
                return False
            
            stream_type = self.active_streams[stream_id]["type"]
            output_dir = Path(self.active_streams[stream_id]["config"]["output_dir"])
            
            if not output_dir.exists():
                return False
            
            # Cria diretório de backup se não existir
            backup_dir = Path(BACKUP_CONFIG["storage"]["path"]) / stream_type / stream_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copia os vídeos relevantes
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_event = BACKUP_CONFIG["triggers"]["alert"]["pre_event"]
            post_event = BACKUP_CONFIG["triggers"]["alert"]["post_event"]
            
            # Encontra os vídeos relevantes
            video_files = list(output_dir.glob("*.mp4"))
            relevant_videos = []
            
            for video in video_files:
                video_time = datetime.fromtimestamp(video.stat().st_mtime)
                if abs((video_time - datetime.now()).total_seconds()) <= (pre_event + post_event):
                    relevant_videos.append(video)
            
            # Copia os vídeos para o backup
            for video in relevant_videos:
                backup_name = f"backup_{alert['type']}_{timestamp}_{video.name}"
                shutil.copy2(video, backup_dir / backup_name)
            
            # Limpa backups antigos
            self.backup_manager.cleanup_old_backups(backup_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao fazer backup: {str(e)}")
            return False

class BackupManager:
    def __init__(self):
        self.retention_days = BACKUP_CONFIG["storage"]["retention_days"]
    
    def cleanup_old_backups(self, backup_dir: Path) -> None:
        """Remove backups mais antigos que o período de retenção."""
        try:
            current_time = datetime.now()
            for backup_file in backup_dir.glob("*"):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if (current_time - file_time).days > self.retention_days:
                        backup_file.unlink()
                        logger.info(f"Backup antigo removido: {backup_file}")
        except Exception as e:
            logger.error(f"Erro ao limpar backups antigos: {str(e)}")

def main():
    """Função principal com exemplo de uso."""
    # Inicializa o monitoramento
    monitor = SecurityMonitoring()
    
    # Exemplo de monitoramento de entrada
    entrance_url = "rtsp://camera1.condominio.com/entrance1"
    if monitor.start_entrance_monitoring("entrance1", entrance_url):
        logger.info("Monitoramento de entrada iniciado com sucesso")
    
    # Exemplo de monitoramento de estacionamento
    parking_url = "rtsp://camera2.condominio.com/parking1"
    if monitor.start_parking_monitoring("parking1", parking_url):
        logger.info("Monitoramento de estacionamento iniciado com sucesso")
    
    # Exemplo de monitoramento de áreas comuns
    common_areas_url = "rtsp://camera3.condominio.com/common1"
    if monitor.start_common_areas_monitoring("common1", common_areas_url):
        logger.info("Monitoramento de áreas comuns iniciado com sucesso")
    
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
                    
                    # Faz backup do vídeo se necessário
                    if alert["severity"] in ["high", "critical"]:
                        monitor.handle_backup(stream_id, alert)
                
                # Exporta dados periodicamente
                if datetime.now().second % EXPORT_CONFIG["access_logs"]["interval"] == 0:
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