"""
Configuração para monitoramento de bares e restaurantes.
Este módulo contém configurações específicas para análise de clientes e operações.
"""

RESTAURANT_CONFIG = {
    "model_config": {
        "model_name": "yolov8n.pt",  # Modelo nano para detecção de pessoas e objetos
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
            "type": "restaurant",
            "parameters": {
                "areas": [
                    {
                        "name": "entrada",
                        "polygon": [(0.1, 0.1), (0.9, 0.1), (0.9, 0.3), (0.1, 0.3)],
                        "type": "entrance"
                    },
                    {
                        "name": "mesas",
                        "polygon": [(0.1, 0.4), (0.9, 0.4), (0.9, 0.9), (0.1, 0.9)],
                        "type": "dining"
                    },
                    {
                        "name": "bar",
                        "polygon": [(0.7, 0.1), (0.9, 0.1), (0.9, 0.9), (0.7, 0.9)],
                        "type": "bar"
                    }
                ],
                "customer_analysis": {
                    "wait_time": {
                        "enabled": True,
                        "threshold": 300,  # 5 minutos
                        "alert_threshold": 600  # 10 minutos
                    },
                    "table_occupancy": {
                        "enabled": True,
                        "max_time": 7200,  # 2 horas
                        "alert_threshold": 5400  # 1.5 horas
                    },
                    "queue_analysis": {
                        "enabled": True,
                        "max_queue_length": 10,
                        "alert_threshold": 8
                    }
                },
                "staff_analysis": {
                    "productivity": {
                        "enabled": True,
                        "min_activity_threshold": 0.3,
                        "max_idle_time": 300  # 5 minutos
                    },
                    "service_quality": {
                        "enabled": True,
                        "response_time_threshold": 180,  # 3 minutos
                        "table_visit_frequency": 900  # 15 minutos
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
            "classes": [0],  # Apenas pessoas
            "analysis": {
                "type": "restaurant",
                "parameters": {
                    "customer_analysis": {
                        "wait_time": {
                            "enabled": True,
                            "threshold": 300
                        },
                        "queue_analysis": {
                            "enabled": True,
                            "max_queue_length": 10
                        }
                    }
                }
            }
        }
    },
    "salao": {
        "model_config": {
            "classes": [0],  # Apenas pessoas
            "analysis": {
                "type": "restaurant",
                "parameters": {
                    "table_occupancy": {
                        "enabled": True,
                        "max_time": 7200
                    },
                    "staff_analysis": {
                        "service_quality": {
                            "enabled": True,
                            "response_time_threshold": 180
                        }
                    }
                }
            }
        }
    },
    "bar": {
        "model_config": {
            "classes": [0],  # Apenas pessoas
            "analysis": {
                "type": "restaurant",
                "parameters": {
                    "customer_analysis": {
                        "wait_time": {
                            "enabled": True,
                            "threshold": 180  # 3 minutos
                        },
                        "queue_analysis": {
                            "enabled": True,
                            "max_queue_length": 5
                        }
                    },
                    "staff_analysis": {
                        "productivity": {
                            "enabled": True,
                            "min_activity_threshold": 0.4
                        }
                    }
                }
            }
        }
    }
}

# Configurações de alertas
ALERT_CONFIG = {
    "wait_time": {
        "enabled": True,
        "notification": {
            "type": "email",
            "recipients": ["manager@restaurant.com"],
            "template": "wait_time_alert.html"
        }
    },
    "table_occupancy": {
        "enabled": True,
        "notification": {
            "type": "sms",
            "recipients": ["manager@restaurant.com"],
            "template": "table_occupancy_alert.txt"
        }
    },
    "staff_productivity": {
        "enabled": True,
        "notification": {
            "type": "email",
            "recipients": ["manager@restaurant.com"],
            "template": "staff_productivity_alert.html"
        }
    },
    "queue_length": {
        "enabled": True,
        "notification": {
            "type": "sms",
            "recipients": ["manager@restaurant.com"],
            "template": "queue_length_alert.txt"
        }
    }
}

# Configurações de exportação de dados
EXPORT_CONFIG = {
    "customer_metrics": {
        "enabled": True,
        "format": "json",
        "interval": 300,  # 5 minutos
        "fields": [
            "timestamp",
            "camera_id",
            "area",
            "customer_count",
            "wait_time",
            "queue_length",
            "table_occupancy"
        ],
        "destination": "metrics/customers/"
    },
    "staff_metrics": {
        "enabled": True,
        "format": "csv",
        "interval": 900,  # 15 minutos
        "fields": [
            "timestamp",
            "camera_id",
            "area",
            "staff_count",
            "activity_level",
            "response_time",
            "table_visits"
        ],
        "destination": "metrics/staff/"
    },
    "business_analytics": {
        "enabled": True,
        "format": "json",
        "interval": 3600,  # 1 hora
        "fields": [
            "timestamp",
            "period",
            "total_customers",
            "average_wait_time",
            "peak_hours",
            "table_turnover",
            "staff_efficiency"
        ],
        "destination": "analytics/"
    }
}

# Configurações de relatórios
REPORT_CONFIG = {
    "daily_report": {
        "enabled": True,
        "schedule": "23:00",  # Horário para gerar relatório diário
        "format": "pdf",
        "sections": [
            "customer_metrics",
            "staff_metrics",
            "business_analytics",
            "alerts_summary"
        ],
        "recipients": ["manager@restaurant.com"],
        "template": "daily_report.html"
    },
    "weekly_report": {
        "enabled": True,
        "schedule": "sunday 23:00",
        "format": "pdf",
        "sections": [
            "weekly_trends",
            "staff_performance",
            "customer_satisfaction",
            "business_insights"
        ],
        "recipients": ["owner@restaurant.com", "manager@restaurant.com"],
        "template": "weekly_report.html"
    }
} 