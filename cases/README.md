# Casos de Uso do Sistema de Detecção

Este diretório contém exemplos de implementação para diferentes casos de uso do sistema de detecção.

## Estrutura de Diretórios

```
cases/
├── city_security/           # Segurança de Cidades
│   ├── traffic_monitoring/  # Monitoramento de Tráfego
│   ├── crowd_analysis/      # Análise de Multidões
│   └── suspicious_behavior/ # Detecção de Comportamentos Suspeitos
│
├── condominium/            # Segurança de Condomínios
│   ├── access_control/     # Controle de Acesso
│   ├── visitor_tracking/   # Rastreamento de Visitantes
│   └── perimeter_security/ # Segurança Perimetral
│
├── retail/                 # Bares e Restaurantes
│   ├── customer_tracking/  # Rastreamento de Clientes
│   ├── queue_analysis/     # Análise de Filas
│   └── occupancy_monitor/  # Monitoramento de Ocupação
│
├── industrial/            # Industrial
│   ├── productivity/      # Análise de Produtividade
│   ├── quality_control/   # Controle de Qualidade
│   └── equipment_monitor/ # Monitoramento de Equipamentos
│
├── traffic/              # Tráfego e Transporte
│   ├── vehicle_tracking/ # Rastreamento de Veículos
│   ├── license_plate/    # Reconhecimento de Placas
│   └── collision_prevention/ # Prevenção de Colisão
│
└── wildlife/            # Monitoramento de Animais
    ├── animal_detection/ # Detecção de Animais
    └── species_classification/ # Classificação de Espécies
```

## Casos de Uso Implementados

### 1. Segurança de Cidades
- Monitoramento de tráfego
- Análise de multidões
- Detecção de comportamentos suspeitos
- Monitoramento de áreas públicas

### 2. Segurança de Condomínios
- Controle de acesso
- Rastreamento de visitantes
- Segurança perimetral
- Detecção de intrusos

### 3. Bares e Restaurantes
- Rastreamento de clientes
- Contagem de pessoas
- Análise de tempo de espera
- Monitoramento de ocupação

### 4. Industrial
- Análise de produtividade
- Controle de qualidade
- Inspeção visual de equipamentos
- Monitoramento de processos

### 5. Tráfego e Transporte
- Classificação de veículos
- Reconhecimento de placas
- Detecção de pedestres
- Prevenção de colisão
- Monitoramento de atenção do motorista

### 6. Monitoramento de Animais
- Detecção de animais
- Classificação de espécies
- Monitoramento de comportamento animal

## Como Usar

Cada caso de uso contém:
1. Arquivo de configuração específico
2. Script de exemplo
3. Documentação de uso
4. Requisitos específicos

Para usar um caso de uso específico:
1. Navegue até o diretório do caso de uso
2. Leia o README.md específico
3. Configure as variáveis necessárias
4. Execute o script de exemplo

## Requisitos Comuns
- Python 3.8+
- OpenCV
- Ultralytics YOLO
- FastAPI
- Outras dependências específicas por caso de uso 