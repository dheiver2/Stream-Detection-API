# Stream Detection API

API robusta para detecção de objetos em streams de vídeo usando YOLO, com suporte a múltiplos casos de uso.

## Características

- Processamento de múltiplos streams RTSP simultaneamente
- Suporte a diferentes casos de uso (tráfego, segurança, bar)
- Detecção de objetos usando modelos YOLO
- Sistema de eventos e alertas com armazenamento em CSV
- Métricas e monitoramento em tempo real
- Cache e otimizações de performance
- Segurança e autenticação
- Logging estruturado
- Testes automatizados

## Requisitos

- Python 3.8+
- OpenCV
- PyTorch
- FastAPI
- Pandas
- Prometheus (opcional)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/stream-detection-api.git
cd stream-detection-api
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas configurações
```

## Configuração

O projeto usa variáveis de ambiente para configuração. Principais configurações:

- `API_HOST`: Host da API (default: 0.0.0.0)
- `API_PORT`: Porta da API (default: 8000)
- `SECRET_KEY`: Chave secreta para JWT
- `MODEL_DEVICE`: Dispositivo para inferência (cpu/cuda)
- `DATA_DIR`: Diretório para armazenamento de CSVs (default: ./data)

## Uso

1. Inicie o servidor:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

2. Acesse a documentação da API:
```
http://localhost:8000/docs
```

### Exemplos de Uso

#### Monitoramento de Tráfego

```python
import requests

# Criar stream de tráfego
stream_data = {
    "stream_id": "traffic_cam_1",
    "url": "rtsp://camera.com/traffic",
    "case_type": "traffic",
    "config": {
        "track_objects": True,
        "save_violations": True
    }
}

response = requests.post("http://localhost:8000/streams", json=stream_data)
```

#### Monitoramento de Segurança

```python
# Criar stream de segurança
stream_data = {
    "stream_id": "security_cam_1",
    "url": "rtsp://camera.com/security",
    "case_type": "security",
    "config": {
        "track_objects": True,
        "save_events": True
    }
}

response = requests.post("http://localhost:8000/streams", json=stream_data)
```

## Casos de Uso

### Monitoramento de Tráfego
- Detecção de veículos
- Monitoramento de velocidade
- Violações de trânsito
- Métricas de tráfego

### Segurança em Condomínios
- Detecção de pessoas
- Acesso não autorizado
- Atividades suspeitas
- Registro de eventos

### Monitoramento de Bares
- Contagem de pessoas
- Comportamentos suspeitos
- Aglomerações
- Alertas de segurança

## Estrutura do Projeto

```
stream-detection-api/
├── api.py                 # API principal
├── config/               # Configurações
│   ├── settings.py       # Configurações gerais
│   ├── logging_config.py # Configuração de logging
│   ├── security.py       # Configurações de segurança
│   └── cache.py          # Configurações de cache
├── cases/                # Casos de uso
│   ├── storage_manager.py # Gerenciador de armazenamento CSV
│   ├── event_manager.py  # Gerenciador de eventos
│   ├── city_security/    # Monitoramento de tráfego
│   ├── condominium/      # Segurança em condomínios
│   └── bar/             # Monitoramento de bares
├── models/               # Modelos YOLO
├── tests/               # Testes
├── logs/                # Logs
├── data/                # Dados (CSVs)
│   ├── events/         # Eventos
│   ├── alerts/         # Alertas
│   └── metrics/        # Métricas
└── requirements.txt     # Dependências
```

## Armazenamento de Dados

O sistema utiliza arquivos CSV para armazenamento de dados, organizados da seguinte forma:

### Eventos
- Armazenados em `data/events/{case_type}_{date}.csv`
- Campos: timestamp, stream_id, event_type, confidence, metadata
- Rotação diária de arquivos
- Limpeza automática após 30 dias

### Alertas
- Armazenados em `data/alerts/{case_type}_{date}.csv`
- Campos: timestamp, stream_id, alert_type, severity, message, metadata, resolved
- Rotação diária de arquivos
- Limpeza automática após 30 dias

### Métricas
- Armazenadas em `data/metrics/{case_type}_{date}.csv`
- Campos: timestamp + métricas específicas do caso
- Rotação diária de arquivos
- Limpeza automática após 30 dias

## API Endpoints

### Streams
- `POST /streams`: Criar novo stream
- `GET /streams`: Listar streams
- `GET /streams/{stream_id}`: Obter stream
- `DELETE /streams/{stream_id}`: Remover stream
- `GET /streams/{stream_id}/status`: Status do stream

### Detecção
- `POST /detect`: Processar frame
- `GET /detections`: Listar detecções
- `GET /detections/{stream_id}`: Detecções por stream

### Eventos
- `POST /events`: Criar evento
- `GET /events`: Listar eventos
- `GET /events/{stream_id}`: Eventos por stream

### Alertas
- `POST /alerts`: Criar alerta
- `GET /alerts`: Listar alertas
- `GET /alerts/active`: Alertas ativos
- `PUT /alerts/{alert_id}/resolve`: Resolver alerta

### Métricas
- `GET /metrics`: Métricas do sistema
- `GET /metrics/{stream_id}`: Métricas por stream
- `GET /cases/{case_type}/metrics`: Métricas por caso

## Monitoramento

### Métricas
- Uso de CPU/Memória
- Latência de detecção
- Contagem de eventos
- Status dos streams

### Logs
- Logs estruturados em JSON
- Rotação automática
- Níveis configuráveis
- Separação por caso de uso

### Alertas
- Alertas de sistema
- Alertas de performance
- Alertas de erro
- Notificações configuráveis

## Segurança

- Autenticação JWT
- Rate limiting
- CORS configurável
- SSL/TLS
- Validação de dados
- Sanitização de inputs

## Performance

- Cache em memória
- Processamento em lote
- Otimização de modelos
- Compressão de dados
- Gerenciamento de recursos

## Testes

```bash
# Executar todos os testes
pytest

# Executar testes específicos
pytest tests/test_api.py
pytest tests/test_detection.py

# Executar com cobertura
pytest --cov=.
```

## Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

Para suporte, abra uma issue no GitHub ou contate a equipe de desenvolvimento.
