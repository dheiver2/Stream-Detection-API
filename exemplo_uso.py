#!/usr/bin/env python3
"""
Exemplo de uso da API de Detecção de Pessoas em Streams RTSP
Este script demonstra como usar a API para detectar pessoas em câmeras RTSP.
"""

import requests
import json
import time
from typing import List, Dict

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

def exemplo_basico():
    """Exemplo básico de uso da API."""
    print("=== Exemplo Básico de Uso da API ===")
    
    # Inicializar cliente
    client = RTSPDetectorClient()
    
    # Configurar streams (substitua pelas suas URLs RTSP reais)
    streams = [
        {
            "url": "rtsp://apoio:apoio5971@206.42.30.104:4501/cam/realmonitor?channel=4&subtype=0",
            "stream_id": "camera_01",
            "output_dir": "./detections/camera_01"
        },
        {
            "url": "rtsp://apoio:apoio5971@206.42.30.104:4501/cam/realmonitor?channel=13&subtype=0",
            "stream_id": "camera_02",
            "output_dir": "./detections/camera_02"
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
                    print(f"   {stream_id}: {stream_status['status']} - "
                          f"Pessoas detectadas: {stream_status['people_detected']}")
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
    """Exemplo de monitoramento contínuo."""
    print("=== Exemplo de Monitoramento Contínuo ===")
    
    client = RTSPDetectorClient()
    
    # Stream único para teste
    streams = [
        {
            "url": "rtsp://usuario:senha@ip:porta/path",  # Substitua pela sua URL
            "stream_id": "monitor_principal",
            "output_dir": "./detections/monitor"
        }
    ]
    
    try:
        # Iniciar detecção
        print("Iniciando monitoramento...")
        client.start_detection(streams)
        
        # Monitoramento contínuo
        print("Pressione Ctrl+C para parar o monitoramento")
        while True:
            try:
                stream_status = client.get_stream_status("monitor_principal")
                print(f"[{time.strftime('%H:%M:%S')}] Status: {stream_status['status']} - "
                      f"Pessoas: {stream_status['people_detected']} - "
                      f"Última detecção: {stream_status.get('last_detection', 'Nenhuma')}")
                
                time.sleep(10)  # Verificar a cada 10 segundos
                
            except KeyboardInterrupt:
                print("\nParando monitoramento...")
                break
            except requests.exceptions.HTTPError:
                print(f"[{time.strftime('%H:%M:%S')}] Stream ainda não iniciado...")
                time.sleep(5)
        
        # Parar stream
        client.stop_stream("monitor_principal")
        print("Monitoramento finalizado.")
        
    except Exception as e:
        print(f"Erro no monitoramento: {e}")

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
