"""
Exemplo de uso da API para monitoramento de bares e restaurantes.
Este script demonstra como configurar e usar a API para análise de clientes e operações.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, List, Optional
import schedule
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import pdfkit

from config import RESTAURANT_CONFIG, CAMERA_CONFIGS, ALERT_CONFIG, EXPORT_CONFIG, REPORT_CONFIG

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restaurant_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RestaurantMonitoring:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.active_streams: Dict[str, dict] = {}
        self.metrics_history: Dict[str, List[dict]] = {
            "customer_metrics": [],
            "staff_metrics": [],
            "business_analytics": []
        }
        
    def start_entrance_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento da entrada."""
        try:
            config = RESTAURANT_CONFIG.copy()
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
    
    def start_dining_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento do salão."""
        try:
            config = RESTAURANT_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["salao"]["model_config"])
            
            stream_config = {
                "url": rtsp_url,
                "stream_id": stream_id,
                "model_config": config["model_config"],
                "rtsp_config": config["rtsp_config"],
                "output_dir": f"output/dining/{stream_id}"
            }
            
            response = requests.post(
                f"{self.api_url}/start-detection",
                json=stream_config
            )
            
            if response.status_code == 200:
                self.active_streams[stream_id] = {
                    "type": "dining",
                    "config": stream_config,
                    "start_time": datetime.now()
                }
                logger.info(f"Monitoramento iniciado para salão {stream_id}")
                return True
            else:
                logger.error(f"Erro ao iniciar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento de salão: {str(e)}")
            return False
    
    def start_bar_monitoring(self, stream_id: str, rtsp_url: str) -> bool:
        """Inicia o monitoramento do bar."""
        try:
            config = RESTAURANT_CONFIG.copy()
            config["model_config"].update(CAMERA_CONFIGS["bar"]["model_config"])
            
            stream_config = {
                "url": rtsp_url,
                "stream_id": stream_id,
                "model_config": config["model_config"],
                "rtsp_config": config["rtsp_config"],
                "output_dir": f"output/bar/{stream_id}"
            }
            
            response = requests.post(
                f"{self.api_url}/start-detection",
                json=stream_config
            )
            
            if response.status_code == 200:
                self.active_streams[stream_id] = {
                    "type": "bar",
                    "config": stream_config,
                    "start_time": datetime.now()
                }
                logger.info(f"Monitoramento iniciado para bar {stream_id}")
                return True
            else:
                logger.error(f"Erro ao iniciar monitoramento: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento de bar: {str(e)}")
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
        
        # Verifica tempo de espera
        if ALERT_CONFIG["wait_time"]["enabled"]:
            wait_times = analysis_data.get("wait_times", [])
            if wait_times:
                avg_wait_time = sum(wait_times) / len(wait_times)
                if avg_wait_time >= RESTAURANT_CONFIG["model_config"]["analysis"]["parameters"]["customer_analysis"]["wait_time"]["alert_threshold"]:
                    alerts.append({
                        "type": "wait_time",
                        "stream_id": stream_id,
                        "severity": "high",
                        "message": f"Tempo de espera alto: {avg_wait_time:.1f} segundos",
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Verifica ocupação de mesas
        if ALERT_CONFIG["table_occupancy"]["enabled"] and stream_type == "dining":
            table_times = analysis_data.get("table_times", [])
            if table_times:
                for table_id, time in table_times.items():
                    if time >= RESTAURANT_CONFIG["model_config"]["analysis"]["parameters"]["customer_analysis"]["table_occupancy"]["alert_threshold"]:
                        alerts.append({
                            "type": "table_occupancy",
                            "stream_id": stream_id,
                            "severity": "medium",
                            "message": f"Mesa {table_id} ocupada por muito tempo: {time/60:.1f} minutos",
                            "timestamp": datetime.now().isoformat()
                        })
        
        # Verifica produtividade da equipe
        if ALERT_CONFIG["staff_productivity"]["enabled"]:
            staff_metrics = analysis_data.get("staff_metrics", {})
            for staff_id, metrics in staff_metrics.items():
                if metrics.get("activity_level", 1.0) < RESTAURANT_CONFIG["model_config"]["analysis"]["parameters"]["staff_analysis"]["productivity"]["min_activity_threshold"]:
                    alerts.append({
                        "type": "staff_productivity",
                        "stream_id": stream_id,
                        "severity": "medium",
                        "message": f"Baixa produtividade detectada para funcionário {staff_id}",
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Verifica tamanho da fila
        if ALERT_CONFIG["queue_length"]["enabled"] and stream_type in ["entrance", "bar"]:
            queue_length = analysis_data.get("queue_length", 0)
            if queue_length >= RESTAURANT_CONFIG["model_config"]["analysis"]["parameters"]["customer_analysis"]["queue_analysis"]["alert_threshold"]:
                alerts.append({
                    "type": "queue_length",
                    "stream_id": stream_id,
                    "severity": "high",
                    "message": f"Fila grande detectada: {queue_length} pessoas",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def collect_metrics(self, stream_id: str) -> bool:
        """Coleta métricas do stream."""
        try:
            status = self.get_stream_status(stream_id)
            if not status:
                return False
            
            stream_type = self.active_streams[stream_id]["type"]
            analysis_data = status.get("analysis_data", {})
            timestamp = datetime.now()
            
            # Coleta métricas de clientes
            if EXPORT_CONFIG["customer_metrics"]["enabled"]:
                customer_metrics = {
                    "timestamp": timestamp.isoformat(),
                    "camera_id": stream_id,
                    "area": stream_type,
                    "customer_count": sum(status.get("detection_counts", {}).values()),
                    "wait_time": analysis_data.get("average_wait_time", 0),
                    "queue_length": analysis_data.get("queue_length", 0),
                    "table_occupancy": analysis_data.get("table_occupancy", 0)
                }
                self.metrics_history["customer_metrics"].append(customer_metrics)
            
            # Coleta métricas da equipe
            if EXPORT_CONFIG["staff_metrics"]["enabled"]:
                staff_metrics = {
                    "timestamp": timestamp.isoformat(),
                    "camera_id": stream_id,
                    "area": stream_type,
                    "staff_count": analysis_data.get("staff_count", 0),
                    "activity_level": analysis_data.get("staff_activity", 0),
                    "response_time": analysis_data.get("average_response_time", 0),
                    "table_visits": analysis_data.get("table_visits", 0)
                }
                self.metrics_history["staff_metrics"].append(staff_metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {str(e)}")
            return False
    
    def generate_business_analytics(self) -> bool:
        """Gera análises de negócio a partir das métricas coletadas."""
        try:
            if not self.metrics_history["customer_metrics"] or not self.metrics_history["staff_metrics"]:
                return False
            
            # Converte métricas para DataFrames
            customer_df = pd.DataFrame(self.metrics_history["customer_metrics"])
            staff_df = pd.DataFrame(self.metrics_history["staff_metrics"])
            
            # Calcula métricas de negócio
            analytics = {
                "timestamp": datetime.now().isoformat(),
                "period": "hourly",
                "total_customers": customer_df["customer_count"].sum(),
                "average_wait_time": customer_df["wait_time"].mean(),
                "peak_hours": self._calculate_peak_hours(customer_df),
                "table_turnover": self._calculate_table_turnover(customer_df),
                "staff_efficiency": self._calculate_staff_efficiency(customer_df, staff_df)
            }
            
            self.metrics_history["business_analytics"].append(analytics)
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar análises de negócio: {str(e)}")
            return False
    
    def _calculate_peak_hours(self, customer_df: pd.DataFrame) -> List[dict]:
        """Calcula os horários de pico."""
        try:
            customer_df["hour"] = pd.to_datetime(customer_df["timestamp"]).dt.hour
            hourly_counts = customer_df.groupby("hour")["customer_count"].mean()
            peak_hours = hourly_counts.nlargest(3)
            
            return [
                {"hour": hour, "average_customers": count}
                for hour, count in peak_hours.items()
            ]
        except Exception as e:
            logger.error(f"Erro ao calcular horários de pico: {str(e)}")
            return []
    
    def _calculate_table_turnover(self, customer_df: pd.DataFrame) -> float:
        """Calcula a taxa de rotatividade das mesas."""
        try:
            if "table_occupancy" not in customer_df.columns:
                return 0.0
            
            total_tables = 10  # Número total de mesas (deve ser configurável)
            occupied_tables = customer_df["table_occupancy"].mean()
            return (occupied_tables / total_tables) * 100
        except Exception as e:
            logger.error(f"Erro ao calcular rotatividade de mesas: {str(e)}")
            return 0.0
    
    def _calculate_staff_efficiency(self, customer_df: pd.DataFrame, staff_df: pd.DataFrame) -> float:
        """Calcula a eficiência da equipe."""
        try:
            if "response_time" not in staff_df.columns or "wait_time" not in customer_df.columns:
                return 0.0
            
            avg_response_time = staff_df["response_time"].mean()
            avg_wait_time = customer_df["wait_time"].mean()
            
            if avg_wait_time == 0:
                return 0.0
            
            return (1 - (avg_response_time / avg_wait_time)) * 100
        except Exception as e:
            logger.error(f"Erro ao calcular eficiência da equipe: {str(e)}")
            return 0.0
    
    def export_metrics(self) -> bool:
        """Exporta métricas para os formatos configurados."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Exporta métricas de clientes
            if EXPORT_CONFIG["customer_metrics"]["enabled"] and self.metrics_history["customer_metrics"]:
                output_dir = Path(EXPORT_CONFIG["customer_metrics"]["destination"])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                with open(output_dir / f"customer_metrics_{timestamp}.json", "w") as f:
                    json.dump(self.metrics_history["customer_metrics"], f, indent=2)
            
            # Exporta métricas da equipe
            if EXPORT_CONFIG["staff_metrics"]["enabled"] and self.metrics_history["staff_metrics"]:
                output_dir = Path(EXPORT_CONFIG["staff_metrics"]["destination"])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                df = pd.DataFrame(self.metrics_history["staff_metrics"])
                df.to_csv(output_dir / f"staff_metrics_{timestamp}.csv", index=False)
            
            # Exporta análises de negócio
            if EXPORT_CONFIG["business_analytics"]["enabled"] and self.metrics_history["business_analytics"]:
                output_dir = Path(EXPORT_CONFIG["business_analytics"]["destination"])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                with open(output_dir / f"business_analytics_{timestamp}.json", "w") as f:
                    json.dump(self.metrics_history["business_analytics"], f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar métricas: {str(e)}")
            return False
    
    def generate_report(self, report_type: str = "daily") -> bool:
        """Gera relatório diário ou semanal."""
        try:
            if report_type not in ["daily", "weekly"]:
                return False
            
            report_config = REPORT_CONFIG[f"{report_type}_report"]
            if not report_config["enabled"]:
                return False
            
            # Carrega template
            template_path = Path("templates") / report_config["template"]
            if not template_path.exists():
                logger.error(f"Template não encontrado: {template_path}")
                return False
            
            with open(template_path) as f:
                template = Template(f.read())
            
            # Prepara dados para o relatório
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "report_type": report_type,
                "period": "daily" if report_type == "daily" else "weekly",
                "customer_metrics": self._prepare_customer_metrics(report_type),
                "staff_metrics": self._prepare_staff_metrics(report_type),
                "business_analytics": self._prepare_business_analytics(report_type),
                "alerts_summary": self._prepare_alerts_summary(report_type)
            }
            
            # Gera gráficos
            self._generate_report_charts(report_data)
            
            # Renderiza template
            html_content = template.render(**report_data)
            
            # Converte para PDF
            output_dir = Path("reports") / report_type
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = output_dir / f"{report_type}_report_{timestamp}.pdf"
            
            pdfkit.from_string(html_content, str(pdf_path))
            
            # Envia relatório
            self._send_report(pdf_path, report_config["recipients"])
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {str(e)}")
            return False
    
    def _prepare_customer_metrics(self, report_type: str) -> dict:
        """Prepara métricas de clientes para o relatório."""
        try:
            df = pd.DataFrame(self.metrics_history["customer_metrics"])
            if df.empty:
                return {}
            
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            if report_type == "daily":
                df = df[df["timestamp"].dt.date == datetime.now().date()]
            else:
                df = df[df["timestamp"] >= datetime.now() - timedelta(days=7)]
            
            return {
                "total_customers": df["customer_count"].sum(),
                "average_wait_time": df["wait_time"].mean(),
                "max_queue_length": df["queue_length"].max(),
                "average_table_occupancy": df["table_occupancy"].mean()
            }
        except Exception as e:
            logger.error(f"Erro ao preparar métricas de clientes: {str(e)}")
            return {}
    
    def _prepare_staff_metrics(self, report_type: str) -> dict:
        """Prepara métricas da equipe para o relatório."""
        try:
            df = pd.DataFrame(self.metrics_history["staff_metrics"])
            if df.empty:
                return {}
            
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            if report_type == "daily":
                df = df[df["timestamp"].dt.date == datetime.now().date()]
            else:
                df = df[df["timestamp"] >= datetime.now() - timedelta(days=7)]
            
            return {
                "average_activity_level": df["activity_level"].mean(),
                "average_response_time": df["response_time"].mean(),
                "total_table_visits": df["table_visits"].sum()
            }
        except Exception as e:
            logger.error(f"Erro ao preparar métricas da equipe: {str(e)}")
            return {}
    
    def _prepare_business_analytics(self, report_type: str) -> dict:
        """Prepara análises de negócio para o relatório."""
        try:
            df = pd.DataFrame(self.metrics_history["business_analytics"])
            if df.empty:
                return {}
            
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            if report_type == "daily":
                df = df[df["timestamp"].dt.date == datetime.now().date()]
            else:
                df = df[df["timestamp"] >= datetime.now() - timedelta(days=7)]
            
            return {
                "peak_hours": df["peak_hours"].iloc[-1] if not df.empty else [],
                "table_turnover": df["table_turnover"].mean(),
                "staff_efficiency": df["staff_efficiency"].mean()
            }
        except Exception as e:
            logger.error(f"Erro ao preparar análises de negócio: {str(e)}")
            return {}
    
    def _prepare_alerts_summary(self, report_type: str) -> List[dict]:
        """Prepara resumo de alertas para o relatório."""
        try:
            alerts = []
            for stream_id in self.active_streams:
                stream_alerts = self.check_alerts(stream_id)
                alerts.extend(stream_alerts)
            
            if report_type == "daily":
                alerts = [a for a in alerts if datetime.fromisoformat(a["timestamp"]).date() == datetime.now().date()]
            else:
                alerts = [a for a in alerts if datetime.fromisoformat(a["timestamp"]) >= datetime.now() - timedelta(days=7)]
            
            return alerts
        except Exception as e:
            logger.error(f"Erro ao preparar resumo de alertas: {str(e)}")
            return []
    
    def _generate_report_charts(self, report_data: dict) -> None:
        """Gera gráficos para o relatório."""
        try:
            # Configura estilo dos gráficos
            sns.set_style("whitegrid")
            plt.rcParams["figure.figsize"] = (10, 6)
            
            # Gráfico de clientes por hora
            if report_data["customer_metrics"]:
                df = pd.DataFrame(self.metrics_history["customer_metrics"])
                df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
                hourly_counts = df.groupby("hour")["customer_count"].mean()
                
                plt.figure()
                hourly_counts.plot(kind="bar")
                plt.title("Média de Clientes por Hora")
                plt.xlabel("Hora")
                plt.ylabel("Número de Clientes")
                plt.savefig("reports/charts/customers_by_hour.png")
                plt.close()
            
            # Gráfico de tempo de espera
            if report_data["customer_metrics"]:
                df = pd.DataFrame(self.metrics_history["customer_metrics"])
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                
                plt.figure()
                plt.plot(df["timestamp"], df["wait_time"])
                plt.title("Tempo de Espera ao Longo do Dia")
                plt.xlabel("Horário")
                plt.ylabel("Tempo de Espera (segundos)")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig("reports/charts/wait_time.png")
                plt.close()
            
            # Gráfico de eficiência da equipe
            if report_data["staff_metrics"]:
                df = pd.DataFrame(self.metrics_history["staff_metrics"])
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                
                plt.figure()
                plt.plot(df["timestamp"], df["activity_level"])
                plt.title("Nível de Atividade da Equipe")
                plt.xlabel("Horário")
                plt.ylabel("Nível de Atividade")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig("reports/charts/staff_activity.png")
                plt.close()
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráficos: {str(e)}")
    
    def _send_report(self, report_path: Path, recipients: List[str]) -> bool:
        """Envia relatório por email."""
        try:
            # Aqui você implementaria a lógica de envio de email
            # Por enquanto, apenas logamos a ação
            logger.info(f"Relatório enviado para {recipients}: {report_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar relatório: {str(e)}")
            return False

def main():
    """Função principal com exemplo de uso."""
    # Inicializa o monitoramento
    monitor = RestaurantMonitoring()
    
    # Exemplo de monitoramento de entrada
    entrance_url = "rtsp://camera1.restaurant.com/entrance1"
    if monitor.start_entrance_monitoring("entrance1", entrance_url):
        logger.info("Monitoramento de entrada iniciado com sucesso")
    
    # Exemplo de monitoramento do salão
    dining_url = "rtsp://camera2.restaurant.com/dining1"
    if monitor.start_dining_monitoring("dining1", dining_url):
        logger.info("Monitoramento do salão iniciado com sucesso")
    
    # Exemplo de monitoramento do bar
    bar_url = "rtsp://camera3.restaurant.com/bar1"
    if monitor.start_bar_monitoring("bar1", bar_url):
        logger.info("Monitoramento do bar iniciado com sucesso")
    
    # Agenda geração de relatórios
    schedule.every().day.at(REPORT_CONFIG["daily_report"]["schedule"]).do(
        monitor.generate_report, "daily"
    )
    schedule.every().sunday.at(REPORT_CONFIG["weekly_report"]["schedule"]).do(
        monitor.generate_report, "weekly"
    )
    
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
                
                # Coleta métricas
                monitor.collect_metrics(stream_id)
            
            # Gera análises de negócio periodicamente
            if datetime.now().minute % 60 == 0:  # A cada hora
                monitor.generate_business_analytics()
            
            # Exporta métricas periodicamente
            if datetime.now().second % EXPORT_CONFIG["customer_metrics"]["interval"] == 0:
                monitor.export_metrics()
            
            # Executa tarefas agendadas
            schedule.run_pending()
            
            time.sleep(1)  # Aguarda 1 segundo antes da próxima verificação
            
    except KeyboardInterrupt:
        logger.info("Encerrando monitoramento...")
    finally:
        # Para todos os streams ativos
        for stream_id in list(monitor.active_streams.keys()):
            monitor.stop_monitoring(stream_id)

if __name__ == "__main__":
    main() 