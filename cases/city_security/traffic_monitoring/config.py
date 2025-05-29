"""
Configuração para monitoramento de tráfego em cidades.
Este módulo contém configurações específicas para detecção e análise de tráfego.
"""

TRAFFIC_CONFIG = {
    "model_config": {
        "model_name": "yolo11x.pt",  # Modelo mais preciso para detecção de veículos
        "conf_threshold": 0.5,
        "classes": [2, 3, 5, 7],  # car, motorcycle, bus, truck
        "img_size": 1280,
        "process_every_n_frames": 1,
        "tracking": {
            "enabled": True,
            "type": "centroid",
            "max_distance": 100,  # Maior distância para veículos em movimento
            "min_confidence": 0.4,
            "max_age": 30,
            "min_hits": 3
        },
        "analysis": {
            "enabled": True,
            "type": "traffic",
            "parameters": {
                "count_lines": [
                    {"start": (0, 0.5), "end": (1, 0.5)},  # Linha horizontal no meio
                    {"start": (0.5, 0), "end": (0.5, 1)}   # Linha vertical no meio
                ],
                "speed_estimation": True,
                "congestion_threshold": 10,  # Número de veículos para considerar congestionamento
                "vehicle_types": {
                    "car": {"weight": 1},
                    "motorcycle": {"weight": 0.5},
                    "bus": {"weight": 2},
                    "truck": {"weight": 2}
                }
            }
        }
    },
    "rtsp_config": {
        "timeout": 60000000,  # Timeout maior para streams de tráfego
        "buffer_size": 4096,  # Buffer maior para streams de tráfego
        "reconnect_attempts": 5,
        "reconnect_delay": 3,
        "drop_frames": True,  # Descartar frames em caso de atraso
        "max_queue_size": 5
    }
}

# Configurações específicas para diferentes tipos de câmeras
CAMERA_CONFIGS = {
    "intersection": {
        "model_config": {
            "classes": [2, 3, 5, 7, 9, 11],  # Adiciona semáforos e placas de stop
            "analysis": {
                "type": "traffic",
                "parameters": {
                    "count_lines": [
                        {"start": (0, 0.5), "end": (1, 0.5)},
                        {"start": (0.5, 0), "end": (0.5, 1)}
                    ],
                    "traffic_light_detection": True,
                    "red_light_violation": True
                }
            }
        }
    },
    "highway": {
        "model_config": {
            "classes": [2, 3, 5, 7],  # Apenas veículos
            "analysis": {
                "type": "traffic",
                "parameters": {
                    "count_lines": [
                        {"start": (0, 0.5), "end": (1, 0.5)}
                    ],
                    "speed_estimation": True,
                    "lane_detection": True
                }
            }
        }
    },
    "parking": {
        "model_config": {
            "classes": [2, 3, 5, 7],  # Veículos
            "analysis": {
                "type": "parking",
                "parameters": {
                    "parking_spots": [
                        {"x1": 0.1, "y1": 0.1, "x2": 0.3, "y2": 0.3},
                        {"x1": 0.4, "y1": 0.1, "x2": 0.6, "y2": 0.3},
                        # Adicionar mais vagas conforme necessário
                    ],
                    "occupancy_threshold": 0.7
                }
            }
        }
    }
}

# Configurações de alertas
ALERT_CONFIG = {
    "congestion": {
        "enabled": True,
        "threshold": 10,  # Número de veículos
        "duration": 300,  # Segundos
        "notification": {
            "type": "email",
            "recipients": ["traffic@city.gov"],
            "template": "congestion_alert.html"
        }
    },
    "accident": {
        "enabled": True,
        "detection": {
            "motion_threshold": 0.8,
            "stopped_vehicles": 2,
            "duration": 60
        },
        "notification": {
            "type": "sms",
            "recipients": ["emergency@city.gov"],
            "template": "accident_alert.txt"
        }
    },
    "speeding": {
        "enabled": True,
        "speed_limit": 60,  # km/h
        "threshold": 1.2,   # 20% acima do limite
        "notification": {
            "type": "log",
            "file": "speeding_violations.log"
        }
    }
}

# Configurações de exportação de dados
EXPORT_CONFIG = {
    "traffic_data": {
        "format": "json",
        "interval": 300,  # 5 minutos
        "fields": [
            "timestamp",
            "vehicle_count",
            "vehicle_types",
            "average_speed",
            "congestion_level"
        ],
        "destination": "traffic_data/"
    },
    "violations": {
        "format": "csv",
        "interval": 60,  # 1 minuto
        "fields": [
            "timestamp",
            "violation_type",
            "vehicle_type",
            "confidence",
            "location"
        ],
        "destination": "violations/"
    }
} 