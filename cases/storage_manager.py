"""
Gerenciador de armazenamento em CSV.
Este módulo implementa o armazenamento de eventos e alertas em arquivos CSV.
"""

import csv
import json
import fcntl
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from config.settings import DATA_DIR, STORAGE_CONFIG
from config.logging_config import CaseLogger

logger = CaseLogger("storage")

class FileLock:
    """Implementa lock de arquivo usando fcntl."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.lock_file = file_path.with_suffix('.lock')
        self.lock_fd = None
    
    def __enter__(self):
        # Criar arquivo de lock se não existir
        self.lock_fd = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
        except Exception as e:
            self.lock_fd.close()
            raise e
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            try:
                os.remove(self.lock_file)
            except:
                pass

class StorageManager:
    """Gerenciador de armazenamento em CSV."""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.events_dir = self.data_dir / "events"
        self.alerts_dir = self.data_dir / "alerts"
        self.metrics_dir = self.data_dir / "metrics"
        
        # Criar diretórios necessários
        for directory in [self.events_dir, self.alerts_dir, self.metrics_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Verificar permissões
        self._check_permissions()
    
    def _check_permissions(self):
        """Verifica permissões dos diretórios."""
        for directory in [self.events_dir, self.alerts_dir, self.metrics_dir]:
            if not os.access(directory, os.W_OK):
                raise PermissionError(f"Sem permissão de escrita em {directory}")
    
    def _get_csv_path(self, directory: Path, case_type: str, date: Optional[datetime] = None) -> Path:
        """Obtém caminho do arquivo CSV."""
        if date is None:
            date = datetime.now()
        return directory / f"{case_type}_{date.strftime('%Y%m%d')}.csv"
    
    def _ensure_csv_headers(self, file_path: Path, headers: List[str]) -> None:
        """Garante que o arquivo CSV existe com os headers corretos."""
        if not file_path.exists():
            with FileLock(file_path):
                with open(file_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
    
    def _check_disk_space(self, file_path: Path) -> bool:
        """Verifica se há espaço suficiente em disco."""
        try:
            stat = os.statvfs(file_path.parent)
            free_space = stat.f_frsize * stat.f_bavail
            return free_space > STORAGE_CONFIG["max_file_size_mb"] * 1024 * 1024
        except Exception as e:
            logger.log_error("disk_space_check_error", {"error": str(e)})
            return False
    
    def _validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Valida dados antes de salvar."""
        try:
            return all(field in data for field in required_fields)
        except Exception as e:
            logger.log_error("data_validation_error", {"error": str(e)})
            return False
    
    def save_event(self, case_type: str, event_data: Dict[str, Any]) -> bool:
        """Salva evento em CSV com lock e validação."""
        try:
            # Validar dados
            required_fields = ['stream_id', 'event_type', 'confidence']
            if not self._validate_data(event_data, required_fields):
                logger.log_error("invalid_event_data", {"data": event_data})
                return False
            
            # Preparar dados
            event_data['timestamp'] = datetime.now().isoformat()
            if 'metadata' in event_data:
                event_data['metadata'] = json.dumps(event_data['metadata'])
            
            # Definir headers
            headers = ['timestamp', 'stream_id', 'event_type', 'confidence', 'metadata']
            
            # Obter caminho do arquivo
            file_path = self._get_csv_path(self.events_dir, case_type)
            
            # Verificar espaço em disco
            if not self._check_disk_space(file_path):
                logger.log_error("insufficient_disk_space", {"file": str(file_path)})
                return False
            
            # Salvar com lock
            with FileLock(file_path):
                self._ensure_csv_headers(file_path, headers)
                with open(file_path, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writerow(event_data)
            
            logger.log_info("event_saved", {"case_type": case_type, "event_type": event_data['event_type']})
            return True
        
        except Exception as e:
            logger.log_error("event_save_error", {"error": str(e)})
            return False
    
    def save_alert(self, case_type: str, alert_data: Dict[str, Any]) -> bool:
        """Salva alerta em CSV com lock e validação."""
        try:
            # Validar dados
            required_fields = ['stream_id', 'alert_type', 'severity', 'message']
            if not self._validate_data(alert_data, required_fields):
                logger.log_error("invalid_alert_data", {"data": alert_data})
                return False
            
            # Preparar dados
            alert_data['timestamp'] = datetime.now().isoformat()
            alert_data['resolved'] = False
            if 'metadata' in alert_data:
                alert_data['metadata'] = json.dumps(alert_data['metadata'])
            
            # Definir headers
            headers = ['timestamp', 'stream_id', 'alert_type', 'severity', 'message', 'metadata', 'resolved']
            
            # Obter caminho do arquivo
            file_path = self._get_csv_path(self.alerts_dir, case_type)
            
            # Verificar espaço em disco
            if not self._check_disk_space(file_path):
                logger.log_error("insufficient_disk_space", {"file": str(file_path)})
                return False
            
            # Salvar com lock
            with FileLock(file_path):
                self._ensure_csv_headers(file_path, headers)
                with open(file_path, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writerow(alert_data)
            
            logger.log_info("alert_saved", {"case_type": case_type, "alert_type": alert_data['alert_type']})
            return True
        
        except Exception as e:
            logger.log_error("alert_save_error", {"error": str(e)})
            return False
    
    def get_recent_events(self, case_type: str, stream_id: Optional[str] = None, 
                         limit: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Obtém eventos recentes com paginação."""
        try:
            # Obter arquivo mais recente
            files = sorted(self.events_dir.glob(f"{case_type}_*.csv"), reverse=True)
            if not files:
                return []
            
            # Calcular offset para paginação
            offset = (page - 1) * limit
            
            # Ler CSV com lock
            with FileLock(files[0]):
                # Ler apenas as linhas necessárias
                df = pd.read_csv(files[0], skiprows=range(1, offset + 1), nrows=limit)
            
            # Filtrar por stream_id se especificado
            if stream_id:
                df = df[df['stream_id'] == stream_id]
            
            # Converter metadata de JSON
            if 'metadata' in df.columns:
                df['metadata'] = df['metadata'].apply(lambda x: json.loads(x) if pd.notna(x) else {})
            
            # Ordenar por timestamp
            df = df.sort_values('timestamp', ascending=False)
            
            return df.to_dict('records')
        
        except Exception as e:
            logger.log_error("event_retrieval_error", {"error": str(e)})
            return []
    
    def get_active_alerts(self, case_type: str, stream_id: Optional[str] = None,
                         page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém alertas ativos com paginação."""
        try:
            # Obter arquivo mais recente
            files = sorted(self.alerts_dir.glob(f"{case_type}_*.csv"), reverse=True)
            if not files:
                return []
            
            # Calcular offset para paginação
            offset = (page - 1) * limit
            
            # Ler CSV com lock
            with FileLock(files[0]):
                # Ler apenas as linhas necessárias
                df = pd.read_csv(files[0], skiprows=range(1, offset + 1), nrows=limit)
            
            # Filtrar por stream_id e alertas não resolvidos
            df = df[df['resolved'] == False]
            if stream_id:
                df = df[df['stream_id'] == stream_id]
            
            # Converter metadata de JSON
            if 'metadata' in df.columns:
                df['metadata'] = df['metadata'].apply(lambda x: json.loads(x) if pd.notna(x) else {})
            
            return df.to_dict('records')
        
        except Exception as e:
            logger.log_error("alert_retrieval_error", {"error": str(e)})
            return []
    
    def resolve_alert(self, case_type: str, alert_id: str) -> bool:
        """Resolve um alerta com lock."""
        try:
            # Obter arquivo mais recente
            files = sorted(self.alerts_dir.glob(f"{case_type}_*.csv"), reverse=True)
            if not files:
                return False
            
            # Atualizar com lock
            with FileLock(files[0]):
                # Ler CSV
                df = pd.read_csv(files[0])
                
                # Atualizar alerta
                mask = df['alert_id'] == alert_id
                if not mask.any():
                    return False
                
                df.loc[mask, 'resolved'] = True
                df.loc[mask, 'resolved_at'] = datetime.now().isoformat()
                
                # Salvar alterações
                df.to_csv(files[0], index=False)
            
            logger.log_info("alert_resolved", {"alert_id": alert_id})
            return True
        
        except Exception as e:
            logger.log_error("alert_resolve_error", {"error": str(e)})
            return False
    
    def save_metrics(self, case_type: str, metrics_data: Dict[str, Any]) -> bool:
        """Salva métricas em CSV com lock e validação."""
        try:
            # Validar dados
            if not metrics_data:
                logger.log_error("invalid_metrics_data", {"data": metrics_data})
                return False
            
            # Preparar dados
            metrics_data['timestamp'] = datetime.now().isoformat()
            
            # Definir headers
            headers = ['timestamp'] + list(metrics_data.keys())
            
            # Obter caminho do arquivo
            file_path = self._get_csv_path(self.metrics_dir, case_type)
            
            # Verificar espaço em disco
            if not self._check_disk_space(file_path):
                logger.log_error("insufficient_disk_space", {"file": str(file_path)})
                return False
            
            # Salvar com lock
            with FileLock(file_path):
                self._ensure_csv_headers(file_path, headers)
                with open(file_path, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writerow(metrics_data)
            
            return True
        
        except Exception as e:
            logger.log_error("metrics_save_error", {"error": str(e)})
            return False
    
    def cleanup_old_files(self, days: int = 30) -> None:
        """Remove arquivos CSV antigos com verificação de espaço."""
        try:
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            
            for directory in [self.events_dir, self.alerts_dir, self.metrics_dir]:
                for file_path in directory.glob("*.csv"):
                    try:
                        # Extrair data do nome do arquivo
                        date_str = file_path.stem.split('_')[-1]
                        file_date = datetime.strptime(date_str, '%Y%m%d')
                        
                        if file_date < cutoff_date:
                            # Verificar se arquivo está em uso
                            try:
                                with FileLock(file_path):
                                    file_path.unlink()
                                    logger.log_info("old_file_removed", {"file": str(file_path)})
                            except:
                                logger.log_warning("file_in_use", {"file": str(file_path)})
                    
                    except Exception as e:
                        logger.log_error("file_cleanup_error", {"file": str(file_path), "error": str(e)})
        
        except Exception as e:
            logger.log_error("cleanup_error", {"error": str(e)})

# Instância global do gerenciador de armazenamento
storage_manager = StorageManager() 