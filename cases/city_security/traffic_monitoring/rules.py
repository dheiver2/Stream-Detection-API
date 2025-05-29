"""
Regras de detecção e alertas para monitoramento de tráfego.
Este módulo contém as regras específicas para detecção de violações e geração de alertas.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import get_case_config
from config.logging_config import CaseLogger

logger = CaseLogger("traffic_monitoring")
CASE_CONFIG = get_case_config("traffic_monitoring")

class TrafficRules:
    """Regras para monitoramento de tráfego."""
    
    def __init__(self):
        self.speed_threshold = CASE_CONFIG.get("speed_threshold", 60)
        self.min_confidence = CASE_CONFIG.get("min_confidence", 0.5)
        self.violation_types = CASE_CONFIG.get("violation_types", [])
    
    def check_speed_violation(self, speed: float, vehicle_type: str) -> Optional[Dict[str, Any]]:
        """Verifica violação de velocidade."""
        if speed > self.speed_threshold:
            return {
                "type": "speed_violation",
                "speed": speed,
                "threshold": self.speed_threshold,
                "vehicle_type": vehicle_type,
                "severity": "high" if speed > self.speed_threshold * 1.5 else "medium"
            }
        return None
    
    def check_red_light_violation(self, 
                                traffic_light_state: str,
                                vehicle_moving: bool,
                                confidence: float) -> Optional[Dict[str, Any]]:
        """Verifica violação de semáforo vermelho."""
        if (traffic_light_state == "red" and 
            vehicle_moving and 
            confidence >= self.min_confidence):
            return {
                "type": "red_light_violation",
                "traffic_light_state": traffic_light_state,
                "confidence": confidence,
                "severity": "high"
            }
        return None
    
    def check_wrong_way_violation(self,
                                direction: str,
                                expected_direction: str,
                                confidence: float) -> Optional[Dict[str, Any]]:
        """Verifica violação de direção proibida."""
        if (direction != expected_direction and 
            confidence >= self.min_confidence):
            return {
                "type": "wrong_way_violation",
                "direction": direction,
                "expected_direction": expected_direction,
                "confidence": confidence,
                "severity": "high"
            }
        return None
    
    def check_congestion(self,
                        vehicle_count: int,
                        average_speed: float,
                        area: str) -> Optional[Dict[str, Any]]:
        """Verifica condições de congestionamento."""
        if vehicle_count > 10 and average_speed < 20:
            severity = "high" if average_speed < 10 else "medium"
            return {
                "type": "congestion",
                "vehicle_count": vehicle_count,
                "average_speed": average_speed,
                "area": area,
                "severity": severity
            }
        return None
    
    def process_detection(self, detection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processa uma detecção e retorna violações encontradas."""
        violations = []
        
        # Verificar velocidade
        if "speed" in detection:
            speed_violation = self.check_speed_violation(
                detection["speed"],
                detection.get("vehicle_type", "unknown")
            )
            if speed_violation:
                violations.append(speed_violation)
        
        # Verificar semáforo
        if "traffic_light_state" in detection:
            red_light_violation = self.check_red_light_violation(
                detection["traffic_light_state"],
                detection.get("vehicle_moving", False),
                detection.get("confidence", 0.0)
            )
            if red_light_violation:
                violations.append(red_light_violation)
        
        # Verificar direção
        if "direction" in detection:
            wrong_way_violation = self.check_wrong_way_violation(
                detection["direction"],
                detection.get("expected_direction", "unknown"),
                detection.get("confidence", 0.0)
            )
            if wrong_way_violation:
                violations.append(wrong_way_violation)
        
        # Registrar violações
        for violation in violations:
            logger.log_detection("violation", violation)
        
        return violations
    
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
            "status": "new"
        }
        
        logger.log_alert(alert_type, alert["severity"], details)
        return alert
    
    def update_metrics(self, 
                      metrics: Dict[str, Any],
                      detection: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza métricas com base na detecção."""
        # Atualizar contagem de veículos
        vehicle_type = detection.get("vehicle_type", "unknown")
        metrics["vehicle_count"] = metrics.get("vehicle_count", 0) + 1
        metrics["vehicle_types"] = metrics.get("vehicle_types", {})
        metrics["vehicle_types"][vehicle_type] = metrics["vehicle_types"].get(vehicle_type, 0) + 1
        
        # Atualizar velocidade média
        if "speed" in detection:
            current_avg = metrics.get("average_speed", 0)
            count = metrics.get("speed_count", 0)
            metrics["average_speed"] = (current_avg * count + detection["speed"]) / (count + 1)
            metrics["speed_count"] = count + 1
        
        # Atualizar violações
        if "violations" in detection:
            metrics["violations"] = metrics.get("violations", {})
            for violation in detection["violations"]:
                v_type = violation["type"]
                metrics["violations"][v_type] = metrics["violations"].get(v_type, 0) + 1
        
        logger.log_metric("traffic_metrics", metrics)
        return metrics 