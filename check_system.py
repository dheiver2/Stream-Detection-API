"""
Script para verificar a configuração do sistema.
"""

import os
import sys
import torch
import cv2
from pathlib import Path
from config.settings import DATA_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR

def check_python_version():
    """Verifica versão do Python."""
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("ERRO: Python 3.8 ou superior é necessário")
        return False
    return True

def check_dependencies():
    """Verifica dependências principais."""
    try:
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        
        print(f"OpenCV version: {cv2.__version__}")
        return True
    except Exception as e:
        print(f"ERRO ao verificar dependências: {e}")
        return False

def check_directories():
    """Verifica diretórios necessários."""
    directories = {
        "Data": DATA_DIR,
        "Models": MODELS_DIR,
        "Logs": LOGS_DIR,
        "Cache": CACHE_DIR
    }
    
    all_ok = True
    for name, path in directories.items():
        if not path.exists():
            print(f"ERRO: Diretório {name} não existe: {path}")
            all_ok = False
        else:
            print(f"OK: Diretório {name} existe: {path}")
            
            # Verificar permissões
            if not os.access(path, os.W_OK):
                print(f"ERRO: Sem permissão de escrita em {path}")
                all_ok = False
            else:
                print(f"OK: Permissões de escrita em {path}")
    
    return all_ok

def check_model():
    """Verifica se o modelo YOLO está disponível."""
    model_path = MODELS_DIR / "yolov8n.pt"
    if not model_path.exists():
        print(f"ERRO: Modelo YOLO não encontrado em {model_path}")
        return False
    
    try:
        from ultralytics import YOLO
        model = YOLO(str(model_path))
        print("OK: Modelo YOLO carregado com sucesso")
        return True
    except Exception as e:
        print(f"ERRO ao carregar modelo: {e}")
        return False

def main():
    """Função principal de verificação."""
    print("=== Verificação do Sistema ===")
    
    checks = {
        "Python Version": check_python_version,
        "Dependencies": check_dependencies,
        "Directories": check_directories,
        "Model": check_model
    }
    
    all_passed = True
    for name, check_func in checks.items():
        print(f"\nVerificando {name}...")
        if not check_func():
            all_passed = False
            print(f"ERRO: Falha na verificação de {name}")
        else:
            print(f"OK: {name} verificado com sucesso")
    
    if all_passed:
        print("\nTodas as verificações passaram!")
        return 0
    else:
        print("\nAlgumas verificações falharam. Por favor, corrija os erros.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 