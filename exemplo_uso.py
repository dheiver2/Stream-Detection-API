#!/usr/bin/env python3
"""
Exemplo de uso da API de Detecção de Pessoas em Streams RTSP
Este script demonstra como usar a API para detectar pessoas em câmeras RTSP.
"""

import requests
import json
import time
import os
import shutil
from typing import List, Dict
from datetime import datetime

# Configuração da API
API_BASE_URL = "http://localhost:8000"

class RTSPDetectorClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
    
    def start_detection(self, streams: List[Dict]) -> Dict:
        """Inicia a detecção em um ou mais streams."""
        url = f"{self.base_url}/start-detection"
        response = requests.post(url, json=streams)
        response.raise_for_status()
        return response.json()
    
    def get_status(self) -> Dict:
        """Obtém o status de todos os streams."""
        url = f"{self.base_url}/status"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_stream_status(self, stream_id: str) -> Dict:
        """Obtém o status de um stream específico."""
        url = f"{self.base_url}/status/{stream_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_detections(self, stream_id: str) -> Dict:
        """Obtém as detecções de um stream específico."""
        url = f"{self.base_url}/detections/{stream_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def stop_stream(self, stream_id: str) -> Dict:
        """Para um stream específico."""
        url = f"{self.base_url}/stop/{stream_id}"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()
    
    def stop_all_streams(self) -> Dict:
        """Para todos os streams."""
        url = f"{self.base_url}/stop-all"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()
    
    def download_frame(self, stream_id: str, filename: str, save_path: str = None):
        """Baixa um frame específico."""
        url = f"{self.base_url}/download/{stream_id}/{filename}"
        response = requests.get(url)
        response.raise_for_status()
        
        if save_path is None:
            save_path = filename
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Frame salvo em: {save_path}")

def setup_detection_directories(streams):
    """Configura e limpa os diretórios de detecção para cada stream."""
    base_dir = "./detections"
    os.makedirs(base_dir, exist_ok=True)
    
    # Criar arquivo de metadados
    metadata_file = os.path.join(base_dir, "metadata.json")
    metadata = {
        "created_at": datetime.now().isoformat(),
        "streams": {}
    }
    
    for stream in streams:
        stream_id = stream["stream_id"]
        stream_dir = os.path.join(base_dir, stream_id)
        
        # Criar estrutura de diretórios
        dirs = {
            "frames": os.path.join(stream_dir, "frames"),  # Frames com detecções
            "events": os.path.join(stream_dir, "events"),  # Eventos importantes
            "logs": os.path.join(stream_dir, "logs"),      # Logs de detecção
            "temp": os.path.join(stream_dir, "temp")       # Arquivos temporários
        }
        
        # Criar diretórios
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Limpar diretório temp se existir
        if os.path.exists(dirs["temp"]):
            shutil.rmtree(dirs["temp"])
        os.makedirs(dirs["temp"])
        
        # Atualizar metadados
        metadata["streams"][stream_id] = {
            "url": stream["url"],
            "created_at": datetime.now().isoformat(),
            "directories": dirs,
            "model_config": stream["model_config"],
            "rtsp_config": stream["rtsp_config"]
        }
    
    # Salvar metadados
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return base_dir

def exemplo_basico():
    """Exemplo básico de uso da API."""
    print("=== Exemplo Básico de Uso da API ===")
    
    # Inicializar cliente
    client = RTSPDetectorClient()
    
    # Configurar streams com diferentes modelos e configurações
    streams = [
        {
            "url": "rtsp://apoio:apoio5971@206.42.30.104:4501/cam/realmonitor?channel=4&subtype=0",
            "stream_id": "camera_01",
            "output_dir": "./detections/camera_01",
            "model_config": {
                "model_name": "yolov8n.pt",  # Modelo nano
                "conf_threshold": 0.5,
                "classes": [0],  # Apenas pessoas
                "img_size": 640,
                "process_every_n_frames": 2  # Processar a cada 2 frames
            },
            "rtsp_config": {
                "timeout": 30000000,
                "buffer_size": 2048,
                "reconnect_attempts": 5,
                "reconnect_delay": 3
            }
        },
        {
            "url": "rtsp://apoio:apoio5971@206.42.30.104:4501/cam/realmonitor?channel=13&subtype=0",
            "stream_id": "camera_02",
            "output_dir": "./detections/camera_02",
            "model_config": {
                "model_name": "yolov8n.pt",  # Modelo nano
                "conf_threshold": 0.6,
                "classes": [0, 2, 3, 5, 7],  # Pessoas, carros, motos, ônibus, caminhões
                "img_size": 640,
                "process_every_n_frames": 1  # Processar todos os frames
            },
            "rtsp_config": {
                "timeout": 60000000,  # Timeout maior
                "buffer_size": 4096,  # Buffer maior
                "reconnect_attempts": 3,
                "reconnect_delay": 5
            }
        }
    ]
    
    try:
        # 1. Iniciar detecção
        print("1. Iniciando detecção...")
        result = client.start_detection(streams)
        print(f"✓ Detecção iniciada: {result}")
        
        # 2. Aguardar um pouco para inicialização
        print("\n2. Aguardando inicialização...")
        time.sleep(5)
        
        # 3. Verificar status geral
        print("\n3. Verificando status geral...")
        status = client.get_status()
        print(f"✓ Status geral: {json.dumps(status, indent=2)}")
        
        # 4. Monitorar por 30 segundos
        print("\n4. Monitorando detecções por 30 segundos...")
        for i in range(6):  # 6 x 5 segundos = 30 segundos
            time.sleep(5)
            
            for stream_config in streams:
                stream_id = stream_config["stream_id"]
                try:
                    stream_status = client.get_stream_status(stream_id)
                    model_info = stream_config["model_config"]
                    print(f"\n   {stream_id}:")
                    print(f"   Status: {stream_status['status']}")
                    print(f"   Modelo: {model_info['model_name']}")
                    print(f"   Pessoas detectadas: {stream_status['people_detected']}")
                    print(f"   Última detecção: {stream_status.get('last_detection', 'Nenhuma')}")
                except requests.exceptions.HTTPError:
                    print(f"   {stream_id}: Sem dados ainda")
        
        # 5. Obter detecções detalhadas
        print("\n5. Obtendo detecções detalhadas...")
        for stream_config in streams:
            stream_id = stream_config["stream_id"]
            try:
                detections = client.get_detections(stream_id)
                print(f"\n   Detecções para {stream_id}:")
                print(f"   Total: {detections['total_detections']}")
                
                for detection in detections['detections'][-3:]:  # Últimas 3 detecções
                    print(f"     - Pessoa ID {detection['person_id']}: "
                          f"Confiança {detection['confidence']:.2f} "
                          f"em {detection['timestamp']}")
                          
            except requests.exceptions.HTTPError:
                print(f"   Nenhuma detecção encontrada para {stream_id}")
        
        # 6. Parar streams
        print("\n6. Parando todos os streams...")
        result = client.stop_all_streams()
        print(f"✓ Streams parados: {result}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")

def exemplo_monitoramento():
    """Exemplo de monitoramento contínuo com configurações personalizadas."""
    print("=== Exemplo de Monitoramento Contínuo ===")
    print("Status da conexão e detecção:")
    print("-" * 50)
    
    client = RTSPDetectorClient()
    
    # Stream com configurações otimizadas para monitoramento
    streams = [
        {
            "url": "rtsp://apoio:apoio5971@206.42.30.104:4501/cam/realmonitor?channel=4&subtype=0",  # URL da camera_01
            "stream_id": "monitor_principal",
            "model_config": {
                "model_name": "yolov8n.pt",  # Modelo nano
                "conf_threshold": 0.4,  # Mais sensível
                "classes": [0],  # Apenas pessoas
                "img_size": 480,  # Resolução menor para performance
                "process_every_n_frames": 3,  # Processar a cada 3 frames
                "save_config": {  # Configuração de salvamento
                    "save_all_frames": False,  # Não salvar todos os frames
                    "save_detections": True,   # Salvar frames com detecções
                    "save_events": True,       # Salvar eventos importantes
                    "max_frames_per_day": 1000,  # Limite de frames por dia
                    "compression_quality": 85,   # Qualidade da compressão JPEG
                    "max_storage_days": 7        # Manter por 7 dias
                }
            },
            "rtsp_config": {
                "timeout": 30000000,
                "buffer_size": 1024,
                "reconnect_attempts": 10,  # Mais tentativas de reconexão
                "reconnect_delay": 2  # Delay menor entre tentativas
            }
        }
    ]
    
    try:
        # Configurar diretórios de detecção
        print("1. Configurando diretórios de detecção...")
        base_dir = setup_detection_directories(streams)
        print(f"✓ Diretórios configurados em: {base_dir}")
        
        # Atualizar output_dir nos streams
        for stream in streams:
            stream["output_dir"] = os.path.join(base_dir, stream["stream_id"])
        
        # Iniciar detecção
        print("\n2. Iniciando conexão com a câmera...")
        result = client.start_detection(streams)
        print(f"✓ Conexão iniciada: {result['message']}")
        print(f"✓ ID da tarefa: {result['task_id']}")
        
        # Aguardar inicialização
        print("\n3. Aguardando inicialização do stream (5 segundos)...")
        time.sleep(5)
        
        # Monitoramento contínuo
        print("\n4. Iniciando monitoramento contínuo")
        print("Pressione Ctrl+C para parar o monitoramento")
        print("-" * 50)
        
        last_status = None
        consecutive_errors = 0
        last_cleanup = time.time()
        
        while True:
            try:
                # Verificar necessidade de limpeza de arquivos antigos
                if time.time() - last_cleanup > 3600:  # A cada hora
                    for stream in streams:
                        stream_dir = stream["output_dir"]
                        cleanup_old_files(stream_dir, stream["model_config"]["save_config"]["max_storage_days"])
                    last_cleanup = time.time()
                
                stream_status = client.get_stream_status("monitor_principal")
                current_status = stream_status['status']
                
                # Verificar mudança de status
                if current_status != last_status:
                    print(f"\n[{time.strftime('%H:%M:%S')}] Status do Stream: {current_status}")
                    if current_status == "running":
                        print("✓ Stream conectado e processando frames")
                    elif current_status == "connecting":
                        print("⏳ Tentando conectar ao stream...")
                    elif current_status == "error":
                        print("❌ Erro na conexão do stream")
                    elif current_status == "stopped":
                        print("⏹ Stream parado")
                    last_status = current_status
                
                # Verificar detecções
                if current_status == "running":
                    detections = stream_status.get('detections', {})
                    people_detected = detections.get('person', 0)  # Usar 'person' em vez de 'people_detected'
                    last_detection = stream_status.get('last_detection', 'Nenhuma')
                    fps = stream_status.get('performance_metrics', {}).get('fps', 0)
                    
                    print(f"\n[{time.strftime('%H:%M:%S')}] Status da Detecção:")
                    print(f"✓ Pessoas detectadas: {people_detected}")
                    print(f"✓ Última detecção: {last_detection}")
                    print(f"✓ FPS atual: {fps:.1f}")
                    
                    # Verificar performance
                    if fps < 1.0:
                        print("⚠️ Performance baixa: FPS muito baixo")
                    elif fps > 0 and fps < 5.0:
                        print("⚠️ Performance moderada: FPS abaixo do ideal")
                    
                    consecutive_errors = 0  # Resetar contador de erros
                else:
                    consecutive_errors += 1
                    if consecutive_errors > 3:
                        print("\n⚠️ Possíveis problemas:")
                        print("1. Verifique se a URL da câmera está correta")
                        print("2. Verifique se a câmera está online")
                        print("3. Verifique se as credenciais estão corretas")
                        print("4. Verifique sua conexão com a internet")
                        print("5. Verifique se a porta está acessível")
                        consecutive_errors = 0  # Resetar após mostrar mensagem
                
                time.sleep(10)  # Verificar a cada 10 segundos
                
            except KeyboardInterrupt:
                print("\nParando monitoramento...")
                break
            except requests.exceptions.HTTPError as e:
                print(f"\n❌ Erro na requisição: {e}")
                print("Verificando novamente em 5 segundos...")
                time.sleep(5)
            except requests.exceptions.ConnectionError:
                print("\n❌ Erro de conexão com a API")
                print("Verifique se a API está rodando em http://localhost:8000")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                print("Tentando novamente em 5 segundos...")
                time.sleep(5)
        
        # Parar stream
        print("\n5. Finalizando monitoramento...")
        client.stop_stream("monitor_principal")
        print("✓ Monitoramento finalizado com sucesso")
        
    except Exception as e:
        print(f"\n❌ Erro fatal no monitoramento: {e}")
        print("Verifique se:")
        print("1. A API está rodando (http://localhost:8000)")
        print("2. O modelo YOLO está disponível (yolov8n.pt)")
        print("3. As credenciais da câmera estão corretas")
        print("4. A URL da câmera está acessível")

def cleanup_old_files(directory, max_days):
    """Remove arquivos mais antigos que max_days."""
    try:
        current_time = time.time()
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_time = os.path.getmtime(file_path)
                if (current_time - file_time) > (max_days * 86400):  # Converter dias para segundos
                    os.remove(file_path)
    except Exception as e:
        print(f"Erro ao limpar arquivos antigos: {e}")

def exemplo_teste_api():
    """Testa se a API está funcionando."""
    print("=== Teste de Conectividade da API ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✓ API está funcionando!")
            print(f"Resposta: {response.json()}")
        else:
            print(f"❌ API retornou status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API")
        print("Certifique-se de que a API está rodando em http://localhost:8000")
    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    """Função principal com menu de opções."""
    print("Sistema de Detecção de Pessoas em Streams RTSP")
    print("=" * 50)
    
    while True:
        print("\nOpções disponíveis:")
        print("1. Testar conectividade da API")
        print("2. Executar exemplo básico")
        print("3. Executar monitoramento contínuo")
        print("4. Sair")
        
        try:
            opcao = input("\nEscolha uma opção (1-4): ").strip()
            
            if opcao == "1":
                exemplo_teste_api()
            elif opcao == "2":
                exemplo_basico()
            elif opcao == "3":
                exemplo_monitoramento()
            elif opcao == "4":
                print("Saindo...")
                break
            else:
                print("Opção inválida. Escolha entre 1-4.")
                
        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    main()
