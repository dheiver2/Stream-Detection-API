"""
Configuração para monitoramento de segurança em condomínios.
Este módulo contém configurações específicas para detecção e análise de segurança.
"""

SECURITY_CONFIG = {
    "model_config": {
        "model_name": "yolo11x.pt",  # Modelo mais preciso para detecção de pessoas e objetos
        "conf_threshold": 0.5,
        "classes": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79],  # Todas as classes do YOLO
        "img_size": 1280,
        "process_every_n_frames": 1,
        "tracking": {
            "enabled": True,
            "type": "centroid",
            "max_distance": 50,
            "min_confidence": 0.4,
            "max_age": 30,
            "min_hits": 3
        },
        "analysis": {
            "enabled": True,
            "type": "security",
            "parameters": {
                "restricted_areas": [
                    {
                        "name": "entrada_principal",
                        "polygon": [(0.1, 0.1), (0.9, 0.1), (0.9, 0.3), (0.1, 0.3)],
                        "allowed_classes": [0],  # Apenas pessoas
                        "max_people": 5
                    },
                    {
                        "name": "estacionamento",
                        "polygon": [(0.1, 0.4), (0.9, 0.4), (0.9, 0.9), (0.1, 0.9)],
                        "allowed_classes": [0, 2, 3, 5, 7],  # Pessoas e veículos
                        "max_vehicles": 50
                    }
                ],
                "suspicious_behavior": {
                    "loitering": {
                        "enabled": True,
                        "threshold": 300,  # 5 minutos
                        "min_confidence": 0.6
                    },
                    "crowding": {
                        "enabled": True,
                        "threshold": 10,  # Número de pessoas
                        "min_confidence": 0.6
                    },
                    "unauthorized_access": {
                        "enabled": True,
                        "restricted_areas": ["entrada_servico", "area_tecnica"],
                        "min_confidence": 0.7
                    }
                }
            }
        }
    },
    "rtsp_config": {
        "timeout": 30000000,  # 30 segundos
        "buffer_size": 4096,
        "reconnect_attempts": 5,
        "reconnect_delay": 3,
        "drop_frames": True,
        "max_queue_size": 5
    }
}

# Configurações específicas para diferentes tipos de câmeras
CAMERA_CONFIGS = {
    "entrada": {
        "model_config": {
            "classes": [0, 2, 3, 5, 7],  # Pessoas e veículos
            "analysis": {
                "type": "security",
                "parameters": {
                    "restricted_areas": [
                        {
                            "name": "portaria",
                            "polygon": [(0.1, 0.1), (0.9, 0.1), (0.9, 0.3), (0.1, 0.3)],
                            "allowed_classes": [0],
                            "max_people": 3
                        }
                    ],
                    "access_control": {
                        "enabled": True,
                        "track_entries": True,
                        "track_exits": True,
                        "generate_reports": True
                    }
                }
            }
        }
    },
    "estacionamento": {
        "model_config": {
            "classes": [0, 2, 3, 5, 7],  # Pessoas e veículos
            "analysis": {
                "type": "security",
                "parameters": {
                    "parking_monitoring": {
                        "enabled": True,
                        "detect_unauthorized_vehicles": True,
                        "track_vehicle_movement": True
                    },
                    "suspicious_behavior": {
                        "loitering": {
                            "enabled": True,
                            "threshold": 180  # 3 minutos
                        }
                    }
                }
            }
        }
    },
    "areas_comuns": {
        "model_config": {
            "classes": [0],  # Apenas pessoas
            "analysis": {
                "type": "security",
                "parameters": {
                    "crowd_monitoring": {
                        "enabled": True,
                        "max_people": 20,
                        "alert_threshold": 15
                    },
                    "suspicious_behavior": {
                        "loitering": {
                            "enabled": True,
                            "threshold": 600  # 10 minutos
                        },
                        "crowding": {
                            "enabled": True,
                            "threshold": 10
                        }
                    }
                }
            }
        }
    }
}

# Configurações de alertas
ALERT_CONFIG = {
    "unauthorized_access": {
        "enabled": True,
        "notification": {
            "type": "email",
            "recipients": ["security@condominio.com"],
            "template": "unauthorized_access_alert.html"
        }
    },
    "suspicious_behavior": {
        "enabled": True,
        "notification": {
            "type": "sms",
            "recipients": ["security@condominio.com"],
            "template": "suspicious_behavior_alert.txt"
        }
    },
    "crowding": {
        "enabled": True,
        "notification": {
            "type": "email",
            "recipients": ["security@condominio.com"],
            "template": "crowding_alert.html"
        }
    }
}

# Configurações de exportação de dados
EXPORT_CONFIG = {
    "access_logs": {
        "enabled": True,
        "format": "json",
        "interval": 300,  # 5 minutos
        "fields": [
            "timestamp",
            "camera_id",
            "event_type",
            "object_type",
            "confidence",
            "location"
        ],
        "destination": "logs/access/"
    },
    "security_events": {
        "enabled": True,
        "format": "csv",
        "interval": 60,  # 1 minuto
        "fields": [
            "timestamp",
            "camera_id",
            "event_type",
            "severity",
            "description",
            "location",
            "confidence"
        ],
        "destination": "logs/security/"
    }
}

# Configurações de backup de vídeo
BACKUP_CONFIG = {
    "enabled": True,
    "storage": {
        "type": "local",
        "path": "backup/videos/",
        "retention_days": 30
    },
    "triggers": {
        "motion": {
            "enabled": True,
            "min_duration": 10,  # segundos
            "min_confidence": 0.5
        },
        "alert": {
            "enabled": True,
            "pre_event": 30,  # segundos antes do evento
            "post_event": 60   # segundos depois do evento
        }
    }
} 