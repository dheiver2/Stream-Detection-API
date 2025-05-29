"""
Regras de detecção e alertas para monitoramento de segurança em condomínios.
Este módulo contém as regras específicas para detecção de intrusão e geração de alertas.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config.settings import get_case_config
from config.logging_config import CaseLogger

logger = CaseLogger("condominium_security")
CASE_CONFIG = get_case_config("condominium_security")

class SecurityRules:
    """Regras para monitoramento de segurança em condomínios."""
    
    def __init__(self):
        self.min_confidence = CASE_CONFIG.get("min_confidence", 0.6)
        self.restricted_areas = CASE_CONFIG.get("restricted_areas", [])
        self.alert_threshold = CASE_CONFIG.get("alert_threshold", 0.8)
        self.authorized_persons = set()  # Conjunto de pessoas autorizadas
        self.authorized_vehicles = set()  # Conjunto de veículos autorizados
    
    def check_unauthorized_access(self,
                                person_id: Optional[str],
                                vehicle_plate: Optional[str],
                                area: str,
                                timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Verifica acesso não autorizado."""
        if area in self.restricted_areas:
            if person_id and person_id not in self.authorized_persons:
                return {
                    "type": "unauthorized_person",
                    "person_id": person_id,
                    "area": area,
                    "timestamp": timestamp.isoformat(),
                    "severity": "high"
                }
            if vehicle_plate and vehicle_plate not in self.authorized_vehicles:
                return {
                    "type": "unauthorized_vehicle",
                    "vehicle_plate": vehicle_plate,
                    "area": area,
                    "timestamp": timestamp.isoformat(),
                    "severity": "high"
                }
        return None
    
    def check_suspicious_activity(self,
                                activity_type: str,
                                location: str,
                                person_count: int,
                                duration: float) -> Optional[Dict[str, Any]]:
        """Verifica atividades suspeitas."""
        if activity_type == "loitering" and duration > 300:  # 5 minutos
            return {
                "type": "suspicious_loitering",
                "location": location,
                "person_count": person_count,
                "duration": duration,
                "severity": "medium"
            }
        elif activity_type == "crowding" and person_count > 5:
            return {
                "type": "suspicious_crowding",
                "location": location,
                "person_count": person_count,
                "duration": duration,
                "severity": "high"
            }
        return None
    
    def check_restricted_area_access(self,
                                   area: str,
                                   person_count: int,
                                   timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Verifica acesso a áreas restritas."""
        if area in self.restricted_areas and person_count > 0:
            return {
                "type": "restricted_area_access",
                "area": area,
                "person_count": person_count,
                "timestamp": timestamp.isoformat(),
                "severity": "high"
            }
        return None
    
    def check_after_hours_access(self,
                               area: str,
                               timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Verifica acesso fora do horário permitido."""
        hour = timestamp.hour
        if hour < 6 or hour > 22:  # Horário restrito: 22h às 6h
            return {
                "type": "after_hours_access",
                "area": area,
                "timestamp": timestamp.isoformat(),
                "hour": hour,
                "severity": "high"
            }
        return None
    
    def process_detection(self, detection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processa uma detecção e retorna alertas encontrados."""
        alerts = []
        timestamp = datetime.fromisoformat(detection.get("timestamp", datetime.utcnow().isoformat()))
        
        # Verificar acesso não autorizado
        if "person_id" in detection or "vehicle_plate" in detection:
            access_alert = self.check_unauthorized_access(
                detection.get("person_id"),
                detection.get("vehicle_plate"),
                detection.get("area", "unknown"),
                timestamp
            )
            if access_alert:
                alerts.append(access_alert)
        
        # Verificar atividades suspeitas
        if "activity_type" in detection:
            activity_alert = self.check_suspicious_activity(
                detection["activity_type"],
                detection.get("location", "unknown"),
                detection.get("person_count", 0),
                detection.get("duration", 0.0)
            )
            if activity_alert:
                alerts.append(activity_alert)
        
        # Verificar acesso a áreas restritas
        if "area" in detection:
            area_alert = self.check_restricted_area_access(
                detection["area"],
                detection.get("person_count", 0),
                timestamp
            )
            if area_alert:
                alerts.append(area_alert)
            
            # Verificar acesso fora do horário
            hours_alert = self.check_after_hours_access(
                detection["area"],
                timestamp
            )
            if hours_alert:
                alerts.append(hours_alert)
        
        # Registrar alertas
        for alert in alerts:
            logger.log_detection("alert", alert)
        
        return alerts
    
    def generate_alert(self,
                      alert_type: str,
                      details: Dict[str, Any],
                      timestamp: datetime) -> Dict[str, Any]:
        """Gera um alerta baseado nas regras."""
        alert = {
            "type": alert_type,
            "timestamp": timestamp.isoformat(),
            "details": details,
            "severity": details.get("severity", "medium"),
            "status": "new",
            "action_required": True
        }
        
        logger.log_alert(alert_type, alert["severity"], details)
        return alert
    
    def update_metrics(self,
                      metrics: Dict[str, Any],
                      detection: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza métricas com base na detecção."""
        # Atualizar contagem de pessoas
        metrics["total_accesses"] = metrics.get("total_accesses", 0) + 1
        
        # Atualizar acessos autorizados/não autorizados
        if detection.get("authorized", False):
            metrics["authorized_accesses"] = metrics.get("authorized_accesses", 0) + 1
        else:
            metrics["unauthorized_accesses"] = metrics.get("unauthorized_accesses", 0) + 1
        
        # Atualizar atividades suspeitas
        if "activity_type" in detection:
            metrics["suspicious_activities"] = metrics.get("suspicious_activities", {})
            activity_type = detection["activity_type"]
            metrics["suspicious_activities"][activity_type] = \
                metrics["suspicious_activities"].get(activity_type, 0) + 1
        
        # Atualizar acessos por área
        if "area" in detection:
            metrics["area_accesses"] = metrics.get("area_accesses", {})
            area = detection["area"]
            metrics["area_accesses"][area] = metrics["area_accesses"].get(area, 0) + 1
        
        logger.log_metric("security_metrics", metrics)
        return metrics
    
    def add_authorized_person(self, person_id: str) -> None:
        """Adiciona uma pessoa à lista de autorizados."""
        self.authorized_persons.add(person_id)
        logger.log_metric("authorized_persons", len(self.authorized_persons))
    
    def add_authorized_vehicle(self, vehicle_plate: str) -> None:
        """Adiciona um veículo à lista de autorizados."""
        self.authorized_vehicles.add(vehicle_plate)
        logger.log_metric("authorized_vehicles", len(self.authorized_vehicles))
    
    def remove_authorized_person(self, person_id: str) -> None:
        """Remove uma pessoa da lista de autorizados."""
        self.authorized_persons.discard(person_id)
        logger.log_metric("authorized_persons", len(self.authorized_persons))
    
    def remove_authorized_vehicle(self, vehicle_plate: str) -> None:
        """Remove um veículo da lista de autorizados."""
        self.authorized_vehicles.discard(vehicle_plate)
        logger.log_metric("authorized_vehicles", len(self.authorized_vehicles)) 