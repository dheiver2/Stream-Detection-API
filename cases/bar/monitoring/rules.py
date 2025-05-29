"""
Regras de detecção e alertas para monitoramento de bares.
Este módulo contém as regras específicas para detecção de comportamentos suspeitos e geração de alertas.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config.settings import get_case_config
from config.logging_config import CaseLogger

logger = CaseLogger("bar_monitoring")
CASE_CONFIG = get_case_config("bar_monitoring")

class BarMonitoringRules:
    """Regras para monitoramento de bares."""
    
    def __init__(self):
        self.min_confidence = CASE_CONFIG.get("min_confidence", 0.6)
        self.max_capacity = CASE_CONFIG.get("max_capacity", 100)
        self.alert_threshold = CASE_CONFIG.get("alert_threshold", 0.8)
        self.restricted_areas = CASE_CONFIG.get("restricted_areas", [])
        self.age_restriction = CASE_CONFIG.get("age_restriction", 18)
        self.max_group_size = CASE_CONFIG.get("max_group_size", 8)
    
    def check_capacity(self,
                      current_count: int,
                      area: str) -> Optional[Dict[str, Any]]:
        """Verifica se a capacidade máxima foi atingida."""
        if current_count >= self.max_capacity:
            return {
                "type": "capacity_exceeded",
                "area": area,
                "current_count": current_count,
                "max_capacity": self.max_capacity,
                "severity": "high"
            }
        elif current_count >= self.max_capacity * 0.9:  # 90% da capacidade
            return {
                "type": "capacity_warning",
                "area": area,
                "current_count": current_count,
                "max_capacity": self.max_capacity,
                "severity": "medium"
            }
        return None
    
    def check_age_restriction(self,
                            estimated_age: int,
                            location: str) -> Optional[Dict[str, Any]]:
        """Verifica restrição de idade."""
        if estimated_age < self.age_restriction:
            return {
                "type": "age_restriction_violation",
                "estimated_age": estimated_age,
                "location": location,
                "severity": "high"
            }
        return None
    
    def check_group_size(self,
                        group_size: int,
                        location: str) -> Optional[Dict[str, Any]]:
        """Verifica tamanho de grupos."""
        if group_size > self.max_group_size:
            return {
                "type": "large_group",
                "group_size": group_size,
                "location": location,
                "severity": "medium"
            }
        return None
    
    def check_restricted_area(self,
                            area: str,
                            person_count: int) -> Optional[Dict[str, Any]]:
        """Verifica acesso a áreas restritas."""
        if area in self.restricted_areas and person_count > 0:
            return {
                "type": "restricted_area_access",
                "area": area,
                "person_count": person_count,
                "severity": "high"
            }
        return None
    
    def check_suspicious_behavior(self,
                                behavior_type: str,
                                location: str,
                                duration: float) -> Optional[Dict[str, Any]]:
        """Verifica comportamentos suspeitos."""
        if behavior_type == "aggression" and duration > 0:
            return {
                "type": "aggression_detected",
                "location": location,
                "duration": duration,
                "severity": "high"
            }
        elif behavior_type == "intoxication" and duration > 300:  # 5 minutos
            return {
                "type": "intoxication_detected",
                "location": location,
                "duration": duration,
                "severity": "medium"
            }
        return None
    
    def process_detection(self, detection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processa uma detecção e retorna alertas encontrados."""
        alerts = []
        timestamp = datetime.fromisoformat(detection.get("timestamp", datetime.utcnow().isoformat()))
        
        # Verificar capacidade
        if "current_count" in detection and "area" in detection:
            capacity_alert = self.check_capacity(
                detection["current_count"],
                detection["area"]
            )
            if capacity_alert:
                alerts.append(capacity_alert)
        
        # Verificar idade
        if "estimated_age" in detection:
            age_alert = self.check_age_restriction(
                detection["estimated_age"],
                detection.get("location", "unknown")
            )
            if age_alert:
                alerts.append(age_alert)
        
        # Verificar tamanho de grupo
        if "group_size" in detection:
            group_alert = self.check_group_size(
                detection["group_size"],
                detection.get("location", "unknown")
            )
            if group_alert:
                alerts.append(group_alert)
        
        # Verificar área restrita
        if "area" in detection:
            area_alert = self.check_restricted_area(
                detection["area"],
                detection.get("person_count", 0)
            )
            if area_alert:
                alerts.append(area_alert)
        
        # Verificar comportamento suspeito
        if "behavior_type" in detection:
            behavior_alert = self.check_suspicious_behavior(
                detection["behavior_type"],
                detection.get("location", "unknown"),
                detection.get("duration", 0.0)
            )
            if behavior_alert:
                alerts.append(behavior_alert)
        
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
        if "current_count" in detection:
            metrics["current_count"] = detection["current_count"]
        
        # Atualizar contagem por área
        if "area" in detection:
            metrics["area_counts"] = metrics.get("area_counts", {})
            area = detection["area"]
            metrics["area_counts"][area] = detection.get("current_count", 0)
        
        # Atualizar comportamentos suspeitos
        if "behavior_type" in detection:
            metrics["suspicious_behaviors"] = metrics.get("suspicious_behaviors", {})
            behavior_type = detection["behavior_type"]
            metrics["suspicious_behaviors"][behavior_type] = \
                metrics["suspicious_behaviors"].get(behavior_type, 0) + 1
        
        # Atualizar violações de idade
        if "estimated_age" in detection and detection["estimated_age"] < self.age_restriction:
            metrics["age_violations"] = metrics.get("age_violations", 0) + 1
        
        # Atualizar grupos grandes
        if "group_size" in detection and detection["group_size"] > self.max_group_size:
            metrics["large_groups"] = metrics.get("large_groups", 0) + 1
        
        logger.log_metric("bar_metrics", metrics)
        return metrics
    
    def update_capacity(self, new_capacity: int) -> None:
        """Atualiza a capacidade máxima do estabelecimento."""
        self.max_capacity = new_capacity
        logger.log_metric("max_capacity", new_capacity)
    
    def update_restricted_areas(self, areas: List[str]) -> None:
        """Atualiza a lista de áreas restritas."""
        self.restricted_areas = areas
        logger.log_metric("restricted_areas", areas)
    
    def update_age_restriction(self, age: int) -> None:
        """Atualiza a restrição de idade."""
        self.age_restriction = age
        logger.log_metric("age_restriction", age)
    
    def update_max_group_size(self, size: int) -> None:
        """Atualiza o tamanho máximo de grupo permitido."""
        self.max_group_size = size
        logger.log_metric("max_group_size", size) 