# Sistema de Detecção de Pessoas em Streams RTSP

## 📋 Descrição

Este sistema utiliza **YOLO (You Only Look Once)** e **FastAPI** para detectar pessoas em tempo real através de streams RTSP de câmeras de segurança. O sistema salva automaticamente frames quando pessoas são detectadas e fornece uma API REST completa para gerenciamento e monitoramento.

## 🚀 Características Principais

- **Detecção em Tempo Real**: Utiliza YOLOv11 para detecção precisa de pessoas
- **Múltiplos Streams**: Suporte simultâneo para várias câmeras RTSP
- **API REST**: Interface completa para controle e monitoramento
- **Rastreamento de Centroides**: Evita duplicação de detecções da mesma pessoa
- **Salvamento Automático**: Frames com pessoas detectadas são salvos automaticamente
- **Logs Detalhados**: Sistema de logging completo para debugging
- **Interface Assíncrona**: Processamento não-bloqueante usando FastAPI

## 📦 Instalação

### Pré-requisitos

```bash
# Python 3.8 ou superior
python --version

# Instalar dependências
pip install fastapi uvicorn opencv-python ultralytics numpy logging pydantic
```

### Instalação Completa

```bash
# Clonar ou baixar os arquivos
# Instalar todas as dependências
pip install -r requirements.txt

# Ou instalar manualmente:
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install opencv-python==4.8.1.78
pip install ultralytics==8.0.200
pip install numpy==1.24.3
pip install pydantic==2.4.2
```

## 🛠️ Estrutura dos Arquivos

```
projeto/
├── api.py              # API FastAPI principal
├── exemplo_uso.py      # Exemplos de uso da API
├── README.md          # Este arquivo
├── requirements.txt   # Dependências Python
└── detections/        # Pasta para frames salvos (criada automaticamente)
    ├── camera_01/
    ├── camera_02/
    └── ...
```

## 🔧 Configuração

### 1. URLs RTSP

Configure suas URLs RTSP no exemplo de uso:

```python
streams = [
    {
        "url": "rtsp://usuario:senha@ip:porta/path",
        "stream_id": "camera_01",
        "output_dir": "./detections/camera_01"
    }
]
```

### 2. Parâmetros de Detecção

No arquivo `api.py`, você pode ajustar:

```python
# Confiança mínima para detecção
results = model(frame, conf=0.5, classes=[0])

# Distância máxima para rastreamento
tracker = CentroidTracker(max_distance=50)
```

## 🚀 Como Usar

### 1. Iniciar a API

```bash
# Método 1: Executar diretamente
python api.py

# Método 2: Usar uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

A API estará disponível em: `http://localhost:8000`

### 2. Usar os Exemplos

```bash
# Executar exemplos interativos
python exemplo_uso.py
```

### 3. Documentação Automática

Acesse a documentação interativa da API:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📡 Endpoints da API

### Principais Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Informações da API |
| `POST` | `/start-detection` | Iniciar detecção em streams |
| `GET` | `/status` | Status de todos os streams |
| `GET` | `/status/{stream_id}` | Status de um stream específico |
| `GET` | `/detections/{stream_id}` | Detecções de um stream |
| `POST` | `/stop/{stream_id}` | Parar um stream específico |
| `POST` | `/stop-all` | Parar todos os streams |
| `GET` | `/download/{stream_id}/{filename}` | Baixar frame salvo |
| `DELETE` | `/clear/{stream_id}` | Limpar detecções |

### Exemplo de Requisição

```bash
# Iniciar detecção
curl -X POST "http://localhost:8000/start-detection" \
     -H "Content-Type: application/json" \
     -d '[{
       "url": "rtsp://usuario:senha@ip:porta/path",
       "stream_id": "camera_01",
       "output_dir": "./detections/camera_01"
     }]'

# Verificar status
curl "http://localhost:8000/status"

# Obter detecções
curl "http://localhost:8000/detections/camera_01"
```

## 🔍 Exemplos de Uso

### Exemplo Básico (Python)

```python
import requests

# Configurar stream
streams = [{
    "url": "rtsp://usuario:senha@ip:porta/path",
    "stream_id": "camera_01"
}]

# Iniciar detecção
response = requests.post("http://localhost:8000/start-detection", json=streams)
print(response.json())

# Verificar status
status = requests.get("http://localhost:8000/status/camera_01")
print(status.json())
```

### Monitoramento Contínuo

```python
import time
import requests

while True:
    try:
        status = requests.get("http://localhost:8000/status/camera_01")
        data = status.json()
        print(f"Pessoas detectadas: {data['people_detected']}")
        time.sleep(10)
    except KeyboardInterrupt:
        break
```

## 📊 Formato das Detecções

```json
{
  "stream_id": "camera_01",
  "total_detections": 15,
  "detections": [
    {
      "person_id": 1,
      "stream_id": "camera_01",
      "timestamp": "2024-01-20T10:30:15.123456",
      "confidence": 0.87,
      "bbox": [100, 150, 200, 400],
      "saved_frame": "./detections/camera_01/person_camera_01_1_20240120_103015.jpg"
    }
  ]
}
```

## 🐛 Solução de Problemas

### Problemas Comuns

#### 1. Erro de Conexão RTSP
```
[Stream camera_01] Erro ao conectar: rtsp://...
```
**Soluções:**
- Verificar credenciais (usuário/senha)
- Testar URL RTSP em player como VLC
- Verificar firewall e conectividade de rede
- Confirmar se a câmera suporta RTSP

#### 2. Modelo YOLO não Carrega
```
Erro ao carregar modelo YOLO
```
**Soluções:**
```bash
# Baixar modelo manualmente
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
```

#### 3. Performance Baixa
**Soluções:**
- Usar modelo mais leve: `yolo11n.pt` ao invés de `yolo11x.pt`
- Reduzir resolução do stream
- Aumentar intervalo entre frames:
```python
time.sleep(0.5)  # Ao invés de 0.1
```

#### 4. Muitas Detecções Duplicadas
**Ajustar parâmetros do tracker:**
```python
tracker = CentroidTracker(max_distance=30)  # Reduzir distância
```

#### 5. API não Responde
```bash
# Verificar se está rodando
curl http://localhost:8000/
# Verificar logs
tail -f stream_log.txt
```

### Logs e Debug

#### Ativar Logs Detalhados
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Verificar Status dos Streams
```bash
# Via API
curl http://localhost:8000/status

# Via logs
tail -f stream_log.txt
```

## ⚙️ Configurações Avançadas

### Personalizar Detecção

```python
# No arquivo api.py, ajustar parâmetros:

# Confiança mínima (0.0 a 1.0)
results = model(frame, conf=0.3)  # Menos restritivo

# Classes a detectar (0 = pessoa)
results = model(frame, classes=[0])

# Tamanho de entrada do modelo
model = YOLO("yolo11n.pt", imgsz=640)
```

### Otimização de Performance

```python
# Processar a cada N frames
frame_count = 0
if frame_count % 3 == 0:  # Processar 1 a cada 3 frames
    results = model(frame)
frame_count += 1

# Redimensionar frame antes da detecção
frame_small = cv2.resize(frame, (640, 480))
results = model(frame_small)
```

### Configurar Timeout RTSP

```python
# Timeout mais longo para conexões instáveis
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout;120000000"
```

## 📁 Estrutura de Arquivos Salvos

```
detections/
├── camera_01/
│   ├── person_camera_01_1_20240120_103015.jpg
│   ├── person_camera_01_2_20240120_103045.jpg
│   └── ...
├── camera_02/
│   ├── person_camera_02_1_20240120_104012.jpg
│   └── ...
└── logs/
    └── stream_log.txt
```

### Formato dos Nomes de Arquivo

```
person_{stream_id}_{person_id}_{timestamp}.jpg
```

- `stream_id`: ID do stream (ex: camera_01)
- `person_id`: ID único da pessoa detectada
- `timestamp`: Data e hora (YYYYMMDD_HHMMSS)

## 🔐 Segurança

### Autenticação RTSP

```python
# Credenciais na URL
"rtsp://usuario:senha@192.168.1.100:554/stream"

# Caracteres especiais devem ser codificados
import urllib.parse
username = urllib.parse.quote("usuário@dominio")
password = urllib.parse.quote("senha#123")
url = f"rtsp://{username}:{password}@ip:porta/path"
```

### Segurança da API

Para produção, adicionar autenticação:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/start-detection")
async def start_detection(token: str = Depends(security)):
    # Validar token aqui
    pass
```

## 📈 Monitoramento e Métricas

### Métricas Disponíveis

```python
# Via API
GET /status  # Status geral
GET /status/{stream_id}  # Status específico

# Métricas incluem:
# - people_detected: Total de pessoas detectadas
# - last_detection: Timestamp da última detecção
# - status: Estado do stream (running, stopped, error)
```

### Integração com Sistemas de Monitoramento

```python
# Exemplo: Enviar métricas para sistema externo
import requests

def send_metrics(stream_id, people_count):
    metrics_data = {
        "stream": stream_id,
        "people": people_count,
        "timestamp": datetime.now().isoformat()
    }
    requests.post("http://monitoring-system/metrics", json=metrics_data)
```

## 🔄 Backup e Recuperação

### Backup de Detecções

```bash
# Backup diário automático
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf "backup_detections_$DATE.tar.gz" detections/
```

### Recuperação após Falha

```python
# A API reinicia automaticamente streams após falhas
# Para recuperação manual:
curl -X POST "http://localhost:8000/start-detection" -d '[...]'
```

## 📊 Performance e Otimização

### Benchmarks Típicos

| Hardware | Streams | FPS por Stream | CPU Usage |
|----------|---------|----------------|-----------|
| CPU i5 | 2 | 5-10 FPS | ~60% |
| CPU i7 | 4 | 10-15 FPS | ~70% |
| GPU RTX 3060 | 8 | 15-20 FPS | ~40% |

### Otimizações Recomendadas

1. **GPU**: Use CUDA se disponível
```python
model = YOLO("yolo11n.pt").cuda()
```

2. **Resolução**: Reduza para 640x480 se possível

3. **Intervalo**: Aumente tempo entre detecções
```python
time.sleep(0.2)  # 5 FPS ao invés de 10 FPS
```

## 🤝 Contribuição e Suporte

### Como Contribuir

1. Fork do repositório
2. Criar branch para feature: `git checkout -b feature/nova-funcionalidade`
3. Commit das mudanças: `git commit -m 'Adicionar nova funcionalidade'`
4. Push para branch: `git push origin feature/nova-funcionalidade`
5. Abrir Pull Request

### Reportar Bugs

Ao reportar bugs, inclua:
- Versão do Python
- Sistema operacional
- Logs de erro
- Configuração RTSP (sem credenciais)
- Passos para reproduzir

### Suporte

- **Issues**: Use o sistema de issues do repositório
- **Documentação**: Verifique `/docs` na API
- **Logs**: Sempre inclua logs relevantes

## 📜 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🙏 Agradecimentos

- **Ultralytics**: Pelo excelente framework YOLO
- **FastAPI**: Pela framework web moderna e rápida
- **OpenCV**: Pelas ferramentas de visão computacional
- **Comunidade Open Source**: Por todas as contribuições

## 📞 Contato

Para dúvidas técnicas ou sugestões:
- **GitHub Issues**: [Criar issue](https://github.com/dheiver2/Stream-Detection-API)
- **Email**: dheiver.santos@gmail.com

---

**Desenvolvido com ❤️ para a comunidade de visão computacional**
